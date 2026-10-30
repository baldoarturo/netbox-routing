from django.db import migrations


class Migration(migrations.Migration):
    """First half of the BGP rewrite: drop the router, scope, templates and settings
    (the data is not migrated; BGP was not production ready). The new models are
    created by the next migration."""

    dependencies = [
        ('netbox_routing_protocols', '0102_ospf_authentication_key'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ospfredistribution',
            name='netbox_routing_protocols_ospfredistribution_unique_instance_source',
        ),
        migrations.RemoveConstraint(
            model_name='isisredistribution',
            name='netbox_routing_protocols_isisredistribution_unique_instance_source',
        ),
        migrations.RemoveField(model_name='ospfredistribution', name='bgp_source'),
        migrations.RemoveField(model_name='isisredistribution', name='bgp_source'),
        migrations.DeleteModel(name='BGPPeerAddressFamily'),
        migrations.DeleteModel(name='BGPPeer'),
        migrations.DeleteModel(name='BGPAddressFamily'),
        migrations.DeleteModel(name='BGPScope'),
        migrations.DeleteModel(name='BGPSetting'),
        migrations.DeleteModel(name='BGPRouter'),
        migrations.DeleteModel(name='BGPPolicyTemplate'),
        migrations.DeleteModel(name='BGPPeerTemplate'),
        migrations.DeleteModel(name='BGPSessionTemplate'),
    ]
