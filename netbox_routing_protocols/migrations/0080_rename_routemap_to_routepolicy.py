import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):
    """Route map is the Cisco name: the plugin calls it Route policy (#322)"""

    dependencies = [
        ('netbox_routing_protocols', '0079_prefixlist_references_set_null'),
    ]

    operations = [
        migrations.RemoveConstraint('routemap', 'netbox_routing_protocols_routemap_unique_name'),
        migrations.RemoveConstraint('routemapentry', 'netbox_routing_protocols_routemapentry_unique_routemap_sequence'),
        migrations.RenameModel('RouteMap', 'RoutePolicy'),
        migrations.RenameModel('RouteMapEntry', 'RoutePolicyEntry'),
        migrations.RenameField('routepolicyentry', 'route_map', 'route_policy'),
        migrations.RenameField('bgppolicytemplate', 'routemap_in', 'routepolicy_in'),
        migrations.RenameField('bgppolicytemplate', 'routemap_out', 'routepolicy_out'),
        migrations.RenameField('bgppeeraddressfamily', 'routemap_in', 'routepolicy_in'),
        migrations.RenameField('bgppeeraddressfamily', 'routemap_out', 'routepolicy_out'),
        migrations.AlterModelOptions(
            name='routepolicyentry',
            options={'ordering': ['route_policy', 'sequence']},
        ),
        migrations.AlterField(
            model_name='routepolicyentry',
            name='match_aspath',
            field=models.ManyToManyField(blank=True, related_name='route_policy_entries', to='netbox_routing_protocols.aspath'),
        ),
        migrations.AlterField(
            model_name='routepolicyentry',
            name='match_community',
            field=models.ManyToManyField(blank=True, related_name='route_policy_entries', to='netbox_routing_protocols.community'),
        ),
        migrations.AlterField(
            model_name='routepolicyentry',
            name='match_community_list',
            field=models.ManyToManyField(blank=True, related_name='route_policy_entries', to='netbox_routing_protocols.communitylist'),
        ),
        migrations.AlterField(
            model_name='routepolicyentry',
            name='match_prefix_list',
            field=models.ManyToManyField(blank=True, related_name='route_policy_entries', to='netbox_routing_protocols.prefixlist'),
        ),
        migrations.AlterField(
            model_name='routepolicyentry',
            name='route_policy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_policy_entries', to='netbox_routing_protocols.routepolicy'),
        ),
        migrations.AddConstraint(
            model_name='routepolicy',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('name'), name='netbox_routing_protocols_routepolicy_unique_name', violation_error_message='Name must be unique.'),
        ),
        migrations.AddConstraint(
            model_name='routepolicyentry',
            constraint=models.UniqueConstraint(fields=('route_policy', 'sequence'), name='netbox_routing_protocols_routepolicyentry_unique_routepolicy_sequence', violation_error_message='Route Policy sequence must be unique.'),
        ),
    ]
