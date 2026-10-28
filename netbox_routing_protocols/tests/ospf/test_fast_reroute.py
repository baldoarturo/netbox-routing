from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_protocols.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFFastRerouteTestCase',)


class OSPFFastRerouteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1'
        )
        cls.area = OSPFArea.objects.create(
            instance=cls.instance, area_id='1', fast_reroute=True
        )

    def _interface(self, **kwargs):
        return OSPFInterface(
            instance=self.instance, area=self.area, interface=self.interface, **kwargs
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_off_by_default(self):
        area = OSPFArea.objects.create(instance=self.instance, area_id='2')
        self.assertFalse(area.fast_reroute)
        interface = self._interface()
        interface.full_clean()
        self.assertIsNone(interface.fast_reroute)

    def test_modes(self):
        for mode in ('lfa', 'remote-lfa'):
            with self.subTest(mode=mode):
                self._interface(fast_reroute=mode).full_clean()
        self._assert_invalid(self._interface(fast_reroute='ti-lfa'), 'fast_reroute')

    def test_interface_mode_needs_the_area_switch(self):
        OSPFArea.objects.filter(pk=self.area.pk).update(fast_reroute=False)
        self.area.refresh_from_db()
        self._assert_invalid(self._interface(fast_reroute='lfa'), 'fast_reroute')

    def test_area_switch_cannot_be_disabled_while_interfaces_use_it(self):
        self._interface(fast_reroute='lfa').save()
        self.area.fast_reroute = False
        self._assert_invalid(self.area, 'fast_reroute')
