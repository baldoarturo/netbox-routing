from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing.choices import OSPFNetworkTypeChoices
from netbox_routing.models import *

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def _instance(self, router_id):
        return OSPFInstance(
            name='Instance 1', device=self.device, router_id=router_id, process_id=1
        )

    def test_router_id_ipv4_is_valid(self):
        self._instance('10.0.0.1').full_clean()

    def test_router_id_ipv6_is_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            self._instance('2001:db8::1').full_clean()
        self.assertIn('router_id', cm.exception.error_dict)

    def test_router_id_zero_is_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            self._instance('0.0.0.0').full_clean()
        self.assertIn('router_id', cm.exception.error_dict)

    def test_router_id_with_mask_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._instance('10.0.0.1/24').full_clean()


class OSPFAreaTestCase(TestCase):
    pass


class OSPFInterfaceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1',
            device=cls.device,
            router_id='1.1.1.1',
            process_id=1,
        )
        area = OSPFArea.objects.create(area_id='0.0.0.0')
        OSPFInterface.objects.create(
            instance=cls.instance, area=area, interface=interface
        )

    def test_network_type_defaults_to_broadcast(self):
        self.assertEqual(
            OSPFInterface.objects.get().network_type, OSPFNetworkTypeChoices.BROADCAST
        )

    def test_cost_limits(self):
        ospf_interface = OSPFInterface.objects.get()
        for cost in (1, 65535, None):
            ospf_interface.cost = cost
            ospf_interface.full_clean()
        for cost in (0, 65536):
            ospf_interface.cost = cost
            with self.assertRaises(ValidationError) as cm:
                ospf_interface.full_clean()
            self.assertIn('cost', cm.exception.error_dict)

    def test_delete_device_with_ospf_interfaces(self):
        self.device.delete()
        self.assertFalse(OSPFInstance.objects.exists())
        self.assertFalse(OSPFInterface.objects.exists())

    def test_delete_instance_with_interfaces_is_blocked(self):
        with self.assertRaises(RestrictedError):
            self.instance.delete()
