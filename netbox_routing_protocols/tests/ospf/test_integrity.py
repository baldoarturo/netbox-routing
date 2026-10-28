from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_protocols.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFInterfaceScopeTestCase',)


class OSPFInterfaceScopeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1', process_id=1
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def test_interface_must_be_on_the_device_of_the_instance(self):
        other = create_test_device(name='Device 2')
        interface = Interface.objects.create(
            name='Interface 9', device=other, type='virtual'
        )
        ospf_interface = OSPFInterface(
            instance=self.instance,
            area=self.area,
            interface=interface,
        )
        with self.assertRaises(ValidationError) as cm:
            ospf_interface.full_clean()
        self.assertIn('interface', cm.exception.error_dict)

    def test_interface_must_be_in_the_vrf_of_the_instance(self):
        vrf = VRF.objects.create(name='VRF 1')
        area = self.area
        in_vrf = Interface.objects.create(
            name='Interface 8', device=self.device, type='virtual', vrf=vrf
        )
        no_vrf = Interface.objects.create(
            name='Interface 7', device=self.device, type='virtual'
        )
        vrf_instance = OSPFInstance.objects.create(
            name='Instance 2',
            device=self.device,
            router_id='2.2.2.2',
            process_id=2,
            vrf=vrf,
        )
        vrf_area = OSPFArea.objects.create(instance=vrf_instance, area_id='1')
        # global instance, interface in a VRF
        with self.assertRaises(ValidationError) as cm:
            OSPFInterface(
                instance=self.instance, area=area, interface=in_vrf
            ).full_clean()
        self.assertIn('interface', cm.exception.error_dict)
        # VRF instance, interface in the global routing table
        with self.assertRaises(ValidationError) as cm:
            OSPFInterface(
                instance=vrf_instance, area=vrf_area, interface=no_vrf
            ).full_clean()
        self.assertIn('interface', cm.exception.error_dict)
        # same VRF
        OSPFInterface(
            instance=vrf_instance, area=vrf_area, interface=in_vrf
        ).full_clean()
        # both in the global routing table
        OSPFInterface(instance=self.instance, area=area, interface=no_vrf).full_clean()
