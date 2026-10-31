from django.test import TestCase
from tenancy.models import Tenant

from netbox_routing_protocols.forms.bulk_import import BFDProfileImportForm

__all__ = ('BFDProfileBulkImportTestCase',)


class BFDProfileBulkImportTestCase(TestCase):
    """The CSV import of BFD profiles: the tenant is named, the timers are checked by the model"""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name='Tenant A', slug='tenant-a')

    def test_profile_with_tenant_named_in_the_row(self):
        form = BFDProfileImportForm(
            data={
                'name': 'Fast',
                'min_tx_int': 300,
                'min_rx_int': 300,
                'multiplier': 3,
                'tenant': self.tenant.name,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().tenant, self.tenant)

    def test_timers_are_checked_by_the_model(self):
        form = BFDProfileImportForm(
            data={'name': 'Bad', 'min_tx_int': 0, 'min_rx_int': 300, 'multiplier': 0}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('min_tx_int', form.errors)
        self.assertIn('multiplier', form.errors)

    def test_unknown_tenant_is_rejected(self):
        form = BFDProfileImportForm(
            data={
                'name': 'Fast',
                'min_tx_int': 300,
                'min_rx_int': 300,
                'multiplier': 3,
                'tenant': 'Missing',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('tenant', form.errors)
