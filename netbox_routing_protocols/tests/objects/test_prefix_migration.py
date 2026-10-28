from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('PrefixListEntryPrefixMigrationTestCase',)

BEFORE = [('netbox_routing_protocols', '0072_prefixlistentry_sequence_range')]
AFTER = [('netbox_routing_protocols', '0074_prefixlistentry_prefix_required')]


class PrefixListEntryPrefixMigrationTestCase(TransactionTestCase):
    """Entries keep their IPAM prefix; the ones with a custom prefix are deleted."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_entries_with_custom_prefixes_are_deleted(self):
        apps = self._migrate(BEFORE)
        ContentType = apps.get_model('contenttypes', 'ContentType')
        Prefix = apps.get_model('ipam', 'Prefix')
        PrefixList = apps.get_model('netbox_routing_protocols', 'PrefixList')
        PrefixListEntry = apps.get_model('netbox_routing_protocols', 'PrefixListEntry')
        CustomPrefix = apps.get_model('netbox_routing_protocols', 'CustomPrefix')

        ipam_ct, _ = ContentType.objects.get_or_create(app_label='ipam', model='prefix')
        custom_ct, _ = ContentType.objects.get_or_create(
            app_label='netbox_routing_protocols', model='customprefix'
        )
        existing = Prefix.objects.create(prefix='10.10.0.0/24', status='active')
        prefix_list = PrefixList.objects.create(name='List', family=4)
        PrefixListEntry.objects.create(
            prefix_list=prefix_list,
            sequence=1,
            action='permit',
            assigned_prefix_type=ipam_ct,
            assigned_prefix_id=existing.pk,
        )
        # custom prefixes, one of them with the same value as an IPAM prefix
        for sequence, value in ((2, '10.10.0.0/24'), (3, '10.9.0.0/24')):
            custom = CustomPrefix.objects.create(prefix=value)
            PrefixListEntry.objects.create(
                prefix_list=prefix_list,
                sequence=sequence,
                action='deny',
                assigned_prefix_type=custom_ct,
                assigned_prefix_id=custom.pk,
            )

        apps = self._migrate(AFTER)
        Prefix = apps.get_model('ipam', 'Prefix')
        PrefixListEntry = apps.get_model('netbox_routing_protocols', 'PrefixListEntry')

        # only the entry with an IPAM prefix is left, and nothing was created in IPAM
        entries = list(PrefixListEntry.objects.all())
        self.assertEqual([e.sequence for e in entries], [1])
        self.assertEqual(entries[0].prefix_id, existing.pk)
        self.assertEqual(Prefix.objects.count(), 1)

    def tearDown(self):
        # Leave the database at the latest migration for the other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
