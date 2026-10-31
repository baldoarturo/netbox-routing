from django.db import migrations, models
from django.db.models import Q

from netbox_routing_plugin.helpers.community import WELL_KNOWN


def name_well_known(apps, schema_editor):
    """The well-known communities without a name take the name the RFC gives them"""
    Community = apps.get_model('netbox_routing_plugin', 'Community')
    for name, (value, _rfc) in WELL_KNOWN.items():
        Community.objects.filter(community=value, name='').update(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_routing_plugin', '0083_community_integrity'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='community',
            name='netbox_routing_plugin_community_community',
        ),
        migrations.AddConstraint(
            model_name='community',
            constraint=models.UniqueConstraint(
                fields=('tenant', 'community'),
                name='netbox_routing_plugin_community_unique_tenant_community',
                violation_error_message='This tenant already has this community.',
            ),
        ),
        migrations.AddConstraint(
            model_name='community',
            constraint=models.UniqueConstraint(
                fields=('community',),
                condition=Q(tenant__isnull=True),
                name='netbox_routing_plugin_community_unique_community_no_tenant',
                violation_error_message=(
                    'A community with this value and no tenant already exists.'
                ),
            ),
        ),
        migrations.AlterModelOptions(
            name='community',
            options={
                'ordering': ['community', 'pk'],
                'verbose_name': 'Community',
                'verbose_name_plural': 'Communities',
            },
        ),
        migrations.RunPython(name_well_known, migrations.RunPython.noop),
    ]
