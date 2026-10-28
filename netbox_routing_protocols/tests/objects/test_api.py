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
        'display',
        'ge',
        'id',
        'le',
        'prefix',
        'prefix_list',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        Prefix.objects.bulk_create(Prefix(prefix=f'10.0.{i}.0/24') for i in range(5))
        prefixes = tuple(Prefix.objects.order_by('prefix'))

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
                prefix=prefixes[0],
            ),
            cls.model(
                prefix_list=cls.prefix_list[0],
                action='permit',
                sequence=2,
                prefix=prefixes[1],
            ),
            cls.model(
                prefix_list=cls.prefix_list[1],
                action='permit',
                sequence=1,
                prefix=prefixes[0],
            ),
        )
        cls.model.objects.bulk_create(cls.prefix_list_entry)

        cls.create_data = [
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 3,
                'prefix': prefixes[0].pk,
            },
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 4,
                'prefix': prefixes[-1].pk,
            },
        ]


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

    def test_prefix_change_that_invalidates_an_entry_is_refused(self):
        self.add_permissions('ipam.change_prefix', 'ipam.view_prefix')
        prefix = Prefix.objects.create(prefix='10.0.0.0/24')
        PrefixListEntry.objects.create(
            prefix_list=self.v4,
            action='permit',
            sequence=1,
            prefix=prefix,
            ge=28,
        )
        url = reverse('ipam-api:prefix-detail', kwargs={'pk': prefix.pk})
        response = self.client.patch(
            url, {'prefix': '10.0.0.0/29'}, format='json', **self.header
        )
        self.assertHttpStatus(response, 400)
        prefix.refresh_from_db()
        self.assertEqual(str(prefix.prefix), '10.0.0.0/24')
        # a compatible change goes through
        response = self.client.patch(
            url, {'prefix': '10.0.0.0/25'}, format='json', **self.header
        )
        self.assertHttpStatus(response, 200)

    def test_entry_family_mismatch_is_rejected(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='2001:db8::/32')
        response = self.client.post(
            self._url('prefixlistentry'),
            {
                'prefix_list': self.v4.pk,
                'action': 'permit',
                'sequence': 1,
                'prefix': prefix.pk,
            },
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 400)

    def _post_entry(self, **data):
        data.setdefault('action', 'permit')
        data.setdefault('sequence', 1)
        return self.client.post(
            self._url('prefixlistentry'), data, format='json', **self.header
        )

    def test_any_shorthands(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlistentry',
            'netbox_routing_protocols.view_prefixlistentry',
        )
        for sequence, (prefix_list, prefix, le) in enumerate(
            (
                (self.v4, 'any', 32),
                (self.v4, '0.0.0.0/0', 32),
                (self.v6, 'ANY', 128),
                (self.v6, '::/0', 128),
            ),
            start=1,
        ):
            with self.subTest(f'{prefix_list.name} {prefix}'):
                response = self._post_entry(
                    prefix_list=prefix_list.pk, prefix=prefix, sequence=sequence
                )
                self.assertHttpStatus(response, 201)
                self.assertIsNone(response.data['prefix'])
                self.assertTrue(response.data['any_prefix'])
                self.assertEqual((response.data['ge'], response.data['le']), (None, le))
        # nothing is created in IPAM
        self.assertFalse(
            Prefix.objects.filter(prefix__in=['0.0.0.0/0', '::/0']).exists()
        )

    def test_any_flag_and_explicit_values(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        response = self._post_entry(prefix_list=self.v4.pk, prefix='any', ge=24)
        self.assertHttpStatus(response, 201)
        self.assertEqual((response.data['ge'], response.data['le']), (24, None))
        # the explicit flag with a null prefix is the same entry
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=None, any_prefix=True, sequence=2, le=32
        )
        self.assertHttpStatus(response, 201)
        self.assertTrue(response.data['any_prefix'])

    def test_any_errors(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        # the all zeros prefix of the other family does not fit the list
        response = self._post_entry(prefix_list=self.v4.pk, prefix='::/0')
        self.assertHttpStatus(response, 400)
        # 'any' without a valid list cannot tell the family
        response = self._post_entry(prefix_list=999999, prefix='any', sequence=2)
        self.assertHttpStatus(response, 400)
        # a prefix and any at the same time
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=prefix.pk, any_prefix=True, sequence=3
        )
        self.assertHttpStatus(response, 400)
        # neither
        response = self._post_entry(prefix_list=self.v4.pk, sequence=4)
        self.assertHttpStatus(response, 400)

    def test_any_on_update_uses_the_list_of_the_entry(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlistentry',
            'netbox_routing_protocols.change_prefixlistentry',
        )
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        response = self._post_entry(prefix_list=self.v4.pk, prefix=prefix.pk)
        self.assertHttpStatus(response, 201)
        url = self._url('prefixlistentry', PrefixListEntry.objects.get())
        response = self.client.patch(
            url, {'prefix': 'any'}, format='json', **self.header
        )
        self.assertHttpStatus(response, 200)
        self.assertIsNone(response.data['prefix'])
        self.assertEqual(response.data['le'], 32)

    def test_sequence_defaults_to_the_next_one(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        data = {'action': 'permit', 'prefix': prefix.pk}
        for list_, expected in ((self.v4, 10), (self.v4, 20), (self.v6, 10)):
            if list_ is self.v6:
                data['prefix'] = Prefix.objects.create(prefix='2001:db8::/32').pk
            response = self.client.post(
                self._url('prefixlistentry'),
                {**data, 'prefix_list': list_.pk},
                format='json',
                **self.header,
            )
            self.assertHttpStatus(response, 201)
            self.assertEqual(response.data['sequence'], expected)
        # an arbitrary one is accepted and the next follows it
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=prefix.pk, sequence=55
        )
        self.assertEqual(response.data['sequence'], 55)
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=prefix.pk, sequence=None
        )
        self.assertEqual(response.data['sequence'], 60)

    def test_bulk_create_assigns_consecutive_sequences(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        entry = {'prefix_list': self.v4.pk, 'action': 'permit', 'prefix': prefix.pk}
        response = self.client.post(
            self._url('prefixlistentry'),
            [entry, entry, {**entry, 'sequence': 5}, entry],
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual([e['sequence'] for e in response.data], [10, 20, 5, 30])

    def test_update_does_not_reassign_the_sequence(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlistentry',
            'netbox_routing_protocols.change_prefixlistentry',
        )
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=prefix.pk, sequence=7
        )
        url = self._url('prefixlistentry', PrefixListEntry.objects.get())
        response = self.client.patch(url, {'le': 24}, format='json', **self.header)
        self.assertHttpStatus(response, 200)
        self.assertEqual(response.data['sequence'], 7)

    def test_exact_length(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        response = self._post_entry(prefix_list=self.v4.pk, prefix=prefix.pk, eq=16)
        self.assertHttpStatus(response, 201)
        self.assertEqual((response.data['ge'], response.data['le']), (16, 16))
        self.assertNotIn('eq', response.data)
        response = self._post_entry(
            prefix_list=self.v4.pk, prefix=prefix.pk, eq=16, ge=12, sequence=2
        )
        self.assertHttpStatus(response, 400)

    def test_large_sequence(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='10.0.0.0/24')
        data = {
            'prefix_list': self.v4.pk,
            'action': 'permit',
            'prefix': prefix.pk,
        }
        for sequence, status in ((4294967294, 201), (0, 400), (4294967295, 400)):
            response = self.client.post(
                self._url('prefixlistentry'),
                {**data, 'sequence': sequence},
                format='json',
                **self.header,
            )
            self.assertHttpStatus(response, status)

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
            'prefix': prefix.pk,
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
