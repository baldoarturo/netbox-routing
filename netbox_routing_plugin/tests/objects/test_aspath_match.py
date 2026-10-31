from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from users.models import User

from unittest import mock

from netbox_routing_plugin.helpers import aspath as aspath_helpers
from netbox_routing_plugin.helpers.aspath import parse_as_path
from netbox_routing_plugin.models.objects import *


def make_entry(aspath, sequence, pattern, action='permit'):
    return ASPathEntry.objects.create(
        aspath=aspath, sequence=sequence, action=action, pattern=pattern
    )


class ParseASPathTestCase(SimpleTestCase):
    def test_numbers_are_normalized(self):
        self.assertEqual(parse_as_path('  65001   65002 '), '65001 65002')
        self.assertEqual(parse_as_path('1.10 4294967295 0'), '1.10 4294967295 0')

    def test_the_as_prefix_is_dropped(self):
        self.assertEqual(parse_as_path('AS65001 as65002 65003'), '65001 65002 65003')
        self.assertEqual(parse_as_path('AS1.10'), '1.10')

    def test_invalid_paths(self):
        for text in (
            '',
            '   ',
            '65001 abc',
            '65001,65002',
            '4294967296',
            '70000.1',
            '²',
            'AS',
            'ASN65001',
            'AS AS65001',
            'AS4294967296',
        ):
            with self.subTest(text), self.assertRaises(ValidationError):
                parse_as_path(text)


class ASPathMatchViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customers = ASPath.objects.create(name='Customers')
        cls.transit = ASPath.objects.create(name='Transit')
        cls.unused = ASPath.objects.create(name='Unused')
        make_entry(cls.customers, 10, '^65001 65002$', 'deny')
        make_entry(cls.customers, 20, '^65001 \\d+$')
        make_entry(cls.customers, 30, '^65003 ')
        make_entry(cls.transit, 5, '_')
        make_entry(cls.unused, 5, '^1$')
        cls.url = reverse('plugins:netbox_routing_plugin:aspath_match')
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
        self.assertContains(response, '20 permit ^65001 \\d+$')
        self.assertContains(response, 'first match')
        self.assertContains(response, 'also matches, not reached')
        self.assertNotContains(response, '30 permit')
        self.assertNotContains(response, 'Unused')

    def test_a_path_with_the_as_prefix_is_shown_normalized(self):
        response = self.client.get(self.url, {'q': 'AS65001 as65002'})
        self.assertContains(response, 'AS paths matching 65001 65002')
        self.assertContains(response, '10 deny ^65001 65002$')

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


class CatastrophicPatternTestCase(TestCase):
    """A pattern that backtracks without end is cut, it does not hang the page"""

    SLOW = r'(?:\d+ ?)+(?:\d+ ?)+(?:\d+ ?)+(?<=x)'
    PATH = ' '.join(['65001'] * 300)

    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Slow')
        cls.slow = make_entry(cls.aspath, 10, cls.SLOW)
        cls.fine = make_entry(cls.aspath, 20, '^65001 ')
        cls.user = User.objects.create_superuser('root', 'root@example.com', 'x')

    def test_the_slow_entry_is_reported_and_the_others_still_match(self):
        with mock.patch.object(aspath_helpers, 'MATCH_TIMEOUT', 0.05):
            results, timed_out, _left = aspath_helpers.evaluate_path(
                self.PATH, ASPathEntry.objects.select_related('aspath')
            )
        self.assertEqual(timed_out, [self.slow])
        self.assertEqual([entry for entry, effective in results[0][1]], [self.fine])

    def test_the_page_says_which_entries_were_skipped(self):
        self.client.force_login(self.user)
        with mock.patch.object(aspath_helpers, 'MATCH_TIMEOUT', 0.05):
            response = self.client.get(
                reverse('plugins:netbox_routing_plugin:aspath_match'),
                {'q': self.PATH},
            )
        self.assertContains(response, 'took too long to evaluate')
        self.assertContains(response, 'Slow 10')
        self.assertContains(response, '20 permit ^65001 ')

    def test_a_normal_pattern_is_not_reported(self):
        _results, timed_out, not_evaluated = aspath_helpers.evaluate_path(
            '65001 65002', ASPathEntry.objects.select_related('aspath')
        )
        self.assertEqual((timed_out, not_evaluated), ([], 0))

    def test_the_whole_search_has_a_time_limit(self):
        for sequence in range(30, 70, 10):
            make_entry(self.aspath, sequence, f'{self.SLOW}{sequence}')
        with (
            mock.patch.object(aspath_helpers, 'MATCH_TIMEOUT', 0.05),
            mock.patch.object(aspath_helpers, 'MATCH_BUDGET', 0.08),
        ):
            _results, _timed_out, not_evaluated = aspath_helpers.evaluate_path(
                self.PATH, ASPathEntry.objects.select_related('aspath')
            )
        # the budget runs out before the last entries: they are counted, not evaluated
        self.assertGreater(not_evaluated, 0)
        self.assertLessEqual(not_evaluated, ASPathEntry.objects.count())

    def test_the_page_says_the_search_was_cut(self):
        self.client.force_login(self.user)
        for sequence in range(30, 70, 10):
            make_entry(self.aspath, sequence, f'{self.SLOW}{sequence}')
        with (
            mock.patch.object(aspath_helpers, 'MATCH_TIMEOUT', 0.05),
            mock.patch.object(aspath_helpers, 'MATCH_BUDGET', 0.08),
        ):
            response = self.client.get(
                reverse('plugins:netbox_routing_plugin:aspath_match'),
                {'q': self.PATH},
            )
        self.assertContains(response, 'The time limit of the search was reached')
        self.assertContains(response, 'may be incomplete')
