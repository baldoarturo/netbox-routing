from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from users.models import User

from netbox_routing_plugin.helpers import community as helpers
from netbox_routing_plugin.models.community import *
from netbox_routing_plugin.tests.objects.test_aspath_ui import SuperuserMixin

__all__ = ('CommunityMatchHelpersTestCase', 'CommunityMatchViewTestCase')


class CommunityMatchHelpersTestCase(TestCase):
    def test_parse_communities(self):
        self.assertEqual(
            helpers.parse_communities('65000:100, NO-EXPORT  65000:0100 rt:65000:1'),
            ['65000:100', '65535:65281', 'rt:65000:1'],
        )

    def test_parse_rejects_what_is_not_a_community(self):
        for text in ('', '  ', '65000:100 70000:1', 'nonsense'):
            with self.subTest(text=text), self.assertRaises(ValidationError):
                helpers.parse_communities(text)
        with self.assertRaises(ValidationError) as caught:
            helpers.parse_communities('65000:1 70000:1')
        self.assertIn('70000:1', caught.exception.messages[0])


class CommunityMatchViewTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a, cls.b, cls.c = (
            Community.objects.create(community=value)
            for value in ('65000:1', 'no-export', '65000:3')
        )
        cls.first = CommunityList.objects.create(name='First')
        cls.second = CommunityList.objects.create(name='Second')
        cls.other = CommunityList.objects.create(name='Unrelated')
        cls.entries = {}
        for lst, sequence, community, action in (
            (cls.first, 10, cls.a, 'deny'),
            (cls.first, 20, cls.b, 'permit'),
            (cls.first, 30, cls.c, 'permit'),
            (cls.second, 10, cls.b, 'permit'),
            (cls.other, 10, cls.c, 'permit'),
        ):
            cls.entries[(lst.name, sequence)] = CommunityListEntry.objects.create(
                community_list=lst,
                sequence=sequence,
                community=community,
                action=action,
            )
        cls.url = reverse('plugins:netbox_routing_plugin:community_match')

    def test_evaluate_first_match_wins(self):
        entries = CommunityListEntry.objects.select_related(
            'community_list', 'community'
        )
        results = dict(
            helpers.evaluate_communities(['65000:1', '65535:65281'], entries)
        )
        first = results[self.first]
        self.assertEqual(
            [(e.sequence, effective) for e, effective in first],
            [(10, True), (20, False)],
        )
        self.assertEqual(
            [(e.sequence, ef) for e, ef in results[self.second]], [(10, True)]
        )
        self.assertNotIn(self.other, results)

    def test_the_page(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, 'Community Match')
        response = self.client.get(self.url, {'q': '65000:1 no-export'})
        self.assertContains(response, 'First')
        self.assertContains(response, 'Second')
        self.assertContains(response, 'Deny (first match)')
        self.assertContains(response, 'also matches, not reached')
        self.assertContains(response, 'NO_EXPORT (RFC 1997)')
        self.assertNotContains(response, 'Unrelated')

    def test_lists_with_no_match_on_request(self):
        self.login()
        response = self.client.get(self.url, {'q': '65000:1', 'all': '1'})
        self.assertContains(response, 'Unrelated')
        self.assertContains(response, 'no entry matches')

    def test_nothing_matches(self):
        self.login()
        response = self.client.get(self.url, {'q': '65000:999'})
        self.assertContains(response, 'No community list entry matches')

    def test_an_invalid_community_is_reported(self):
        self.login()
        response = self.client.get(self.url, {'q': '70000:1'})
        self.assertContains(response, '70000:1')
        self.assertContains(response, 'alert-warning')

    def test_it_needs_the_view_permission(self):
        user = User.objects.create_user('plain', 'plain@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_the_menu_has_the_tool(self):
        from netbox_routing_plugin.navigation.community import COMMUNITY_MENU

        self.assertIn(
            'plugins:netbox_routing_plugin:community_match',
            [item.link for item in COMMUNITY_MENU],
        )
