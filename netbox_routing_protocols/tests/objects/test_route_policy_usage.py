from django.test import TestCase
from django.urls import reverse

from users.models import User
from utilities.testing import create_test_device

from netbox_routing_protocols.filtersets import (
    RoutePolicyEntryFilterSet,
    RoutePolicyFilterSet,
)
from netbox_routing_protocols.tests.bgp.base import create_peer_address_family
from netbox_routing_protocols.models import (
    EIGRPRouter,
    ISISInstance,
    OSPFInstance,
    PrefixList,
    RoutePolicy,
    RoutePolicyEntry,
)


class RoutePolicyUsedByTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.other = RoutePolicy.objects.create(name='Other')
        cls.device = create_test_device(name='Device 1')
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')

    def related(self):
        self.client.force_login(self.user)
        return self.client.get(self.policy.get_absolute_url()).content.decode()

    def test_a_policy_nobody_uses(self):
        self.assertNotIn('import_policy_id', self.related())

    def test_the_protocols_the_bgp_objects_and_the_jumps(self):
        OSPFInstance.objects.create(
            name='OSPF',
            device=self.device,
            router_id='1.1.1.1',
            import_policy=self.policy,
        )
        ISISInstance.objects.create(device=self.device, export_policy=self.policy)
        EIGRPRouter.objects.create(
            device=self.device,
            mode='classic',
            pid=1,
            rid='1.1.1.1',
            import_policy=self.policy,
        )
        create_peer_address_family(routepolicy_in=self.policy)
        RoutePolicyEntry.objects.create(
            route_policy=self.other,
            sequence=10,
            action='permit',
            jump_policy=self.policy,
        )
        html = self.related()
        for param in (
            f'import_policy_id={self.policy.pk}',
            f'export_policy_id={self.policy.pk}',
            f'routepolicy_in_id={self.policy.pk}',
            f'jump_policy_id={self.policy.pk}',
        ):
            with self.subTest(param):
                self.assertIn(param, html)


class RoutePolicySearchTestCase(TestCase):
    def test_the_search_does_not_sort_for_nothing(self):
        for filterset, queryset in (
            (RoutePolicyFilterSet, RoutePolicy.objects.all()),
            (RoutePolicyEntryFilterSet, RoutePolicyEntry.objects.all()),
        ):
            with self.subTest(filterset.__name__):
                query = str(filterset({'q': 'x'}, queryset).qs.query)
                self.assertNotIn('DISTINCT', query)

    def test_it_still_finds(self):
        policy = RoutePolicy.objects.create(name='Edge', description='Peers')
        RoutePolicy.objects.create(name='Core')
        found = RoutePolicyFilterSet({'q': 'peers'}, RoutePolicy.objects.all()).qs
        self.assertEqual(list(found), [policy])
        entry = RoutePolicyEntry.objects.create(
            route_policy=policy, sequence=10, action='permit'
        )
        found = RoutePolicyEntryFilterSet(
            {'q': 'edge'}, RoutePolicyEntry.objects.filter(implicit=False)
        ).qs
        self.assertEqual(list(found), [entry])


class NoConditionsWarningTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.prefixes = PrefixList.objects.create(name='Prefixes', family=4)
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')

    def post(self, **data):
        self.client.force_login(self.user)
        return self.client.post(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_add'),
            {'route_policy': self.policy.pk, 'action': 'permit', **data},
            follow=True,
        )

    def texts(self, response):
        return [str(m) for m in response.context['messages']]

    def test_an_entry_without_conditions_is_saved_and_warned(self):
        response = self.post(sequence=10)
        self.assertTrue(RoutePolicyEntry.objects.filter(sequence=10).exists())
        self.assertTrue(any('matches every route' in t for t in self.texts(response)))

    def test_an_entry_with_conditions_is_not_warned(self):
        response = self.post(sequence=10, match_metric=5)
        self.assertFalse(any('matches every route' in t for t in self.texts(response)))

    def test_a_list_is_a_condition(self):
        response = self.post(sequence=10, match_prefix_list=[self.prefixes.pk])
        self.assertFalse(any('matches every route' in t for t in self.texts(response)))

    def test_the_page_and_the_table_say_it(self):
        entry = RoutePolicyEntry.objects.create(
            route_policy=self.policy, sequence=10, action='permit'
        )
        self.client.force_login(self.user)
        self.assertContains(
            self.client.get(entry.get_absolute_url()), 'Matches every route'
        )


class DeleteWarningTestCase(TestCase):
    def test_the_dialog_says_what_happens_to_the_entries(self):
        policy = RoutePolicy.objects.create(name='Policy')
        used = PrefixList.objects.create(name='Used', family=4)
        entry = RoutePolicyEntry.objects.create(
            route_policy=policy, sequence=10, action='deny'
        )
        entry.match_prefix_list.add(used)
        self.client.force_login(
            User.objects.create_superuser('su', 'su@example.com', 'x')
        )
        response = self.client.get(used.get_absolute_url() + 'delete/')
        self.assertContains(response, 'will match every route')
