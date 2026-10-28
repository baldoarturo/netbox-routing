from django.core.exceptions import ValidationError
from django.test import TestCase

from utilities.testing import create_test_device

from netbox_routing_protocols.models import OSPFInstance

__all__ = ('OSPFInstanceIDTestCase',)


class OSPFInstanceIDTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def _instance(self, **kwargs):
        return OSPFInstance(
            name='Instance 1', device=self.device, router_id='1.1.1.1', **kwargs
        )

    def test_default_is_zero(self):
        instance = self._instance()
        instance.full_clean()
        instance.save()
        self.assertEqual(instance.ospf_instance_id, 0)

    def test_range(self):
        for value in (0, 127):
            with self.subTest(value=value):
                self._instance(ospf_instance_id=value).full_clean()
        for value in (-1, 128):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as cm:
                    self._instance(ospf_instance_id=value).full_clean()
                self.assertIn('ospf_instance_id', cm.exception.error_dict)
