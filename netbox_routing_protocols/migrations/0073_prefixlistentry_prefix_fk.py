import django.db.models.deletion
from django.db import migrations, models


def forward_migrate(apps, schema_editor):
    """
    Point every entry to an IPAM prefix. Entries that used a custom prefix get the IPAM
    prefix with the same value, which is created when it does not exist yet.
    """
    PrefixListEntry = apps.get_model('netbox_routing_protocols', 'PrefixListEntry')
    CustomPrefix = apps.get_model('netbox_routing_protocols', 'CustomPrefix')
    Prefix = apps.get_model('ipam', 'Prefix')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ipam_ct = ContentType.objects.filter(app_label='ipam', model='prefix').first()
    created = False
    cache = {}
    for entry in PrefixListEntry.objects.all():
        if ipam_ct is not None and entry.assigned_prefix_type_id == ipam_ct.pk:
            entry.prefix_id = entry.assigned_prefix_id
        else:
            custom = CustomPrefix.objects.get(pk=entry.assigned_prefix_id)
            if custom.prefix not in cache:
                prefix = (
                    Prefix.objects.filter(prefix=custom.prefix, vrf__isnull=True).first()
                    or Prefix.objects.filter(prefix=custom.prefix).first()
                )
                if prefix is None:
                    prefix = Prefix.objects.create(
                        prefix=custom.prefix,
                        status='active',
                        description='Created from a prefix list custom prefix',
                    )
                    created = True
                cache[custom.prefix] = prefix
            entry.prefix_id = cache[custom.prefix].pk
        entry.save(update_fields=['prefix'])

    if created:
        # The historical model does not run the signals that keep the hierarchy up to date
        print(
            '\n  Prefixes were created in IPAM from custom prefixes: run '
            '"manage.py rebuild_prefixes" to refresh the prefix hierarchy.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('ipam', '0097_merge_ipaddress_host_index_and_multi_protocol_services'),
        ('netbox_routing_protocols', '0072_prefixlistentry_sequence_range'),
    ]

    operations = [
        migrations.AddField(
            model_name='prefixlistentry',
            name='prefix',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='prefix_list_entries',
                to='ipam.prefix',
            ),
        ),
        migrations.RunPython(forward_migrate, migrations.RunPython.noop),
    ]
