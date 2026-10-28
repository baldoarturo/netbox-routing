from django.test import TestCase

from extras.models import CachedValue
from netbox.registry import registry
from netbox.search.backends import search_backend
from utilities.testing import create_test_device

from netbox_routing_protocols import models
from netbox_routing_protocols.search import ospf as search

OSPF_MODELS = (
    models.OSPFInstance,
    models.OSPFArea,
    models.OSPFInterface,
    models.OSPFNetwork,
    models.OSPFRedistribution,
    models.OSPFVirtualLink,
    models.OSPFSummaryAddress,
    models.OSPFNeighbor,
    models.OSPFAreaRange,
    models.OSPFPrefixSID,
)

__all__ = ('OSPFSearchTestCase',)


class OSPFSearchTestCase(TestCase):
    def test_every_ospf_model_is_indexed(self):
        for model in OSPF_MODELS:
            with self.subTest(model=model.__name__):
                self.assertIn(model._meta.label_lower, registry['search'])

    def test_every_index_is_listed_in_the_module(self):
        names = {f'{model.__name__}Index' for model in OSPF_MODELS}
        self.assertEqual(names, set(search.__all__))

    def test_the_indexed_fields_exist(self):
        for model in OSPF_MODELS:
            index = registry['search'][model._meta.label_lower]
            for field, _weight in index.fields:
                with self.subTest(model=model.__name__, field=field):
                    model._meta.get_field(field)

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
