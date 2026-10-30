from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ipam.models import ASN, RIR, VRF
from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.filtersets import OSPFRedistributionFilterSet
from netbox_routing_protocols.forms import OSPFRedistributionForm
from netbox_routing_protocols.models import (
    BGPAddressFamily,
    BGPInstance,
    EIGRPAddressFamily,
    EIGRPRouter,
    ISISAddressFamily,
    ISISInstance,
    OSPFInstance,
    OSPFRedistribution,
    RoutePolicy,
)
from netbox_routing_protocols.tests.base import IPAddressFieldMixin, LeanCoreTestsMixin

__all__ = (
    'OSPFRedistributionModelTestCase',
    'OSPFRedistributionFormTestCase',
    'OSPFRedistributionFilterSetTestCase',
    'OSPFRedistributionViewTestCase',
    'OSPFRedistributionAPITestCase',
)


def _create_fixtures(cls):
    cls.policies = [RoutePolicy.objects.create(name=f'Policy {i}') for i in (1, 2)]
    cls.device = create_test_device(name='Device 1')
    cls.other_device = create_test_device(name='Device 2')
    cls.instances = [
        OSPFInstance.objects.create(
            name=f'Instance {i}',
            device=cls.device,
            vrf=VRF.objects.create(name=f'VRF {i}'),
            router_id=f'1.1.1.{i}',
        )
        for i in (1, 2)
    ]
    cls.other_instance = OSPFInstance.objects.create(
        name='Other', device=cls.other_device, router_id='9.9.9.9'
    )
    cls.vrf = cls.instances[0].vrf
    cls.eigrp = EIGRPRouter.objects.create(device=cls.device, mode='classic', pid=100)
    EIGRPAddressFamily.objects.create(router=cls.eigrp, vrf=cls.vrf, family=4)
    cls.other_eigrp = EIGRPRouter.objects.create(
        device=cls.other_device, mode='classic', pid=100
    )
    cls.isis = ISISInstance.objects.create(
        device=cls.device, process_tag='core', vrf=cls.vrf
    )
    ISISAddressFamily.objects.create(instance=cls.isis, address_family='ipv4')
    cls.other_isis = ISISInstance.objects.create(
        device=cls.other_device, process_tag='core'
    )
    rir = RIR.objects.create(name='RIR', slug='rir')
    cls.bgp = BGPInstance.objects.create(
        name='BGP',
        asn=ASN.objects.create(asn=65000, rir=rir),
        device=cls.device,
        vrf=cls.vrf,
    )
    BGPAddressFamily.objects.create(instance=cls.bgp, address_family='ipv4-unicast')
    cls.other_bgp = BGPInstance.objects.create(
        name='Other BGP',
        asn=ASN.objects.create(asn=65001, rir=rir),
        device=cls.other_device,
    )


class OSPFRedistributionModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _redistribution(self, **kwargs):
        kwargs.setdefault('instance', self.instances[0])
        return OSPFRedistribution(**kwargs)

    def test_defaults(self):
        redistribution = self._redistribution(protocol='static')
        redistribution.full_clean()
        self.assertEqual(redistribution.metric_type, '2')
        self.assertTrue(redistribution.subnets)
        self.assertIsNone(redistribution.source)

    def test_ospf_route_types(self):
        # the display only: another OSPF instance is never a valid source (see the
        # rejection test below)
        redistribution = self._redistribution(
            protocol='ospf',
            ospf_source=self.instances[1],
            ospf_match=['internal', 'external-1', 'nssa-external-2'],
        )
        self.assertEqual(
            redistribution.ospf_match_display,
            'Internal, External Type 1, NSSA External Type 2',
        )
        self.assertEqual(self._redistribution(protocol='static').ospf_match, [])
        self.assertEqual(
            self._redistribution(protocol='static').ospf_match_display, '—'
        )

    def test_another_ospf_instance_is_never_a_source(self):
        # one OSPF instance per device, VRF and IP version: the other one of the same
        # device runs in another VRF or family (#528)
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='ospf', ospf_source=self.instances[1]
            ).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)

    def test_ospf_route_types_are_checked(self):
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='ospf', ospf_source=self.instances[1], ospf_match=['bogus']
            ).full_clean()
        self.assertIn('ospf_match', cm.exception.error_dict)

    def test_ospf_route_types_only_when_the_source_is_ospf(self):
        for protocol, source in (
            ('static', {}),
            ('connected', {}),
            ('eigrp', {'eigrp_source': self.eigrp}),
        ):
            with self.subTest(protocol=protocol):
                with self.assertRaises(ValidationError) as cm:
                    self._redistribution(
                        protocol=protocol, ospf_match=['internal'], **source
                    ).full_clean()
                self.assertIn('ospf_match', cm.exception.error_dict)

    def test_connected_has_no_source(self):
        redistribution = self._redistribution(protocol='connected')
        redistribution.full_clean()
        self.assertIsNone(redistribution.source)
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='connected', eigrp_source=self.eigrp
            ).full_clean()
        self.assertIn('eigrp_source', cm.exception.error_dict)

    def test_connected_is_redistributed_only_once_per_instance(self):
        OSPFRedistribution.objects.create(
            instance=self.instances[0], protocol='connected'
        )
        with self.assertRaises(IntegrityError):
            OSPFRedistribution.objects.create(
                instance=self.instances[0], protocol='connected'
            )

    def test_every_protocol_with_its_source_is_valid(self):
        for protocol, source in (
            ('eigrp', {'eigrp_source': self.eigrp}),
            ('bgp', {'bgp_source': self.bgp}),
            ('isis', {'isis_source': self.isis}),
        ):
            with self.subTest(protocol=protocol):
                redistribution = self._redistribution(protocol=protocol, **source)
                redistribution.full_clean()
                self.assertIsNotNone(redistribution.source)

    def test_non_static_protocol_requires_its_source(self):
        for protocol, field in (
            ('ospf', 'ospf_source'),
            ('eigrp', 'eigrp_source'),
            ('bgp', 'bgp_source'),
            ('isis', 'isis_source'),
        ):
            with self.subTest(protocol=protocol):
                with self.assertRaises(ValidationError) as cm:
                    self._redistribution(protocol=protocol).full_clean()
                self.assertIn(field, cm.exception.error_dict)

    def test_static_and_foreign_sources_are_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='static', eigrp_source=self.eigrp
            ).full_clean()
        self.assertIn('eigrp_source', cm.exception.error_dict)

        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='bgp', bgp_source=self.bgp, isis_source=self.isis
            ).full_clean()
        self.assertIn('isis_source', cm.exception.error_dict)

    def test_ospf_instance_cannot_be_redistributed_into_itself(self):
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='ospf', ospf_source=self.instances[0]
            ).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)

    def test_source_must_be_on_the_same_device(self):
        for protocol, source in (
            ('ospf', {'ospf_source': self.other_instance}),
            ('eigrp', {'eigrp_source': self.other_eigrp}),
            ('isis', {'isis_source': self.other_isis}),
            ('bgp', {'bgp_source': self.other_bgp}),
        ):
            with self.subTest(protocol=protocol):
                with self.assertRaises(ValidationError) as cm:
                    self._redistribution(protocol=protocol, **source).full_clean()
                self.assertIn(f'{protocol}_source', cm.exception.error_dict)

    def test_bgp_instance_must_be_on_the_instance_device(self):
        self._redistribution(protocol='bgp', bgp_source=self.bgp).full_clean()

    def test_limits(self):
        redistribution = self._redistribution(protocol='static')
        for metric in (0, 16777214):
            redistribution.metric = metric
            redistribution.full_clean()
        redistribution.metric = 16777215
        with self.assertRaises(ValidationError) as cm:
            redistribution.full_clean()
        self.assertIn('metric', cm.exception.error_dict)

        redistribution.metric = None
        for route_tag in (0, 4294967295):
            redistribution.route_tag = route_tag
            redistribution.full_clean()
        redistribution.route_tag = 4294967296
        with self.assertRaises(ValidationError) as cm:
            redistribution.full_clean()
        self.assertIn('route_tag', cm.exception.error_dict)

    def test_a_source_is_redistributed_only_once_per_instance(self):
        OSPFRedistribution.objects.create(
            instance=self.instances[0], protocol='eigrp', eigrp_source=self.eigrp
        )
        with self.assertRaises(IntegrityError):
            OSPFRedistribution.objects.create(
                instance=self.instances[0], protocol='eigrp', eigrp_source=self.eigrp
            )

    def test_static_is_redistributed_only_once_per_instance(self):
        OSPFRedistribution.objects.create(instance=self.instances[0], protocol='static')
        with self.assertRaises(IntegrityError):
            OSPFRedistribution.objects.create(
                instance=self.instances[0], protocol='static'
            )

    def test_deleting_the_instance_deletes_its_redistributions(self):
        OSPFRedistribution.objects.create(instance=self.instances[0], protocol='static')
        self.instances[0].delete()
        self.assertFalse(OSPFRedistribution.objects.exists())


class OSPFRedistributionFormTestCase(TestCase):
    SOURCE_FIELDS = ('ospf_source', 'eigrp_source', 'bgp_source', 'isis_source')

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _source_fields(self, form):
        return [name for name in self.SOURCE_FIELDS if name in form.fields]

    def test_the_route_types_are_shown_only_for_ospf(self):
        self.assertIn(
            'ospf_match', OSPFRedistributionForm(initial={'protocol': 'ospf'}).fields
        )
        for protocol in (None, 'static', 'connected', 'eigrp'):
            with self.subTest(protocol=protocol):
                form = OSPFRedistributionForm(
                    initial={'protocol': protocol} if protocol else {}
                )
                self.assertNotIn('ospf_match', form.fields)

    def test_the_route_types_need_an_ospf_source_of_the_same_vrf_and_family(self):
        form = OSPFRedistributionForm(
            data={
                'instance': self.instances[0].pk,
                'protocol': 'ospf',
                'ospf_source': self.instances[1].pk,
                'ospf_match': ['internal', 'external-2'],
                'metric_type': '2',
                'subnets': 'on',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('ospf_source', form.errors)

    def test_only_the_source_of_the_selected_protocol_is_shown(self):
        for protocol, field in (
            ('ospf', 'ospf_source'),
            ('eigrp', 'eigrp_source'),
            ('bgp', 'bgp_source'),
            ('isis', 'isis_source'),
        ):
            with self.subTest(protocol=protocol):
                form = OSPFRedistributionForm(initial={'protocol': protocol})
                self.assertEqual(self._source_fields(form), [field])
                form = OSPFRedistributionForm(data={'protocol': protocol})
                self.assertEqual(self._source_fields(form), [field])

    def test_no_source_without_a_source_protocol(self):
        for protocol in (None, '', 'connected', 'static'):
            with self.subTest(protocol=protocol):
                form = OSPFRedistributionForm(
                    initial={'protocol': protocol} if protocol else {}
                )
                self.assertEqual(self._source_fields(form), [])

    def test_editing_shows_the_source_of_the_current_protocol(self):
        redistribution = OSPFRedistribution.objects.create(
            instance=self.instances[0], protocol='eigrp', eigrp_source=self.eigrp
        )
        form = OSPFRedistributionForm(instance=redistribution)
        self.assertEqual(self._source_fields(form), ['eigrp_source'])

    def test_changing_the_protocol_clears_the_previous_source(self):
        redistribution = OSPFRedistribution.objects.create(
            instance=self.instances[0], protocol='eigrp', eigrp_source=self.eigrp
        )
        for protocol in ('static', 'connected'):
            with self.subTest(protocol=protocol):
                form = OSPFRedistributionForm(
                    data={
                        'instance': self.instances[0].pk,
                        'protocol': protocol,
                        'metric_type': '2',
                        'subnets': 'on',
                    },
                    instance=redistribution,
                )
                self.assertTrue(form.is_valid(), form.errors)
                form.save()
                redistribution.refresh_from_db()
                self.assertEqual(redistribution.protocol, protocol)
                self.assertIsNone(redistribution.eigrp_source)

    def test_the_selected_source_is_saved(self):
        form = OSPFRedistributionForm(
            data={
                'instance': self.instances[0].pk,
                'protocol': 'eigrp',
                'eigrp_source': self.eigrp.pk,
                'metric_type': '2',
                'subnets': 'on',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().eigrp_source, self.eigrp)


class OSPFRedistributionFilterSetTestCase(TestCase):
    queryset = OSPFRedistribution.objects.all()
    filterset = OSPFRedistributionFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFRedistribution.objects.bulk_create(
            (
                OSPFRedistribution(
                    instance=cls.instances[0],
                    protocol='static',
                    metric=10,
                    route_policy=cls.policies[0],
                ),
                OSPFRedistribution(
                    instance=cls.instances[0],
                    protocol='eigrp',
                    eigrp_source=cls.eigrp,
                    metric_type='1',
                    route_tag=7,
                ),
                OSPFRedistribution(
                    instance=cls.instances[1], protocol='bgp', bgp_source=cls.bgp
                ),
                OSPFRedistribution(
                    instance=cls.other_instance,
                    protocol='isis',
                    isis_source=cls.isis,
                    subnets=False,
                ),
                OSPFRedistribution(
                    instance=cls.instances[1],
                    protocol='ospf',
                    ospf_source=cls.instances[0],
                    ospf_match=['internal', 'external-1'],
                ),
            )
        )

    def count(self, params):
        return self.filterset(params, self.queryset).qs.count()

    def test_instance_and_device(self):
        self.assertEqual(self.count({'instance_id': [self.instances[0].pk]}), 2)
        self.assertEqual(self.count({'instance': ['Instance 2']}), 2)
        self.assertEqual(self.count({'device_id': [self.device.pk]}), 4)

    def test_protocol_and_sources(self):
        self.assertEqual(self.count({'protocol': ['static', 'bgp']}), 2)
        self.assertEqual(self.count({'eigrp_source_id': [self.eigrp.pk]}), 1)
        self.assertEqual(self.count({'bgp_source_id': [self.bgp.pk]}), 1)
        self.assertEqual(self.count({'isis_source_id': [self.isis.pk]}), 1)

    def test_attributes(self):
        self.assertEqual(self.count({'metric': [10]}), 1)
        self.assertEqual(self.count({'metric_type': ['1']}), 1)
        self.assertEqual(self.count({'subnets': False}), 1)
        self.assertEqual(self.count({'route_tag': [7]}), 1)
        self.assertEqual(self.count({'ospf_match': ['internal']}), 1)
        self.assertEqual(self.count({'ospf_match': ['external-2']}), 0)

    def test_q(self):
        self.assertEqual(self.count({'q': 'Policy 1'}), 1)
        self.assertEqual(self.count({'q': 'Instance 1'}), 2)


class OSPFRedistributionViewTestCase(
    LeanCoreTestsMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFRedistribution

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFRedistribution.objects.bulk_create(
            (
                OSPFRedistribution(instance=cls.instances[0], protocol='static'),
                OSPFRedistribution(
                    instance=cls.instances[0], protocol='eigrp', eigrp_source=cls.eigrp
                ),
                OSPFRedistribution(
                    instance=cls.instances[0], protocol='bgp', bgp_source=cls.bgp
                ),
            )
        )
        cls.form_data = {
            'instance': cls.instances[0].pk,
            'protocol': 'isis',
            'isis_source': cls.isis.pk,
            'metric': 20,
            'metric_type': '1',
            'subnets': True,
            'route_tag': 5,
            'route_policy': cls.policies[0].pk,
        }
        cls.bulk_edit_data = {
            'description': 'A test description',
            'route_policy': cls.policies[1].pk,
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfredistribution_{}'


class OSPFRedistributionAPITestCase(
    LeanCoreTestsMixin, IPAddressFieldMixin, APIViewTestCases.APIViewTestCase
):
    model = OSPFRedistribution
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['display', 'id', 'instance', 'protocol', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'netbox_routing_protocols.view_eigrprouter',
        'netbox_routing_protocols.view_bgpinstance',
        'netbox_routing_protocols.view_isisinstance',
        'dcim.view_device',
        'ipam.view_asn',
    )

    bulk_update_data = {'description': 'A test description'}
    # Changing the protocol of an existing object also needs its source changed
    update_data = {'metric': 30}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFRedistribution.objects.bulk_create(
            (
                OSPFRedistribution(instance=cls.instances[0], protocol='static'),
                OSPFRedistribution(
                    instance=cls.instances[0], protocol='eigrp', eigrp_source=cls.eigrp
                ),
                OSPFRedistribution(
                    instance=cls.instances[0], protocol='bgp', bgp_source=cls.bgp
                ),
            )
        )
        cls.create_data = [
            {
                'instance': cls.instances[0].pk,
                'protocol': 'isis',
                'isis_source': cls.isis.pk,
                'metric': 20,
                'route_policy': cls.policies[0].pk,
            },
        ]


class OSPFRedistributionRoutePolicyTestCase(TestCase):
    """The route policy of a redistribution is an object that cannot be deleted in use."""

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        cls.redistribution = OSPFRedistribution.objects.create(
            instance=cls.instances[0], protocol='static', route_policy=cls.policies[0]
        )

    def test_policy_in_use_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.policies[0].delete()

    def test_filter_by_policy(self):
        qs = OSPFRedistributionFilterSet(
            {'route_policy': [self.policies[0].name]},
            OSPFRedistribution.objects.all(),
        ).qs
        self.assertEqual(list(qs), [self.redistribution])
