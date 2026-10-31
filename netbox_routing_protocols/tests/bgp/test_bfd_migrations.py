from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('BFDProfileZeroTimersMigrationTestCase',)

BEFORE = [('netbox_routing_protocols', '0111_bgp_originated_aggregates')]
AFTER = [('netbox_routing_protocols', '0112_bfdprofile_repair_zero_timers')]


class BFDProfileZeroTimersMigrationTestCase(TransactionTestCase):
    """Profiles left with timers of 0 by migration 0024 get the default timers."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_zero_timers_are_repaired_and_valid_profiles_are_kept(self):
        apps = self._migrate(BEFORE)
        BFDProfile = apps.get_model('netbox_routing_protocols', 'BFDProfile')
        broken = BFDProfile.objects.create(
            name='Broken', min_tx_int=0, min_rx_int=0, multiplier=0
        )
        valid = BFDProfile.objects.create(
            name='Valid', min_tx_int=100, min_rx_int=150, multiplier=5
        )

        apps = self._migrate(AFTER)
        BFDProfile = apps.get_model('netbox_routing_protocols', 'BFDProfile')
        self.assertEqual(
            tuple(
                BFDProfile.objects.values_list(
                    'min_tx_int', 'min_rx_int', 'multiplier'
                ).get(pk=broken.pk)
            ),
            (300, 300, 3),
        )
        self.assertEqual(
            tuple(
                BFDProfile.objects.values_list(
                    'min_tx_int', 'min_rx_int', 'multiplier'
                ).get(pk=valid.pk)
            ),
            (100, 150, 5),
        )
