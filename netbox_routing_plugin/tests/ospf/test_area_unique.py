from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from django.test import TestCase

from ipam.models import VRF
from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_plugin.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFAreaUniqueTestCase', 'OSPFAreaInstanceTestCase')


class OSPFAreaUniqueTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instances = [
            OSPFInstance.objects.create(
                name=f'Instance {i}',
                device=device,
                vrf=VRF.objects.create(name='VRF 2') if i == 2 else None,
                router_id=f'1.1.1.{i}',
            )
            for i in (1, 2)
        ]

    def test_area_id_must_be_unique_within_the_instance(self):
        OSPFArea.objects.create(
            instance=self.instances[0], area_id='0.0.0.0', area_type='backbone'
        )
        with self.assertRaises(ValidationError) as cm:
            OSPFArea(
                instance=self.instances[0], area_id='0.0.0.0', area_type='backbone'
            ).full_clean()
        self.assertIn('__all__', cm.exception.error_dict)

    def test_same_area_id_is_allowed_in_another_instance(self):
        OSPFArea.objects.create(
            instance=self.instances[0], area_id='0.0.0.0', area_type='backbone'
        )
        OSPFArea(
            instance=self.instances[1], area_id='0.0.0.0', area_type='backbone'
        ).full_clean()


class OSPFAreaInstanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instances = [
            OSPFInstance.objects.create(
                name=f'Instance {i}',
                device=cls.device,
                vrf=VRF.objects.create(name='VRF 2') if i == 2 else None,
                router_id=f'1.1.1.{i}',
            )
            for i in (1, 2)
        ]
        cls.area = OSPFArea.objects.create(instance=cls.instances[0], area_id='0')

    def test_interface_area_must_belong_to_the_instance(self):
        ospf_interface = OSPFInterface(
            instance=self.instances[1], area=self.area, interface=self.interface
        )
        with self.assertRaises(ValidationError) as cm:
            ospf_interface.full_clean()
        self.assertIn('area', cm.exception.error_dict)

    def test_interface_with_the_area_of_its_instance_is_valid(self):
        OSPFInterface(
            instance=self.instances[0], area=self.area, interface=self.interface
        ).full_clean()

    def test_area_with_interfaces_cannot_be_deleted(self):
        OSPFInterface.objects.create(
            instance=self.instances[0], area=self.area, interface=self.interface
        )
        with self.assertRaises(RestrictedError):
            self.area.delete()

    def test_instance_with_interfaces_cannot_be_deleted(self):
        OSPFInterface.objects.create(
            instance=self.instances[0], area=self.area, interface=self.interface
        )
        with self.assertRaises(RestrictedError):
            self.instances[0].delete()

    def test_deleting_an_instance_deletes_its_unused_areas(self):
        self.instances[0].delete()
        self.assertFalse(OSPFArea.objects.exists())
