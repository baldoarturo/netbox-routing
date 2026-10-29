from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from users.models import User

from netbox_routing_protocols.helpers.aspath import (
    parse_as_path,
    posix_to_python,
    validate_pattern,
)
from netbox_routing_protocols.models.objects import *

import re


def make_entry(aspath, sequence, pattern, action='permit'):
    return ASPathEntry.objects.create(
        aspath=aspath, sequence=sequence, action=action, pattern=pattern
    )


class ParseASPathTestCase(SimpleTestCase):
    def test_numbers_are_normalized(self):
        self.assertEqual(parse_as_path('  65001   65002 '), '65001 65002')
        self.assertEqual(parse_as_path('1.10 4294967295 0'), '1.10 4294967295 0')

    def test_invalid_paths(self):
        for text in (
            '',
            '   ',
            '65001 abc',
            '65001,65002',
            '4294967296',
            '70000.1',
            '²',
        ):
            with self.subTest(text), self.assertRaises(ValidationError):
                parse_as_path(text)


class PosixToPythonTestCase(SimpleTestCase):
    """The translation keeps the meaning of what validate_pattern accepts"""

    def matches(self, pattern, text):
        self.assertEqual(validate_pattern(pattern), [], pattern)
        return re.search(posix_to_python(pattern), text) is not None

    def test_matches_like_posix(self):
        for pattern, text, expected in (
            ('^65001 ', '65001 65002', True),
            ('^65001 ', '165001 65002', False),
            ('[[:digit:]]+$', '65001 65002', True),
            ('^[[:alpha:]]', '65001', False),
            ('^[0-9]+ [0-9]+$', '65001 65002', True),
            ('^65001( 65002)*$', '65001 65002 65002', True),
            ('(65002|65003)$', '65001 65003', True),
            ('^$', '65001', False),
            ('^6500[12]$', '65002', True),
            ('^6500[^12]$', '65002', False),
            ('65001{2}', '650011', True),
            ('^65001\\.', '65001.5', True),
            # a backslash and a closing bracket are ordinary inside brackets
            ('[\\d]', '65001', False),
            ('[\\d]', 'a\\d', True),
            ('[]a]', 'x]', True),
            ('[^]a]', 'a]', False),
            ('[a-]', '-', True),
        ):
            with self.subTest((pattern, text)):
                self.assertEqual(self.matches(pattern, text), expected)


class ASPathMatchViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customers = ASPath.objects.create(name='Customers')
        cls.transit = ASPath.objects.create(name='Transit')
        cls.unused = ASPath.objects.create(name='Unused')
        make_entry(cls.customers, 10, '^65001 65002$', 'deny')
        make_entry(cls.customers, 20, '^65001 ')
        make_entry(cls.customers, 30, '^65003 ')
        make_entry(cls.transit, 5, '_')
        make_entry(cls.unused, 5, '^1$')
        cls.url = reverse('plugins:netbox_routing_protocols:aspath_match')
        cls.user = User.objects.create_superuser('root', 'root@example.com', 'x')

    def setUp(self):
        self.client.force_login(self.user)

    def test_the_page_has_a_realtime_search_box(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'AS Path Match')
        self.assertContains(response, 'hx-get')
        self.assertContains(response, 'delay:250ms')

    def test_it_tells_the_sequence_of_each_matching_entry(self):
        response = self.client.get(self.url, {'q': '65001 65002'})
        self.assertContains(response, 'Customers')
        self.assertContains(response, '10 deny ^65001 65002$')
        self.assertContains(response, '20 permit ^65001 ')
        self.assertContains(response, 'first match')
        self.assertContains(response, 'also matches, not reached')
        self.assertNotContains(response, '30 permit')
        self.assertNotContains(response, 'Unused')

    def test_the_first_entry_of_each_aspath_is_the_effective_one(self):
        results = self.client.get(self.url, {'q': '65001 65002'}).context['results']
        customers = next(r for r in results if r['aspath'] == self.customers)
        self.assertEqual(
            [(row['entry'].sequence, row['effective']) for row in customers['rows']],
            [(10, True), (20, False)],
        )

    def test_the_aspaths_with_no_match_are_listed_on_request(self):
        response = self.client.get(self.url, {'q': '99', 'all': '1'})
        for name in ('Customers', 'Transit', 'Unused'):
            self.assertContains(response, name)
        self.assertContains(response, 'no entry matches')
        self.assertNotContains(response, 'implicit')
        response = self.client.get(self.url, {'q': '99'})
        self.assertContains(response, 'No AS path entry matches this path.')

    def test_an_invalid_path_is_a_message(self):
        response = self.client.get(self.url, {'q': '65001 abc'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is not an AS number')

    def test_htmx_gets_only_the_results(self):
        response = self.client.get(
            self.url, {'q': '65001 65002'}, HTTP_HX_REQUEST='true'
        )
        self.assertContains(response, 'Customers')
        self.assertNotContains(response, 'hx-trigger')

    def test_it_needs_the_view_permission(self):
        self.client.force_login(User.objects.create_user('plain', 'p@e.com', 'x'))
        self.assertEqual(self.client.get(self.url, {'q': '1'}).status_code, 403)

    def test_a_pattern_the_engine_cannot_read_is_skipped(self):
        # saved before the validation existed: it must not break the page
        ASPathEntry.objects.bulk_create(
            [ASPathEntry(aspath=self.unused, sequence=9, action='permit', pattern='(')]
        )
        response = self.client.get(self.url, {'q': '99'})
        self.assertEqual(response.status_code, 200)
