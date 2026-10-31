import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dcim', '0251_fix_ltree_cascade_triggers'),
        ('ipam', '0097_merge_ipaddress_host_index_and_multi_protocol_services'),
        ('netbox_routing_plugin', '0091_staticroute_distance_and_field_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='staticroute',
            name='interface',
            field=models.ForeignKey(
                blank=True,
                help_text='Outgoing interface, for routes without an IP address as next hop. The route is then carried by the device of the interface only',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='static_routes',
                to='dcim.interface',
                verbose_name='Interface Next Hop',
            ),
        ),
        migrations.AddField(
            model_name='staticroute',
            name='next_hop_type',
            field=models.CharField(
                blank=True,
                default='forward',
                help_text='Forward through an address and/or interface, or one of the special next hops of RFC 8349 (blackhole, unreachable, prohibit, receive)',
                max_length=20,
                verbose_name='Next Hop Type',
            ),
        ),
        migrations.AddField(
            model_name='staticroute',
            name='next_hop_vrf',
            field=models.ForeignKey(
                blank=True,
                help_text='Route leaking: the VRF in which the next hop is resolved, when it is not the VRF of the route',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='staticroutes_next_hop',
                to='ipam.vrf',
                verbose_name='Next Hop VRF',
            ),
        ),
        migrations.AddField(
            model_name='staticroute',
            name='next_hop_global',
            field=models.BooleanField(
                default=False,
                help_text='Route leaking: resolve the next hop in the global routing table',
                verbose_name='Next Hop in the Global Table',
            ),
        ),
    ]
