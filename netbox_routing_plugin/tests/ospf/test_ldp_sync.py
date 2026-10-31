from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_plugin.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFLDPSyncTestCase',)


class OSPFLDPSyncTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1'
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_off_by_default(self):
        self.assertFalse(self.instance.ldp_sync)
        self.assertIsNone(self.instance.ldp_sync_holddown)
        interface = OSPFInterface(
            instance=self.instance, area=self.area, interface=self.interface
        )
        interface.full_clean()
        self.assertIsNone(interface.ldp_sync)

    def test_holddown_needs_ldp_sync(self):
        self.instance.ldp_sync_holddown = 60
        self._assert_invalid(self.instance, 'ldp_sync_holddown')
        self.instance.ldp_sync = True
        self.instance.full_clean()

    def test_holddown_range(self):
        self.instance.ldp_sync = True
        for value in (0, 65536):
            with self.subTest(value=value):
                self.instance.ldp_sync_holddown = value
                self._assert_invalid(self.instance, 'ldp_sync_holddown')
        for value in (1, 65535):
            self.instance.ldp_sync_holddown = value
            self.instance.full_clean()

    def test_interface_can_override_in_both_directions(self):
        for value in (True, False):
            OSPFInterface(
                instance=self.instance,
                area=self.area,
                interface=self.interface,
                ldp_sync=value,
            ).full_clean()
