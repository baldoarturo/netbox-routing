from django.test import TestCase

from extras.models import CachedValue
from netbox.search.backends import search_backend
from utilities.testing import create_test_device

from netbox_routing_protocols import models

__all__ = ('OSPFSearchTestCase',)


class OSPFSearchTestCase(TestCase):

    def test_an_instance_is_found_by_its_router_id(self):
        device = create_test_device(name='Device 1')
        instance = models.OSPFInstance.objects.create(
            name='Core', device=device, router_id='7.7.7.7'
        )
        search_backend.cache([instance])
        self.assertTrue(
            CachedValue.objects.filter(object_id=instance.pk, value='7.7.7.7').exists()
        )

    def test_a_summary_address_is_found_by_its_prefix(self):
        device = create_test_device(name='Device 1')
        instance = models.OSPFInstance.objects.create(
            name='Core', device=device, router_id='7.7.7.7'
        )
        summary = models.OSPFSummaryAddress.objects.create(
            instance=instance, prefix='10.20.0.0/16'
        )
        search_backend.cache([summary])
        self.assertTrue(
            CachedValue.objects.filter(
                object_id=summary.pk, value__contains='10.20.0.0/16'
            ).exists()
        )
