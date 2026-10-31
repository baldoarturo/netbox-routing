from django.db import migrations

# Used for the profiles that migration 0024 left with timers of 0 (#535).
REPAIR_VALUES = {'min_tx_int': 300, 'min_rx_int': 300, 'multiplier': 3}


def repair_zero_timers(apps, schema_editor):
    BFDProfile = apps.get_model('netbox_routing_plugin', 'BFDProfile')
    for field, value in REPAIR_VALUES.items():
        BFDProfile.objects.filter(**{field: 0}).update(**{field: value})


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_routing_plugin', '0111_bgp_originated_aggregates'),
    ]

    operations = [
        migrations.RunPython(code=repair_zero_timers, reverse_code=migrations.RunPython.noop),
    ]
