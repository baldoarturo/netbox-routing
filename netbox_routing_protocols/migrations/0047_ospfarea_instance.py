import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Step 1/3: drop the global unique area_id and add a nullable instance."""

    dependencies = [
        ('netbox_routing_protocols', '0046_ospfnetwork'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='ospfarea',
            name='netbox_routing_protocols_ospfarea_unique_area_id',
        ),
        migrations.AddField(
            model_name='ospfarea',
            name='instance',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='areas',
                to='netbox_routing_protocols.ospfinstance',
            ),
        ),
    ]
