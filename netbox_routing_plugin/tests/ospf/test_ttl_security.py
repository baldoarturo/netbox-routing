from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_plugin.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFVirtualLink,
)

__all__ = ('OSPFTTLSecurityTestCase',)


class OSPFTTLSecurityTestCase(TestCase):
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
        cls.transit = OSPFArea.objects.create(instance=cls.instance, area_id='2')

    def _objects(self, **kwargs):
        return (
            OSPFInterface(
                instance=self.instance,
                area=self.area,
                interface=self.interface,
                **kwargs,
            ),
            OSPFVirtualLink(
                instance=self.instance,
                transit_area=self.transit,
                remote_router_id='2.2.2.2',
                **kwargs,
            ),
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_off_by_default(self):
        for obj in self._objects():
            with self.subTest(obj=type(obj).__name__):
                obj.full_clean()
                self.assertFalse(obj.ttl_security)
                self.assertIsNone(obj.ttl_security_hops)

    def test_hops_are_required_when_enabled(self):
        for obj in self._objects(ttl_security=True):
            with self.subTest(obj=type(obj).__name__):
                self._assert_invalid(obj, 'ttl_security_hops')
                obj.ttl_security_hops = 1
                obj.full_clean()

    def test_hops_need_ttl_security(self):
        for obj in self._objects(ttl_security_hops=2):
            with self.subTest(obj=type(obj).__name__):
                self._assert_invalid(obj, 'ttl_security_hops')

    def test_hops_range(self):
        for obj in self._objects(ttl_security=True):
            for hops in (0, 255):
                with self.subTest(obj=type(obj).__name__, hops=hops):
                    obj.ttl_security_hops = hops
                    self._assert_invalid(obj, 'ttl_security_hops')
            obj.ttl_security_hops = 254
            obj.full_clean()
