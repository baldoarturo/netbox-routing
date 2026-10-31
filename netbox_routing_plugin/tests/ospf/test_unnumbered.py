from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from ipam.models import IPAddress
from utilities.testing import create_test_device

from netbox_routing_plugin.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
)

__all__ = ('OSPFUnnumberedTestCase',)


class OSPFUnnumberedTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.address = IPAddress.objects.create(
            address='10.0.0.1/30', assigned_object=cls.interface
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1'
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _interface(self, **kwargs):
        return OSPFInterface(
            instance=self.instance, area=self.area, interface=self.interface, **kwargs
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_off_by_default(self):
        interface = self._interface()
        interface.full_clean()
        self.assertFalse(interface.unnumbered)

    def test_only_point_to_point(self):
        self._interface(unnumbered=True, network_type='point_to_point').full_clean()
        for network_type in ('broadcast', 'point_to_multipoint', 'loopback'):
            with self.subTest(network_type=network_type):
                self._assert_invalid(
                    self._interface(unnumbered=True, network_type=network_type),
                    'unnumbered',
                )

    def test_unnumbered_interface_has_no_networks(self):
        interface = self._interface(network_type='point_to_point')
        interface.save()
        OSPFNetwork.objects.create(ospf_interface=interface, ip_address=self.address)
        interface.unnumbered = True
        self._assert_invalid(interface, 'unnumbered')

    def test_network_cannot_be_added_to_an_unnumbered_interface(self):
        interface = self._interface(unnumbered=True, network_type='point_to_point')
        interface.save()
        self._assert_invalid(
            OSPFNetwork(ospf_interface=interface, ip_address=self.address),
            'ospf_interface',
        )
