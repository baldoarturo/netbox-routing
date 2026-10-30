import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_routing_protocols', '0100_ospf_authentication_trailer_instance_id'),
    ]

    operations = [
        # The name was free text: it is not carried over, the policy is chosen again
        migrations.RemoveField(
            model_name='ospfredistribution',
            name='route_policy',
        ),
        migrations.AddField(
            model_name='ospfredistribution',
            name='route_policy',
            field=models.ForeignKey(
                blank=True,
                help_text='Route policy applied to the redistributed routes',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ospf_redistributions',
                to='netbox_routing_protocols.routepolicy',
                verbose_name='Route Policy',
            ),
        ),
    ]
