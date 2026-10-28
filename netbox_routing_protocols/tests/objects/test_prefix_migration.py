from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('PrefixListEntryPrefixMigrationTestCase',)

BEFORE = [('netbox_routing_protocols', '0072_prefixlistentry_sequence_range')]
AFTER = [('netbox_routing_protocols', '0074_prefixlistentry_prefix_required')]


class PrefixListEntryPrefixMigrationTestCase(TransactionTestCase):
    """Entries that used a custom prefix end up pointing to an IPAM prefix."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_custom_prefixes_become_ipam_prefixes(self):
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
        # an entry that already used an IPAM prefix
        PrefixListEntry.objects.create(
            prefix_list=prefix_list,
            sequence=1,
            action='permit',
            assigned_prefix_type=ipam_ct,
            assigned_prefix_id=existing.pk,
        )
        # a custom prefix that is already declared in IPAM, and one that is not
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

        entries = {e.sequence: e for e in PrefixListEntry.objects.all()}
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[1].prefix_id, existing.pk)
        # reuses the IPAM prefix that already exists
        self.assertEqual(entries[2].prefix_id, existing.pk)
        self.assertEqual(Prefix.objects.filter(prefix='10.10.0.0/24').count(), 1)
        # declares the one that did not exist
        self.assertEqual(str(entries[3].prefix.prefix), '10.9.0.0/24')
        self.assertEqual(Prefix.objects.filter(prefix='10.9.0.0/24').count(), 1)

    def tearDown(self):
        # Leave the database at the latest migration for the other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
