from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF, IPAddress
from utilities.exceptions import AbortRequest
from utilities.testing import create_test_device

from netbox_routing_plugin.choices import (
    OSPFAreaTypeChoices,
    OSPFRangeTypeChoices,
)
from netbox_routing_plugin.models import (
    OSPFArea,
    OSPFAreaRange,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFVirtualLink,
)

__all__ = ('OSPFIntegrityTestCase',)


class OSPFIntegrityTestCase(TestCase):
    """The rules hold when a parent changes, and the names tell objects apart."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1'
        )
        cls.area0 = OSPFArea.objects.create(
            instance=cls.instance, area_id='0', area_type=OSPFAreaTypeChoices.BACKBONE
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_area_type_keeps_the_virtual_links_valid(self):
        OSPFVirtualLink.objects.create(
            instance=self.instance, transit_area=self.area, remote_router_id='2.2.2.2'
        )
        self.area.area_type = OSPFAreaTypeChoices.STUB
        self._assert_invalid(self.area, 'area_type')

    def test_area_type_keeps_the_nssa_ranges_valid(self):
        nssa = OSPFArea.objects.create(
            instance=self.instance, area_id='2', area_type=OSPFAreaTypeChoices.NSSA
        )
        OSPFAreaRange.objects.create(
            area=nssa,
            prefix='10.0.0.0/8',
            range_type=OSPFRangeTypeChoices.NSSA_EXTERNAL,
        )
        nssa.area_type = OSPFAreaTypeChoices.STANDARD
        self._assert_invalid(nssa, 'area_type')

    def test_router_id_is_not_the_remote_of_a_virtual_link(self):
        OSPFVirtualLink.objects.create(
            instance=self.instance, transit_area=self.area, remote_router_id='2.2.2.2'
        )
        self.instance.router_id = '2.2.2.2'
        self._assert_invalid(self.instance, 'router_id')

    def test_interface_cannot_change_vrf_under_an_ospf_interface(self):
        OSPFInterface.objects.create(
            instance=self.instance, area=self.area, interface=self.interface
        )
        self.interface.vrf = VRF.objects.create(name='VRF 1')
        with self.assertRaises(AbortRequest):
            self.interface.save()

    def test_address_cannot_move_under_an_ospf_network(self):
        ospf_interface = OSPFInterface.objects.create(
            instance=self.instance, area=self.area, interface=self.interface
        )
        address = IPAddress.objects.create(
            address='10.0.0.1/30', assigned_object=self.interface
        )
        OSPFNetwork.objects.create(ospf_interface=ospf_interface, ip_address=address)
        other = Interface.objects.create(
            name='Interface 2', device=self.device, type='virtual'
        )
        address.assigned_object = other
        with self.assertRaises(AbortRequest):
            address.save()

    def test_names_tell_the_objects_apart(self):
        ospf_interface = OSPFInterface.objects.create(
            instance=self.instance, area=self.area, interface=self.interface
        )
        self.assertEqual(str(ospf_interface), 'Device 1 Interface 1')
        self.assertEqual(str(self.area), '1 (Instance 1)')
