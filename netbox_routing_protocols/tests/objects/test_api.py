from django.urls import reverse

from ipam.models import Prefix
from utilities.testing import APIViewTestCases, APITestCase

from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'PrefixListFamilyTestCase',
    'CustomPrefixTestCase',
    'RouteMapTestCase',
    'RouteMapEntryTestCase',
)


class ASPathTestCase(APIViewTestCases.APIViewTestCase):
    model = ASPath
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'aspath'
    brief_fields = [
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.aspath = (
            cls.model(
                name='AS Path List 1',
            ),
            cls.model(
                name='AS Path List 2',
            ),
            cls.model(
                name='AS Path List 3',
            ),
        )
        cls.model.objects.bulk_create(cls.aspath)

        cls.create_data = [
            {
                'name': 'AS Path List 4',
            },
            {
                'name': 'AS Path List 5',
            },
        ]


class ASPathEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = ASPathEntry
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'aspath_entry'
    brief_fields = [
        'action',
        'aspath',
        'display',
        'id',
        'pattern',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

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

        cls.aspath_entry = (
            cls.model(
                aspath=cls.aspath[0], action='permit', sequence=1, pattern='^2448$'
            ),
            cls.model(
                aspath=cls.aspath[0], action='permit', sequence=2, pattern='^2448 2447$'
            ),
            cls.model(
                aspath=cls.aspath[1], action='permit', sequence=1, pattern='^.*$'
            ),
        )
        cls.model.objects.bulk_create(cls.aspath_entry)

        cls.create_data = [
            {
                'aspath': cls.aspath[0].pk,
                'action': 'permit',
                'sequence': 3,
                'pattern': '^2448 2448 2448$',
            },
            {
                'aspath': cls.aspath[0].pk,
                'action': 'permit',
                'sequence': 4,
                'pattern': '^2448 2448 2448 2448$',
            },
        ]


class PrefixListTestCase(APIViewTestCases.APIViewTestCase):
    model = PrefixList
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'prefixlist'
    brief_fields = [
        'display',
        'family',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = (
            cls.model(
                name='Prefix List 1',
            ),
            cls.model(
                name='Prefix List 2',
            ),
            cls.model(
                name='Prefix List 3',
            ),
        )
        cls.model.objects.bulk_create(cls.prefix_list)

        cls.create_data = [
            {
                'name': 'Prefix List 4',
            },
            {
                'name': 'Prefix List 5',
                'family': 6,
            },
        ]


class PrefixListEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = PrefixListEntry
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'prefixlist_entry'
    brief_fields = [
        'action',
        'assigned_prefix_id',
        'assigned_prefix_type',
        'display',
        'ge',
        'id',
        'le',
        'prefix_list',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        prefixes = (
            Prefix(prefix='10.0.0.0/24'),
            Prefix(prefix='10.0.1.0/24'),
            Prefix(prefix='10.0.2.0/24'),
            Prefix(prefix='10.0.3.0/24'),
        )
        Prefix.objects.bulk_create(prefixes)

        custom_prefixes = (
            CustomPrefix(prefix='10.0.0.0/24'),
            CustomPrefix(prefix='10.0.4.0/24'),
        )
        CustomPrefix.objects.bulk_create(custom_prefixes)

        cls.prefix_list = (
            PrefixList(
                name='Prefix List 1',
            ),
            PrefixList(
                name='Prefix List 2',
            ),
        )
        PrefixList.objects.bulk_create(cls.prefix_list)

        cls.prefix_list_entry = (
            cls.model(
                prefix_list=cls.prefix_list[0],
                action='permit',
                sequence=1,
                assigned_prefix=prefixes[0],
            ),
            cls.model(
                prefix_list=cls.prefix_list[0],
                action='permit',
                sequence=2,
                assigned_prefix=prefixes[1],
            ),
            cls.model(
                prefix_list=cls.prefix_list[1],
                action='permit',
                sequence=1,
                assigned_prefix=custom_prefixes[0],
            ),
        )
        cls.model.objects.bulk_create(cls.prefix_list_entry)

        cls.create_data = [
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 3,
                'assigned_prefix_type': 'ipam.prefix',
                'assigned_prefix_id': prefixes[0].pk,
            },
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 4,
                'assigned_prefix_type': 'netbox_routing_protocols.customprefix',
                'assigned_prefix_id': custom_prefixes[1].pk,
            },
        ]


class CustomPrefixTestCase(APIViewTestCases.APIViewTestCase):
    model = CustomPrefix
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'customprefix'
    brief_fields = ['display', 'family', 'id', 'prefix', 'url']

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        CustomPrefix.objects.bulk_create(
            (
                CustomPrefix(prefix='10.0.0.0/24'),
                CustomPrefix(prefix='10.0.1.0/24'),
                CustomPrefix(prefix='2001:db8::/32'),
            )
        )
        cls.create_data = [
            {'prefix': '10.0.2.0/24'},
            {'prefix': '2001:db8:1::/48'},
        ]

    def test_family_is_exposed(self):
        self.add_permissions('netbox_routing_protocols.view_customprefix')
        for prefix, family in (('10.0.0.0/24', 4), ('2001:db8::/32', 6)):
            obj = CustomPrefix.objects.get(prefix=prefix)
            url = reverse(
                'plugins-api:netbox_routing_protocols-api:customprefix-detail',
                kwargs={'pk': obj.pk},
            )
            response = self.client.get(url, **self.header)
            self.assertEqual(response.data['family']['value'], family)
            for field in ('owner', 'tags', 'custom_fields', 'created', 'last_updated'):
                self.assertIn(field, response.data)


class PrefixListFamilyTestCase(APITestCase):
    """The address family of a prefix list over the API"""

    @classmethod
    def setUpTestData(cls):
        cls.v4 = PrefixList.objects.create(name='v4', family=4)
        cls.v6 = PrefixList.objects.create(name='v6', family=6)

    def _url(self, name, obj=None):
        kwargs = {'pk': obj.pk} if obj else {}
        suffix = 'detail' if obj else 'list'
        return reverse(
            f'plugins-api:netbox_routing_protocols-api:{name}-{suffix}', kwargs=kwargs
        )

    def test_create_and_read_family(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlist',
            'netbox_routing_protocols.view_prefixlist',
        )
        response = self.client.post(
            self._url('prefixlist'),
            {'name': 'new v6', 'family': 6, 'tags': []},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['family']['value'], 6)
        for field in ('owner', 'tags', 'custom_fields', 'created', 'last_updated'):
            self.assertIn(field, response.data)

    def test_family_defaults_to_ipv4(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlist')
        response = self.client.post(
            self._url('prefixlist'), {'name': 'default'}, format='json', **self.header
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['family']['value'], 4)

    def test_family_cannot_be_changed(self):
        self.add_permissions('netbox_routing_protocols.change_prefixlist')
        response = self.client.patch(
            self._url('prefixlist', self.v4),
            {'family': 6},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 400)
        self.v4.refresh_from_db()
        self.assertEqual(self.v4.family, 4)

    def test_entry_family_mismatch_is_rejected(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='2001:db8::/32')
        response = self.client.post(
            self._url('prefixlistentry'),
            {
                'prefix_list': self.v4.pk,
                'action': 'permit',
                'sequence': 1,
                'assigned_prefix_type': 'ipam.prefix',
                'assigned_prefix_id': prefix.pk,
            },
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 400)

    def test_ipv6_entry_with_ge_le(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlistentry',
            'netbox_routing_protocols.view_prefixlistentry',
        )
        prefix = Prefix.objects.create(prefix='2001:db8::/32')
        data = {
            'prefix_list': self.v6.pk,
            'action': 'permit',
            'sequence': 1,
            'assigned_prefix_type': 'ipam.prefix',
            'assigned_prefix_id': prefix.pk,
            'ge': 48,
            'le': 128,
        }
        response = self.client.post(
            self._url('prefixlistentry'), data, format='json', **self.header
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['prefix_list']['family']['value'], 6)
        for field in ('owner', 'tags', 'custom_fields', 'created', 'last_updated'):
            self.assertIn(field, response.data)
        # le above the IPv6 boundary
        data.update(sequence=2, le=129)
        response = self.client.post(
            self._url('prefixlistentry'), data, format='json', **self.header
        )
        self.assertHttpStatus(response, 400)


class RouteMapTestCase(APIViewTestCases.APIViewTestCase):
    model = RouteMap
    view_namespace = "plugins-api:netbox_routing_protocols"
    brief_fields = [
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.route_map = (
            cls.model(
                name='Route Map 1',
            ),
            cls.model(
                name='Route Map 2',
            ),
            cls.model(
                name='Route Map 3',
            ),
        )
        cls.model.objects.bulk_create(cls.route_map)

        cls.create_data = [
            {
                'name': 'Route Map 4',
            },
            {
                'name': 'Route Map 5',
            },
        ]


class RouteMapEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = RouteMapEntry
    view_namespace = "plugins-api:netbox_routing_protocols"
    brief_fields = [
        'action',
        'display',
        'id',
        'route_map',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.route_map = (
            RouteMap(
                name='Route Map 1',
            ),
            RouteMap(
                name='Route Map 2',
            ),
        )
        RouteMap.objects.bulk_create(cls.route_map)

        cls.route_map_entry = (
            cls.model(
                route_map=cls.route_map[0],
                action='permit',
                sequence=1,
                match={'tags': 1},
                set={},
            ),
            cls.model(
                route_map=cls.route_map[0],
                action='permit',
                sequence=2,
                match={'tags': 2},
                set={},
            ),
            cls.model(
                route_map=cls.route_map[1],
                action='permit',
                sequence=1,
                match={'tags': 3},
                set={},
            ),
        )
        cls.model.objects.bulk_create(cls.route_map_entry)

        cls.create_data = [
            {
                'route_map': cls.route_map[0].pk,
                'action': 'permit',
                'sequence': 3,
                'flow_control': 4,
                'match': {'tags': 4},
            },
            {
                'route_map': cls.route_map[0].pk,
                'action': 'permit',
                'sequence': 4,
                'match': {'tags': 5},
            },
        ]
