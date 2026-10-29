from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from users.models import User
from utilities.testing import APITestCase

from netbox_routing_protocols.helpers import route_policy as route_policy_helpers
from netbox_routing_protocols.models import (
    ASPath,
    Community,
    PrefixList,
    BGPPolicyTemplate,
    RoutePolicy,
    RoutePolicyEntry,
)


class SuperuserMixin:
    def login(self):
        user = User.objects.filter(username='su').first() or (
            User.objects.create_superuser('su', 'su@example.com', 'x')
        )
        self.client.force_login(user)


class RoutePolicyDeleteTestCase(SuperuserMixin, TestCase):
    """A route policy that a protocol uses cannot be deleted"""

    @classmethod
    def setUpTestData(cls):
        cls.used = RoutePolicy.objects.create(name='Used')
        cls.free = RoutePolicy.objects.create(name='Free')
        RoutePolicyEntry.objects.create(
            route_policy=cls.used, sequence=10, action='permit'
        )
        cls.template = BGPPolicyTemplate.objects.create(
            name='Template', routepolicy_in=cls.used
        )

    def test_the_single_delete_is_refused_and_names_the_user(self):
        self.login()
        url = self.used.get_absolute_url() + 'delete/'
        response = self.client.post(url, {'confirm': True}, follow=True)
        self.assertTrue(RoutePolicy.objects.filter(pk=self.used.pk).exists())
        self.assertTrue(
            RoutePolicyEntry.objects.filter(route_policy=self.used).exists()
        )
        self.assertContains(response, 'Template')

    def test_the_bulk_delete_is_refused(self):
        self.login()
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:routepolicy_bulk_delete'),
            {'pk': [self.used.pk, self.free.pk], 'confirm': True, '_confirm': True},
            follow=True,
        )
        self.assertTrue(RoutePolicy.objects.filter(pk=self.used.pk).exists())
        self.assertContains(response, 'Template')

    def test_a_free_policy_is_deleted_with_its_entries(self):
        RoutePolicyEntry.objects.create(
            route_policy=self.free, sequence=10, action='permit'
        )
        self.login()
        response = self.client.post(
            self.free.get_absolute_url() + 'delete/', {'confirm': True}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RoutePolicy.objects.filter(pk=self.free.pk).exists())
        self.assertFalse(
            RoutePolicyEntry.objects.filter(route_policy=self.free).exists()
        )

    def test_the_api_refuses_it(self):
        self.login()
        response = self.client.delete(
            reverse(
                'plugins-api:netbox_routing_protocols-api:routepolicy-detail',
                kwargs={'pk': self.used.pk},
            )
        )
        self.assertEqual(response.status_code, 409)
        self.assertTrue(RoutePolicy.objects.filter(pk=self.used.pk).exists())


def make_entry(route_policy, sequence, flow_control=None):
    return RoutePolicyEntry.objects.create(
        route_policy=route_policy,
        sequence=sequence,
        action='permit',
        flow_control=flow_control,
    )


class RoutePolicyResequenceTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.other = RoutePolicy.objects.create(name='Other')

    def pairs(self, policy=None):
        return list(
            (policy or self.policy)
            .route_policy_entries.order_by('sequence')
            .values_list('sequence', 'flow_control')
        )

    def test_the_continue_follows_the_entry_it_points_to(self):
        make_entry(self.policy, 3, flow_control=4)
        make_entry(self.policy, 4, flow_control=0)
        make_entry(self.policy, 7, flow_control=99)
        changed = route_policy_helpers.resequence(self.policy)
        self.assertEqual(changed, 3)
        # 0 is "next entry" and 99 points nowhere: both are kept
        self.assertEqual(self.pairs(), [(10, 20), (20, 0), (30, 99)])

    def test_another_policy_is_not_touched(self):
        make_entry(self.policy, 1)
        make_entry(self.other, 5, flow_control=5)
        route_policy_helpers.resequence(self.policy)
        self.assertEqual(self.pairs(self.other), [(5, 5)])

    def test_out_of_range_changes_nothing(self):
        make_entry(self.policy, 3, flow_control=4)
        make_entry(self.policy, 4)
        with self.assertRaises(ValidationError):
            route_policy_helpers.resequence(self.policy, start=4294967294, step=10)
        self.assertEqual(self.pairs(), [(3, 4), (4, None)])

    def test_the_view_renumbers_and_the_button_is_shown(self):
        make_entry(self.policy, 3)
        make_entry(self.policy, 4)
        self.login()
        response = self.client.get(self.policy.get_absolute_url())
        self.assertContains(response, 'resequence')
        url = self.policy.get_absolute_url() + 'resequence/'
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'start': 100, 'step': 50})
        self.assertEqual(response.status_code, 302)
        self.assertEqual([s for s, _f in self.pairs()], [100, 150])


class RoutePolicyResequenceAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.policy = RoutePolicy.objects.create(name='Policy')
        make_entry(self.policy, 3, flow_control=4)
        make_entry(self.policy, 4)
        self.url = reverse(
            'plugins-api:netbox_routing_protocols-api:routepolicy-resequence',
            kwargs={'pk': self.policy.pk},
        )
        self.permissions = (
            'netbox_routing_protocols.change_routepolicy',
            'netbox_routing_protocols.view_routepolicy',
        )

    def pairs(self):
        return list(
            self.policy.route_policy_entries.order_by('sequence').values_list(
                'sequence', 'flow_control'
            )
        )

    def test_resequence_with_defaults_and_values(self):
        self.add_permissions(
            *self.permissions, 'netbox_routing_protocols.change_routepolicyentry'
        )
        response = self.client.patch(self.url, {}, format='json', **self.header)
        self.assertHttpStatus(response, 200)
        self.assertEqual(response.data, {'changed': 2})
        self.assertEqual(self.pairs(), [(10, 20), (20, None)])
        self.client.patch(
            self.url, {'start': 100, 'step': 50}, format='json', **self.header
        )
        self.assertEqual(self.pairs(), [(100, 150), (150, None)])

    def test_invalid_values(self):
        self.add_permissions(
            *self.permissions, 'netbox_routing_protocols.change_routepolicyentry'
        )
        for data in ({'start': 'x'}, {'step': -1}, {'start': 4294967294, 'step': 10}):
            with self.subTest(data):
                response = self.client.patch(
                    self.url, data, format='json', **self.header
                )
                self.assertHttpStatus(response, 400)
        self.assertEqual(self.pairs(), [(3, 4), (4, None)])

    def test_it_needs_the_permission_to_change_entries(self):
        self.add_permissions(*self.permissions)
        response = self.client.patch(self.url, {}, format='json', **self.header)
        self.assertHttpStatus(response, 403)
        self.assertEqual(self.pairs(), [(3, 4), (4, None)])


class RoutePolicyEntryQueriesTestCase(SuperuserMixin, TestCase):
    """The queries of a list do not grow with the number of entries"""

    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.lists = [
            PrefixList.objects.create(name=f'List {i}', family=4) for i in range(3)
        ]
        cls.aspath = ASPath.objects.create(name='Path')

    def add_entries(self, first, count):
        for sequence in range(first, first + count):
            entry = make_entry(self.policy, sequence)
            entry.match_prefix_list.set(self.lists)
            entry.match_aspath.add(self.aspath)

    def count(self, call):
        with CaptureQueriesContext(connection) as queries:
            call()
        return len(queries)

    def check(self, call):
        self.add_entries(1, 2)
        # the first request fills caches (content types, permissions) that later ones reuse
        call()
        few = self.count(call)
        self.add_entries(10, 6)
        self.assertEqual(self.count(call), few)

    def test_the_api_list(self):
        user = User.objects.create_superuser('api', 'api@example.com', 'x')
        self.client.force_login(user)
        url = reverse('plugins-api:netbox_routing_protocols-api:routepolicyentry-list')
        self.check(lambda: self.client.get(url))

    def test_the_entries_tab(self):
        self.login()
        url = self.policy.get_absolute_url() + 'entries/'
        self.check(lambda: self.client.get(url))

    def test_the_graphql_list(self):
        self.login()
        query = '{route_policy_entry_list{id match_prefix_list{id} match_aspath{id}}}'
        self.check(
            lambda: self.client.post(
                '/graphql/', {'query': query}, content_type='application/json'
            )
        )


class RoutePolicyEntryPagesTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.aspath = ASPath.objects.create(name='Path')
        cls.entry = make_entry(cls.policy, 10)
        cls.entry.match_aspath.add(cls.aspath)

    def test_the_match_panel_shows_the_as_path(self):
        self.login()
        response = self.client.get(self.entry.get_absolute_url())
        self.assertContains(response, self.aspath.get_absolute_url())

    def test_the_form_saves_the_match_lists_and_validates_the_continue(self):
        self.login()
        community = Community.objects.create(community='65000:1')
        data = {
            'route_policy': self.policy.pk,
            'sequence': 20,
            'action': 'permit',
            'match_aspath': [self.aspath.pk],
            'match_community': [community.pk],
        }
        url = reverse('plugins:netbox_routing_protocols:routepolicyentry_add')
        response = self.client.post(url, {**data, 'flow_control': -1})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RoutePolicyEntry.objects.filter(sequence=20).exists())
        response = self.client.post(url, {**data, 'flow_control': 30})
        self.assertEqual(response.status_code, 302)
        entry = RoutePolicyEntry.objects.get(sequence=20)
        self.assertEqual(entry.flow_control, 30)
        self.assertEqual(list(entry.match_aspath.all()), [self.aspath])
        self.assertEqual(list(entry.match_community.all()), [community])


class RoutePolicyGraphQLTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.lists = [
            PrefixList.objects.create(name=f'List {i}', family=4) for i in range(2)
        ]
        cls.first = make_entry(cls.policy, 10)
        cls.first.match_prefix_list.set(cls.lists)
        cls.second = RoutePolicyEntry.objects.create(
            route_policy=cls.policy, sequence=20, action='deny', flow_control=30
        )

    def query(self, text):
        self.login()
        response = self.client.post(
            '/graphql/', {'query': text}, content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn('errors', data)
        return data['data']

    def test_the_match_lists_are_lists(self):
        data = self.query('{route_policy_entry_list{sequence match_prefix_list{id}}}')
        by_sequence = {
            int(row['sequence']): row['match_prefix_list']
            for row in data['route_policy_entry_list']
        }
        self.assertEqual(len(by_sequence[10]), 2)
        self.assertEqual(by_sequence[20], [])

    def test_a_policy_has_its_entries(self):
        data = self.query('{route_policy_list{route_policy_entries{sequence}}}')
        rows = data['route_policy_list'][0]['route_policy_entries']
        self.assertEqual(sorted(int(r['sequence']) for r in rows), [10, 20])

    def test_the_entries_can_be_filtered(self):
        for text, expected in (
            (
                '{route_policy_entry_list(filters:{action:{exact:"deny"}}){sequence}}',
                [20],
            ),
            (
                '{route_policy_entry_list(filters:{sequence:{comparison_lookup:{gte:15}}}){sequence}}',
                [20],
            ),
            (
                '{route_policy_entry_list(filters:{flow_control:{filter_lookup:{exact:30}}}){sequence}}',
                [20],
            ),
            (
                '{route_policy_entry_list(filters:{match_prefix_list:{name:{exact:"List 0"}}}){sequence}}',
                [10],
            ),
        ):
            with self.subTest(text):
                data = self.query(text)
                self.assertEqual(
                    [int(r['sequence']) for r in data['route_policy_entry_list']],
                    expected,
                )
