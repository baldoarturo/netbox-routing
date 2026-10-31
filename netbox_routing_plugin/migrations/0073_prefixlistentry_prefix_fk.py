import django.db.models.deletion
from django.db import migrations, models


def forward_migrate(apps, schema_editor):
    """
    Point every entry to its IPAM prefix. Custom prefixes no longer exist and nothing is
    created in IPAM for them: the entries that used one are deleted.
    """
    PrefixListEntry = apps.get_model('netbox_routing_plugin', 'PrefixListEntry')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ipam_ct = ContentType.objects.filter(app_label='ipam', model='prefix').first()
    removed = 0
    for entry in PrefixListEntry.objects.all():
        if ipam_ct is not None and entry.assigned_prefix_type_id == ipam_ct.pk:
            entry.prefix_id = entry.assigned_prefix_id
            entry.save(update_fields=['prefix'])
        else:
            entry.delete()
            removed += 1

    if removed:
        print(
            f'\n  Deleted {removed} prefix list entries that used a custom prefix: '
            'prefixes must be declared in IPAM.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('ipam', '0097_merge_ipaddress_host_index_and_multi_protocol_services'),
        ('netbox_routing_plugin', '0072_prefixlistentry_sequence_range'),
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
