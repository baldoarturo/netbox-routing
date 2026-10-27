from django.core.exceptions import ValidationError
from django.test import TestCase

from netbox_routing.models import *

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(TestCase):
    pass


class OSPFAreaTestCase(TestCase):
    def test_area_id_must_be_unique(self):
        OSPFArea.objects.create(area_id='0.0.0.0')
        with self.assertRaises(ValidationError):
            OSPFArea(area_id='0.0.0.0').full_clean()


class OSPFInterfaceTestCase(TestCase):
    pass
