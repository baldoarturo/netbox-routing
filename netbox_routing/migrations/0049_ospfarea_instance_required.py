import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Step 3/3: require the instance and make the area ID unique per instance."""

    dependencies = [
        ('netbox_routing', '0048_ospfarea_instance_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ospfarea',
            name='instance',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='areas',
                to='netbox_routing.ospfinstance',
            ),
        ),
        migrations.AlterModelOptions(
            name='ospfarea',
            options={
                'ordering': ['instance__name', 'area_id', 'pk'],
                'verbose_name': 'OSPF Area',
            },
        ),
        migrations.AddConstraint(
            model_name='ospfarea',
            constraint=models.UniqueConstraint(
                fields=('instance', 'area_id'),
                name='netbox_routing_ospfarea_unique_instance_area_id',
                violation_error_message='The area ID must be unique within the OSPF instance.',
            ),
        ),
        migrations.AlterField(
            model_name='ospfinterface',
            name='area',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name='interfaces',
                to='netbox_routing.ospfarea',
            ),
        ),
    ]
