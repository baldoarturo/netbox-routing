from django.http import QueryDict
from django.test import TestCase
from tenancy.models import Tenant

from netbox_routing_plugin.filtersets import BFDProfileFilterSet
from netbox_routing_plugin.models import BFDProfile

__all__ = ('BFDProfileFilterSetTestCase',)


class BFDProfileFilterSetTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name='Tenant A', slug='tenant-a')
        BFDProfile.objects.create(
            name='Fast', min_tx_int=300, min_rx_int=300, multiplier=3, tenant=cls.tenant
        )
        BFDProfile.objects.create(
            name='Slow', min_tx_int=1000, min_rx_int=1500, multiplier=5, hold=120
        )

    def _names(self, query):
        filterset = BFDProfileFilterSet(QueryDict(query), BFDProfile.objects.all())
        return sorted(filterset.qs.values_list('name', flat=True))

    def test_filter_by_tenant(self):
        self.assertEqual(self._names(f'tenant_id={self.tenant.pk}'), ['Fast'])

    def test_filter_by_timers(self):
        self.assertEqual(self._names('min_tx_int=1000'), ['Slow'])
        self.assertEqual(
            self._names('min_rx_int=300&min_rx_int=1500'), ['Fast', 'Slow']
        )
        self.assertEqual(self._names('multiplier=3'), ['Fast'])
        self.assertEqual(self._names('hold=120'), ['Slow'])
