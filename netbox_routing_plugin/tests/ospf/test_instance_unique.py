from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_plugin.models import OSPFInstance

__all__ = ('OSPFInstanceUniqueTestCase',)


class OSPFInstanceUniqueTestCase(TestCase):
    """One instance per device and VRF; no VRF is the default VRF."""

    @classmethod
    def setUpTestData(cls):
        cls.devices = [create_test_device(name=f'Device {i}') for i in (1, 2)]
        cls.vrfs = [VRF.objects.create(name=f'VRF {i}') for i in (1, 2)]

    def _instance(self, name, device=None, vrf=None, router_id='1.1.1.1'):
        return OSPFInstance(
            name=name, device=device or self.devices[0], vrf=vrf, router_id=router_id
        )

    def test_only_one_instance_in_the_default_vrf(self):
        self._instance('A').save()
        other = self._instance('B', router_id='2.2.2.2')
        with self.assertRaises(ValidationError) as cm:
            other.full_clean()
        self.assertIn('__all__', cm.exception.error_dict)
        with self.assertRaises(IntegrityError), transaction.atomic():
            other.save()

    def test_only_one_instance_per_vrf(self):
        self._instance('A', vrf=self.vrfs[0]).save()
        with self.assertRaises(ValidationError):
            self._instance('B', vrf=self.vrfs[0], router_id='2.2.2.2').full_clean()

    def test_the_name_does_not_matter(self):
        self._instance('A').save()
        with self.assertRaises(ValidationError):
            self._instance('Other name', router_id='2.2.2.2').full_clean()

    def test_different_vrfs_and_devices_are_independent(self):
        self._instance('A').save()
        self._instance('B', vrf=self.vrfs[0], router_id='2.2.2.2').save()
        self._instance('C', vrf=self.vrfs[1], router_id='3.3.3.3').save()
        self._instance('A', device=self.devices[1], router_id='4.4.4.4').full_clean()
