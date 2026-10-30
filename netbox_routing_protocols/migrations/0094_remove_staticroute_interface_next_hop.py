from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_routing_protocols', '0093_staticroute_interface_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staticroute',
            name='interface_next_hop',
        ),
    ]
