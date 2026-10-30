# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from dcim.models import Device, Interface
from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_protocols.filtersets import (
    ISISInstanceFilterSet,
    ISISInterfaceFilterSet,
    ISISPrefixSIDFilterSet,
    ISISSettingFilterSet,
    ISISSRv6LocatorFilterSet,
)
from netbox_routing_protocols.models import (
    ISISInstance,
    ISISPrefixSID,
    ISISInterface,
    ISISSetting,
    ISISSRv6Locator,
)

__all__ = (
    'ISISInstanceFilterSetTestCase',
    'ISISAttributeFilterSetTestCase',
    'ISISInterfaceFilterSetTestCase',
    'ISISSettingFilterSetTestCase',
    'ISISSRv6LocatorFilterSetTestCase',
)


class ISISInstanceFilterSetTestCase(TestCase):
    queryset = ISISInstance.objects.all()
    filterset = ISISInstanceFilterSet

    @classmethod
    def setUpTestData(cls):
        vrfs = (
            VRF(name='VRF 1'),
            VRF(name='VRF 2'),
            VRF(name='VRF 3'),
        )
        VRF.objects.bulk_create(vrfs)

        devices = [
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
            create_test_device(name='Device 3'),
            create_test_device(name='Device 4'),
        ]

        data = (
            ISISInstance(
                device=devices[0],
                vrf=vrfs[0],
                process_tag='CORE',
                net='49.0001.0000.0000.0001.00',
                is_type='level-1-2',
            ),
            ISISInstance(
                device=devices[1],
                vrf=vrfs[1],
                process_tag='EDGE',
                net='49.0001.0000.0000.0002.00',
                is_type='level-2-only',
            ),
            ISISInstance(
                device=devices[2],
                vrf=None,
                process_tag='',
                net='49.0001.0000.0000.0003.00',
                is_type='level-1',
            ),
            ISISInstance(
                device=devices[3],
                vrf=vrfs[2],
                process_tag='FABRIC',
                net='49.0001.0000.0000.0004.00',
                is_type='level-1-2',
            ),
        )
        ISISInstance.objects.bulk_create(data)

    def test_q(self):
        params = {'q': 'CORE'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search_strips_whitespace(self):
        # search() must trim before the icontains match, otherwise '  CORE  '
        # would never match the 'CORE' process tag. Call search() directly: the
        # `q` form field already strips, which would otherwise mask an untrimmed
        # search() and make this a false pass.
        qs = self.filterset().search(self.queryset, 'q', '  CORE  ')
        self.assertEqual(qs.count(), 1)

    def test_process_tag(self):
        params = {'process_tag': ['CORE', 'EDGE']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_vrf(self):
        data = VRF.objects.order_by('pk')[:2]

        params = {'vrf_id': [data[0].pk, data[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'vrf': [data[0].name, data[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_device(self):
        data = Device.objects.order_by('pk')[:2]

        params = {'device_id': [data[0].pk, data[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'device': [data[0].name, data[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class ISISInterfaceFilterSetTestCase(TestCase):
    queryset = ISISInterface.objects.all()
    filterset = ISISInterfaceFilterSet

    @classmethod
    def setUpTestData(cls):
        vrfs = (
            VRF(name='VRF 1'),
            VRF(name='VRF 2'),
            VRF(name='VRF 3'),
        )
        VRF.objects.bulk_create(vrfs)

        devices = (
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
            create_test_device(name='Device 3'),
            create_test_device(name='Device 4'),
        )
        interfaces = (
            Interface(device=devices[0], name='Interface 1', type='virtual'),
            Interface(device=devices[1], name='Interface 2', type='virtual'),
            Interface(device=devices[2], name='Interface 3', type='virtual'),
            Interface(device=devices[3], name='Interface 4', type='virtual'),
        )
        Interface.objects.bulk_create(interfaces)

        instances = (
            ISISInstance(
                device=devices[0],
                vrf=vrfs[0],
                process_tag='CORE',
                net='49.0001.0000.0000.0001.00',
                is_type='level-1-2',
            ),
            ISISInstance(
                device=devices[1],
                vrf=vrfs[1],
                process_tag='EDGE',
                net='49.0001.0000.0000.0002.00',
                is_type='level-2-only',
            ),
            ISISInstance(
                device=devices[2],
                vrf=None,
                process_tag='',
                net='49.0001.0000.0000.0003.00',
                is_type='level-1',
            ),
            ISISInstance(
                device=devices[3],
                vrf=vrfs[2],
                process_tag='FABRIC',
                net='49.0001.0000.0000.0004.00',
                is_type='level-1-2',
            ),
        )
        ISISInstance.objects.bulk_create(instances)

        data = (
            ISISInterface(
                interface=interfaces[0],
                instance=ISISInstance.objects.get(process_tag='CORE'),
                address_family='ipv4',
                circuit_type='level-1-2',
                network_type='point-to-point',
                passive=True,
                hello_auth_type='md5',
                hello_auth_key='s3cret',
            ),
            ISISInterface(
                interface=interfaces[1],
                instance=ISISInstance.objects.get(process_tag='EDGE'),
                address_family='ipv6',
                circuit_type='level-2-only',
                passive=False,
            ),
            ISISInterface(
                interface=interfaces[2],
                instance=ISISInstance.objects.get(net='49.0001.0000.0000.0003.00'),
                address_family='ipv4',
                circuit_type='level-1',
                passive=True,
            ),
            ISISInterface(
                interface=interfaces[3],
                instance=ISISInstance.objects.get(process_tag='FABRIC'),
                address_family='ipv6',
                circuit_type='level-1-2',
                passive=False,
            ),
        )
        ISISInterface.objects.bulk_create(data)

    def test_q(self):
        params = {'q': 'Interface 1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

        params = {'q': 'CORE'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_search_strips_whitespace(self):
        # See ISISInstanceFilterSetTestCase.test_search_strips_whitespace: the
        # `q` field strips upstream, so exercise search() directly.
        qs = self.filterset().search(self.queryset, 'q', '  CORE  ')
        self.assertEqual(qs.count(), 1)

    def test_instances(self):
        data = ISISInstance.objects.order_by('pk')[:2]

        params = {'instance_id': [data[0].pk, data[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_address_family(self):
        params = {'address_family': ['ipv4']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_devices(self):
        data = Device.objects.order_by('pk')[:2]

        params = {'device_id': [data[0].pk, data[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'device': [data[0].name, data[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_interfaces(self):
        data = Interface.objects.order_by('pk')[:2]

        params = {'interface_id': [data[0].pk, data[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

        params = {'interface': [data[0].name, data[1].name]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_passive(self):
        params = {'passive': True}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_hello_auth_type(self):
        params = {'hello_auth_type': ['md5']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)


class ISISSRv6LocatorFilterSetTestCase(TestCase):
    queryset = ISISSRv6Locator.objects.all()
    filterset = ISISSRv6LocatorFilterSet

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )
        ISISSRv6Locator.objects.create(
            instance=instance, name='LOC-A', prefix='fc00:a::/48'
        )
        ISISSRv6Locator.objects.create(
            instance=instance, name='LOC-B', prefix='fc00:b::/48'
        )

    def test_q_matches_name(self):
        # search() matches on the locator name; before the fix it was a no-op that
        # returned the full queryset regardless of the term.
        self.assertEqual(self.filterset({'q': 'LOC-A'}, self.queryset).qs.count(), 1)

    def test_search_ignores_blank(self):
        # A blank/whitespace term must not filter anything out.
        self.assertEqual(self.filterset().search(self.queryset, 'q', '   ').count(), 2)

    def test_name(self):
        params = {'name': ['LOC-B']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_filter_prefix_none_safe(self):
        # filter_prefix must not raise on a None value (an empty prefix filter can
        # pass None); it should return the queryset unfiltered.
        self.assertEqual(
            self.filterset().filter_prefix(self.queryset, 'prefix', None).count(), 2
        )


class ISISSettingFilterSetTestCase(TestCase):
    queryset = ISISSetting.objects.all()
    filterset = ISISSettingFilterSet

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.inst1 = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )
        cls.inst2 = ISISInstance.objects.create(
            device=device, process_tag='EDGE', net='49.0001.0000.0000.0002.00'
        )
        ct = ContentType.objects.get_for_model(ISISInstance)
        ISISSetting.objects.create(
            assigned_object_type=ct,
            assigned_object_id=cls.inst1.pk,
            key='ldp_sync',
            value='true',
        )
        ISISSetting.objects.create(
            assigned_object_type=ct,
            assigned_object_id=cls.inst2.pk,
            key='graceful_restart',
            value='true',
        )

    def test_assigned_object_type(self):
        ct = ContentType.objects.get_for_model(ISISInstance)
        params = {'assigned_object_type': ct.pk}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_assigned_object_id(self):
        params = {'assigned_object_id': [self.inst1.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_key(self):
        params = {'key': ['ldp_sync']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_matches_key(self):
        # search() matches on key/value; 'ldp_sync' hits one setting's key.
        self.assertEqual(self.filterset({'q': 'ldp_sync'}, self.queryset).qs.count(), 1)

    def test_search_ignores_blank(self):
        # A blank/whitespace term must not filter anything out.
        self.assertEqual(self.filterset().search(self.queryset, 'q', '   ').count(), 2)


class ISISAttributeFilterSetTestCase(TestCase):
    """Filters on the attributes of the instance, interface and prefix-SID (#441)."""

    @classmethod
    def setUpTestData(cls):
        devices = [create_test_device(name=f'Device {i}') for i in (1, 2)]
        cls.instances = [
            ISISInstance.objects.create(
                device=devices[0],
                metric_style='wide',
                overload_bit=True,
                fast_reroute='ti-lfa',
                distance=115,
            ),
            ISISInstance.objects.create(
                device=devices[1], metric_style='narrow', te_enabled=True
            ),
        ]
        cls.interfaces = [
            ISISInterface.objects.create(
                instance=cls.instances[0],
                interface=Interface.objects.create(
                    name='eth0', device=devices[0], type='virtual'
                ),
                address_family='ipv4',
                bfd_enabled=True,
                frr_protection='node',
                mesh_group='blocked',
            ),
            ISISInterface.objects.create(
                instance=cls.instances[1],
                interface=Interface.objects.create(
                    name='eth0', device=devices[1], type='virtual'
                ),
                address_family='ipv4',
                bfd_enabled=False,
            ),
        ]
        ISISPrefixSID.objects.create(
            interface=cls.interfaces[0], sid_index=1, no_php=True
        )
        ISISPrefixSID.objects.create(
            interface=cls.interfaces[1], sid_index=2, no_php=False
        )

    def _ids(self, filterset, params, queryset):
        return set(filterset(params, queryset).qs.values_list('pk', flat=True))

    def test_instance_filters(self):
        qs = ISISInstance.objects.all()
        first, second = self.instances
        for params, expected in (
            ({'metric_style': ['wide']}, first),
            ({'overload_bit': True}, first),
            ({'fast_reroute': ['ti-lfa']}, first),
            ({'distance': [115]}, first),
            ({'te_enabled': True}, second),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self._ids(ISISInstanceFilterSet, params, qs), {expected.pk}
                )

    def test_interface_filters(self):
        qs = ISISInterface.objects.all()
        first, second = self.interfaces
        for params, expected in (
            ({'bfd_enabled': True}, first),
            ({'bfd_enabled': False}, second),
            ({'frr_protection': ['node']}, first),
            ({'mesh_group': ['blocked']}, first),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self._ids(ISISInterfaceFilterSet, params, qs), {expected.pk}
                )

    def test_prefix_sid_flag_filter(self):
        qs = ISISPrefixSID.objects.all()
        self.assertEqual(ISISPrefixSIDFilterSet({'no_php': True}, qs).qs.count(), 1)
