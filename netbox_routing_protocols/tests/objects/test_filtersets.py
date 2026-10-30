from django.test import TestCase

from ipam.models import Prefix
from netbox_routing_protocols.choices import ActionChoices

from netbox_routing_protocols.filtersets.objects import *
from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RoutePolicyTestCase',
    'RoutePolicyEntryTestCase',
)


class ASPathTestCase(TestCase):
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.aspath = [
            ASPath(
                name='AS Path List 1-1',
            ),
            ASPath(
                name='AS Path List 1-2',
            ),
            ASPath(
                name='AS Path List 2-1',
            ),
            ASPath(
                name='AS Path List 2-2',
            ),
        ]
        ASPath.objects.bulk_create(cls.aspath)

    def test_q(self):
        params = {'q': 'AS Path List 1-'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ASPathEntryTestCase(TestCase):
    queryset = ASPathEntry.objects.all()
    filterset = ASPathEntryFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.aspath = (
            ASPath(
                name='AS Path List 1',
            ),
            ASPath(
                name='AS Path List 2',
            ),
        )
        ASPath.objects.bulk_create(cls.aspath)

        cls.aspath_entry = [
            ASPathEntry(
                aspath=cls.aspath[0],
                action=ActionChoices.PERMIT,
                sequence=1,
                pattern='^1234$',
            ),
            ASPathEntry(
                aspath=cls.aspath[0],
                action=ActionChoices.PERMIT,
                sequence=2,
                pattern='^5678$',
            ),
            ASPathEntry(
                aspath=cls.aspath[1],
                action=ActionChoices.PERMIT,
                sequence=1,
                pattern='^1234$',
            ),
            ASPathEntry(
                aspath=cls.aspath[1],
                action=ActionChoices.PERMIT,
                sequence=2,
                pattern='^5678',
            ),
        ]
        ASPathEntry.objects.bulk_create(cls.aspath_entry)

    def test_q(self):
        params = {'q': '1234'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_aspath(self):
        params = {
            'aspath_id': [
                self.aspath[1].pk,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {
            'aspath': [
                self.aspath[1].name,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class PrefixListTestCase(TestCase):
    queryset = PrefixList.objects.all()
    filterset = PrefixListFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = [
            PrefixList(
                name='Prefix List 1-1',
            ),
            PrefixList(
                name='Prefix List 1-2',
            ),
            PrefixList(
                name='Prefix List 2-1',
            ),
            PrefixList(
                name='Prefix List 2-2',
            ),
        ]
        PrefixList.objects.bulk_create(cls.prefix_list)

    def test_q(self):
        params = {'q': 'Prefix List 1-'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_q_description(self):
        PrefixList.objects.filter(name='Prefix List 2-1').update(
            description='customers upstream'
        )
        params = {'q': 'upstream'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name_and_family(self):
        params = {'name': ['Prefix List 1-1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
        params = {'family': 4}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)
        params = {'family': 6}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 0)


class PrefixListEntryTestCase(TestCase):
    queryset = PrefixListEntry.objects.all()
    filterset = PrefixListEntryFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = (
            PrefixList(
                name='Prefix List 1',
            ),
            PrefixList(
                name='Prefix List 2',
            ),
        )
        PrefixList.objects.bulk_create(cls.prefix_list)

        cls.prefixes = (Prefix(prefix='10.0.0.0/24'), Prefix(prefix='10.0.1.0/24'))
        Prefix.objects.bulk_create(cls.prefixes)

        cls.prefix_list_entry = [
            PrefixListEntry(
                prefix_list=cls.prefix_list[0],
                action=ActionChoices.PERMIT,
                sequence=1,
                prefix=cls.prefixes[0],
            ),
            PrefixListEntry(
                prefix_list=cls.prefix_list[0],
                action=ActionChoices.PERMIT,
                sequence=2,
                prefix=cls.prefixes[1],
            ),
            PrefixListEntry(
                prefix_list=cls.prefix_list[1],
                action=ActionChoices.PERMIT,
                sequence=1,
                prefix=cls.prefixes[0],
            ),
            PrefixListEntry(
                prefix_list=cls.prefix_list[1],
                action=ActionChoices.PERMIT,
                sequence=2,
                prefix=cls.prefixes[1],
            ),
        ]
        PrefixListEntry.objects.bulk_create(cls.prefix_list_entry)

    def test_q(self):
        params = {'q': 'Prefix List 1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_q_description(self):
        PrefixListEntry.objects.filter(pk=self.prefix_list_entry[0].pk).update(
            description='default route filter'
        )
        params = {'q': 'default route'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_prefix_list(self):
        params = {
            'prefix_list_id': [
                self.prefix_list[1].pk,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {
            'prefix_list': [
                self.prefix_list[1].name,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_prefix(self):
        params = {
            'prefix_id': [
                self.prefixes[0].pk,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {
            'prefix': [
                self.prefixes[0].prefix,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_any_prefix(self):
        PrefixListEntry.objects.create(
            prefix_list=self.prefix_list[0],
            action=ActionChoices.PERMIT,
            sequence=10,
            any_prefix=True,
            le=32,
        )
        self.assertEqual(
            self.filterset({'any_prefix': True}, self.queryset).qs.count(), 1
        )
        self.assertEqual(
            self.filterset({'any_prefix': False}, self.queryset).qs.count(), 4
        )

    def test_second_prefix(self):
        params = {'prefix_id': [self.prefixes[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'prefix_id': [self.prefixes[0].pk, self.prefixes[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_family(self):
        v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)
        prefix = Prefix.objects.create(prefix='2001:db8::/32')
        PrefixListEntry.objects.create(
            prefix_list=v6_list, action='permit', sequence=1, prefix=prefix
        )
        self.assertEqual(
            self.filterset({'family': 6}, self.queryset).qs.count(),
            1,
        )
        self.assertEqual(
            self.filterset({'family': 4}, self.queryset).qs.count(),
            self.queryset.exclude(prefix_list=v6_list).count(),
        )


class RoutePolicyTestCase(TestCase):
    queryset = RoutePolicy.objects.all()
    filterset = RoutePolicyFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = [
            RoutePolicy(
                name='Route Policy 1-1',
            ),
            RoutePolicy(
                name='Route Policy 1-2',
            ),
            RoutePolicy(
                name='Route Policy 2-1',
            ),
            RoutePolicy(
                name='Route Policy 2-2',
            ),
        ]
        RoutePolicy.objects.bulk_create(cls.prefix_list)

    def test_q(self):
        params = {'q': 'Route Policy 1-'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class RoutePolicyEntryTestCase(TestCase):
    queryset = RoutePolicyEntry.objects.all()
    filterset = RoutePolicyEntryFilterSet

    @classmethod
    def setUpTestData(cls):
        cls.route_policy = (
            RoutePolicy(
                name='Route Policy 1',
            ),
            RoutePolicy(
                name='Route Policy 2',
            ),
        )
        RoutePolicy.objects.bulk_create(cls.route_policy)

        cls.route_policy_entry = [
            RoutePolicyEntry(
                route_policy=cls.route_policy[0],
                action=ActionChoices.PERMIT,
                sequence=1,
                match_tag=1234,
            ),
            RoutePolicyEntry(
                route_policy=cls.route_policy[0],
                action=ActionChoices.PERMIT,
                sequence=2,
                match_tag=5678,
            ),
            RoutePolicyEntry(
                route_policy=cls.route_policy[1],
                action=ActionChoices.PERMIT,
                sequence=1,
                match_tag=9012,
            ),
            RoutePolicyEntry(
                route_policy=cls.route_policy[1],
                action=ActionChoices.PERMIT,
                sequence=2,
                match_tag=3456,
            ),
        ]
        RoutePolicyEntry.objects.bulk_create(cls.route_policy_entry)

    def test_q(self):
        params = {'q': 'Route Policy 1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_match_tag(self):
        params = {'match_tag': [1234, 5678]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_prefix_list(self):
        params = {
            'route_policy_id': [
                self.route_policy[1].pk,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {
            'route_policy': [
                self.route_policy[1].name,
            ]
        }
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
