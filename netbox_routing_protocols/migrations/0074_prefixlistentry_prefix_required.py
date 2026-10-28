import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipam', '0097_merge_ipaddress_host_index_and_multi_protocol_services'),
        ('netbox_routing_protocols', '0073_prefixlistentry_prefix_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prefixlistentry',
            name='prefix',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='prefix_list_entries',
                to='ipam.prefix',
            ),
        ),
        migrations.RemoveField(model_name='prefixlistentry', name='assigned_prefix_type'),
        migrations.RemoveField(model_name='prefixlistentry', name='assigned_prefix_id'),
        migrations.DeleteModel(name='CustomPrefix'),
    ]
