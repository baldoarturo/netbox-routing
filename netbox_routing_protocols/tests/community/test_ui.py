from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from extras.models import Tag
from users.models import User

from netbox_routing_protocols.models import RoutePolicy, RoutePolicyEntry
from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.tests.objects.test_aspath_ui import SuperuserMixin

__all__ = (
    'CommunityListPageTestCase',
    'CommunityListDuplicateTestCase',
    'CommunityPageTestCase',
    'CommunityTablesTestCase',
)

NS = 'plugins:netbox_routing_protocols:'


def make_entry(community_list, sequence, community, action='permit', **kwargs):
    return CommunityListEntry.objects.create(
        community_list=community_list,
        sequence=sequence,
        community=community,
        action=action,
        **kwargs,
    )


def make_policy_entry(sequence=10):
    return RoutePolicyEntry.objects.create(
        route_policy=RoutePolicy.objects.create(name=f'Policy {sequence}'),
        sequence=sequence,
        action='permit',
    )


class CommunityListPageTestCase(SuperuserMixin, TestCase):
    def test_the_page_has_the_entries_panel_and_buttons(self):
        self.login()
        lst = CommunityList.objects.create(name='L')
        make_entry(lst, 10, Community.objects.create(community='65000:1'))
        response = self.client.get(lst.get_absolute_url())
        self.assertContains(
            response,
            f'{reverse(NS + "communitylistentry_add")}?community_list={lst.pk}',
        )
        self.assertContains(response, lst.get_absolute_url() + 'duplicate/')

    def test_the_add_form_suggests_the_next_sequence_and_permit(self):
        self.login()
        lst = CommunityList.objects.create(name='L')
        make_entry(lst, 10, Community.objects.create(community='65000:1'))
        response = self.client.get(
            f'{reverse(NS + "communitylistentry_add")}?community_list={lst.pk}'
        )
        self.assertContains(response, 'value="20"')
        self.assertEqual(response.context['form'].initial['action'], 'permit')

    def test_the_page_lists_the_route_policy_entries_that_match_it(self):
        self.login()
        lst = CommunityList.objects.create(name='L')
        make_policy_entry().match_community_list.add(lst)
        self.assertContains(
            self.client.get(lst.get_absolute_url()),
            f'match_community_list_id={lst.pk}',
        )

    def test_the_entries_tab_has_no_query_per_row(self):
        self.login()
        lst = CommunityList.objects.create(name='L')
        url = lst.get_absolute_url() + 'entries/'
        for sequence in (10, 20):
            make_entry(
                lst, sequence, Community.objects.create(community=f'1:{sequence}')
            )
        self.client.get(url)
        with CaptureQueriesContext(connection) as few:
            self.client.get(url)
        for sequence in range(30, 90, 10):
            make_entry(
                lst, sequence, Community.objects.create(community=f'1:{sequence}')
            )
        with CaptureQueriesContext(connection) as many:
            self.client.get(url)
        self.assertEqual(len(few), len(many))


class CommunityListDuplicateTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = CommunityList.objects.create(
            name='Source', type='extended', description='d', comments='c'
        )
        cls.source.tags.add(Tag.objects.create(name='t', slug='t'))
        cls.community = Community.objects.create(community='rt:65000:1')
        make_entry(cls.source, 10, cls.community, description='one')
        make_entry(cls.source, 20, cls.community, action='deny')
        cls.url = cls.source.get_absolute_url() + 'duplicate/'

    def test_the_form_suggests_a_name(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, 'Source copy')
        self.assertContains(response, '2 entries')

    def test_it_copies_the_list_with_its_entries(self):
        self.login()
        response = self.client.post(self.url, {'name': 'Copy', 'description': 'new'})
        copy = CommunityList.objects.get(name='Copy')
        self.assertRedirects(response, copy.get_absolute_url())
        self.assertEqual(
            (copy.type, copy.description, copy.comments), ('extended', 'new', 'c')
        )
        self.assertEqual(list(copy.tags.names()), ['t'])
        self.assertEqual(
            list(
                copy.communitylistentries.values_list(
                    'sequence', 'action', 'community', 'description'
                )
            ),
            [
                (10, 'permit', self.community.pk, 'one'),
                (20, 'deny', self.community.pk, ''),
            ],
        )
        self.assertEqual(self.source.communitylistentries.count(), 2)

    def test_a_taken_name_is_rejected_and_nothing_is_created(self):
        self.login()
        response = self.client.post(self.url, {'name': 'source'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CommunityList.objects.count(), 1)

    def test_it_needs_the_add_permission(self):
        user = User.objects.create_user('plain', 'plain@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class CommunityPageTestCase(SuperuserMixin, TestCase):
    def test_the_page_says_where_the_community_is_used(self):
        self.login()
        community = Community.objects.create(community='65000:1')
        lst = CommunityList.objects.create(name='L')
        make_entry(lst, 10, community)
        response = self.client.get(community.get_absolute_url())
        self.assertContains(response, f'community_id={community.pk}')

    def test_the_lists_can_be_filtered_by_community(self):
        from netbox_routing_protocols.filtersets.community import CommunityListFilterSet

        community = Community.objects.create(community='65000:1')
        used = CommunityList.objects.create(name='Used')
        CommunityList.objects.create(name='Free')
        make_entry(used, 10, community)
        make_entry(used, 20, community, action='deny')
        qs = CommunityListFilterSet(
            {'community_id': [community.pk]}, CommunityList.objects.all()
        ).qs
        self.assertEqual(list(qs), [used])


class CommunityTablesTestCase(SuperuserMixin, TestCase):
    def test_the_tables_count_entries_and_route_policy_entries(self):
        self.login()
        community = Community.objects.create(community='65000:1')
        lst = CommunityList.objects.create(name='L')
        make_entry(lst, 10, community)
        make_entry(lst, 20, community, action='deny')
        entry = make_policy_entry()
        entry.match_community_list.add(lst)

        response = self.client.get(reverse(NS + 'community_list'))
        row = next(r for r in response.context['table'].data if r.pk == community.pk)
        self.assertEqual(row.entry_count, 2)
        response = self.client.get(reverse(NS + 'communitylist_list'))
        row = next(r for r in response.context['table'].data if r.pk == lst.pk)
        self.assertEqual((row.entry_count, row.route_policy_entry_count), (2, 1))

    def test_the_list_tables_have_no_query_per_row(self):
        self.login()
        url = reverse(NS + 'community_list')
        Community.objects.create(community='65000:1')
        self.client.get(url)
        with CaptureQueriesContext(connection) as few:
            self.client.get(url)
        for number in range(2, 8):
            Community.objects.create(community=f'65000:{number}')
        with CaptureQueriesContext(connection) as many:
            self.client.get(url)
        self.assertEqual(len(few), len(many))
