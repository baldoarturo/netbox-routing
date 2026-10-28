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
    pass


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

    def test_delete_device_with_ospf_interfaces(self):
        self.device.delete()
        self.assertFalse(OSPFInstance.objects.exists())
        self.assertFalse(OSPFInterface.objects.exists())

    def test_delete_instance_with_interfaces_is_blocked(self):
        with self.assertRaises(RestrictedError):
            self.instance.delete()
