from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF, IPAddress
from utilities.testing import create_test_device

from netbox_routing_protocols.choices import OSPFAddressFamilyChoices
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFAreaRange,
    OSPFInstance,
    OSPFInterface,
    OSPFNeighbor,
    OSPFNetwork,
    OSPFPrefixSID,
    OSPFSummaryAddress,
)

__all__ = ('OSPFAddressFamilyTestCase',)

IPV4 = OSPFAddressFamilyChoices.IPV4
IPV6 = OSPFAddressFamilyChoices.IPV6


class OSPFAddressFamilyTestCase(TestCase):
    """OSPFv2 (IPv4) and OSPFv3 (IPv6) instances: uniqueness, locked family, addresses."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.v4 = OSPFInstance.objects.create(
            name='v2', device=cls.device, router_id='1.1.1.1'
        )
        cls.v6 = OSPFInstance.objects.create(
            name='v3',
            device=cls.device,
            router_id='1.1.1.1',
            address_family=IPV6,
            ospf_instance_id=0,
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_default_is_ipv4(self):
        self.assertEqual(self.v4.address_family, IPV4)
        self.assertEqual(self.v4.ip_version, 4)
        self.assertEqual(self.v6.ip_version, 6)

    def test_one_instance_per_device_vrf_and_family(self):
        other = OSPFInstance(name='other', device=self.device, router_id='2.2.2.2')
        with self.assertRaises(ValidationError):
            other.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            other.save()
        other.address_family = IPV6
        with self.assertRaises(ValidationError):
            other.full_clean()

    def test_same_family_in_another_vrf(self):
        vrf = VRF.objects.create(name='VRF 1')
        OSPFInstance(
            name='in vrf', device=self.device, vrf=vrf, router_id='2.2.2.2'
        ).full_clean()

    def test_family_cannot_change(self):
        self.v4.address_family = IPV6
        self._assert_invalid(self.v4, 'address_family')
        self.v6.address_family = IPV4
        self._assert_invalid(self.v6, 'address_family')

    def test_te_router_address_follows_the_family(self):
        self.v6.te_router_address = '10.0.0.1'
        self._assert_invalid(self.v6, 'te_router_address')

    def test_no_networks_on_ipv6(self):
        area = OSPFArea.objects.create(instance=self.v6, area_id='1')
        ospf_interface = OSPFInterface.objects.create(
            instance=self.v6, area=area, interface=self.interface
        )
        address = IPAddress.objects.create(
            address='10.0.0.1/30', assigned_object=self.interface
        )
        self._assert_invalid(
            OSPFNetwork(ospf_interface=ospf_interface, ip_address=address),
            'ospf_interface',
        )

    def test_no_unnumbered_on_ipv6(self):
        area = OSPFArea.objects.create(instance=self.v6, area_id='1')
        self._assert_invalid(
            OSPFInterface(
                instance=self.v6,
                area=area,
                interface=self.interface,
                network_type='point_to_point',
                unnumbered=True,
            ),
            'unnumbered',
        )

    def test_neighbor_addresses(self):
        area = OSPFArea.objects.create(instance=self.v6, area_id='1')
        ospf_interface = OSPFInterface.objects.create(
            instance=self.v6,
            area=area,
            interface=self.interface,
            network_type='non_broadcast',
        )
        for address, valid in (
            ('fe80::2', True),
            ('2001:db8::2', False),
            ('10.0.0.2', False),
            ('ff02::5', False),
        ):
            neighbor = OSPFNeighbor(
                ospf_interface=ospf_interface, ip_address=address, priority=1
            )
            if valid:
                neighbor.full_clean()
            else:
                self._assert_invalid(neighbor, 'ip_address')

    def test_ipv4_neighbor_cannot_be_ipv6(self):
        area = OSPFArea.objects.create(instance=self.v4, area_id='1')
        ospf_interface = OSPFInterface.objects.create(
            instance=self.v4,
            area=area,
            interface=self.interface,
            network_type='non_broadcast',
        )
        self._assert_invalid(
            OSPFNeighbor(
                ospf_interface=ospf_interface, ip_address='fe80::2', priority=1
            ),
            'ip_address',
        )

    def test_prefixes_follow_the_family(self):
        area6 = OSPFArea.objects.create(instance=self.v6, area_id='1')
        area4 = OSPFArea.objects.create(instance=self.v4, area_id='1')
        OSPFAreaRange(area=area6, prefix='2001:db8::/32').full_clean()
        self._assert_invalid(OSPFAreaRange(area=area6, prefix='10.0.0.0/8'), 'prefix')
        self._assert_invalid(
            OSPFAreaRange(area=area4, prefix='2001:db8::/32'), 'prefix'
        )
        OSPFSummaryAddress(instance=self.v6, prefix='2001:db8::/32').full_clean()
        self._assert_invalid(
            OSPFSummaryAddress(instance=self.v6, prefix='10.0.0.0/8'), 'prefix'
        )
        self._assert_invalid(
            OSPFSummaryAddress(instance=self.v4, prefix='2001:db8::/32'), 'prefix'
        )

    def test_prefix_sid_follows_the_family(self):
        self.v6.opaque_capability = True
        self.v6.segment_routing = True
        self.v6.srgb_start = 16000
        self.v6.srgb_size = 8000
        self.v6.save()
        OSPFPrefixSID(
            instance=self.v6, prefix='2001:db8::1/128', sid=1, node_sid=True
        ).full_clean()
        self._assert_invalid(
            OSPFPrefixSID(
                instance=self.v6, prefix='2001:db8::/64', sid=1, node_sid=True
            ),
            'node_sid',
        )
        self._assert_invalid(
            OSPFPrefixSID(instance=self.v6, prefix='10.0.0.1/32', sid=1), 'prefix'
        )

    def test_instance_id_range_by_family(self):
        self.v4.ospf_instance_id = 128
        self._assert_invalid(self.v4, 'ospf_instance_id')
        self.v6.ospf_instance_id = 255
        self.v6.full_clean()
        self.v6.ospf_instance_id = 256
        self._assert_invalid(self.v6, 'ospf_instance_id')

    def test_no_opaque_lsas_on_ipv6(self):
        self.v6.opaque_capability = True
        self._assert_invalid(self.v6, 'opaque_capability')

    def test_traffic_engineering_and_sr_do_not_need_opaque_on_ipv6(self):
        self.v6.te_router_address = '2001:db8::1'
        self.v6.segment_routing = True
        self.v6.full_clean()
        self.v4.segment_routing = True
        self._assert_invalid(self.v4, 'segment_routing')
