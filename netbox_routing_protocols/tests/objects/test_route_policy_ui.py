from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from utilities.testing import APITestCase

from netbox_routing_protocols.helpers import route_policy as route_policy_helpers
from netbox_routing_protocols.models import (
    BGPPolicyTemplate,
    RoutePolicy,
    RoutePolicyEntry,
)


class SuperuserMixin:
    def login(self):
        user = User.objects.create_superuser('su', 'su@example.com', 'x')
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
