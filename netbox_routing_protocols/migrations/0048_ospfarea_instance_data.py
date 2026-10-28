from django.db import migrations


def assign_areas_to_instances(apps, schema_editor):
    """
    Areas used to be global. Give each area to the first instance that uses it
    and copy it for every other instance (tags are not copied). Areas used by
    no interface cannot be assigned to an instance and are deleted.
    """
    OSPFArea = apps.get_model('netbox_routing_protocols', 'OSPFArea')
    OSPFInterface = apps.get_model('netbox_routing_protocols', 'OSPFInterface')
    fields = [f for f in OSPFArea._meta.concrete_fields if not f.primary_key]

    for area in OSPFArea.objects.order_by('pk'):
        instance_ids = list(
            OSPFInterface.objects.filter(area=area)
            .order_by('instance_id')
            .values_list('instance_id', flat=True)
            .distinct()
        )
        if not instance_ids:
            area.delete()
            continue
        area.instance_id = instance_ids[0]
        area.save(update_fields=['instance'])
        for instance_id in instance_ids[1:]:
            copy = OSPFArea(**{f.attname: getattr(area, f.attname) for f in fields})
            copy.instance_id = instance_id
            copy.save()
            OSPFInterface.objects.filter(area=area, instance_id=instance_id).update(
                area=copy
            )


class Migration(migrations.Migration):
    """Step 2/3: data."""

    dependencies = [
        ('netbox_routing_protocols', '0047_ospfarea_instance'),
    ]

    operations = [
        migrations.RunPython(assign_areas_to_instances, migrations.RunPython.noop),
    ]
