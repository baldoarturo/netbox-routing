from django.db import migrations


def interface_text_to_foreign_key(apps, schema_editor):
    """
    `interface_next_hop` was free text on a route shared by several devices. The
    interface is now a foreign key, which belongs to one device, so a route with an
    interface is split into one route per device that has an interface of that name.
    Devices without such an interface stay on the original route, with the old text
    kept in its comments.
    """
    StaticRoute = apps.get_model('netbox_routing_protocols', 'StaticRoute')
    Interface = apps.get_model('dcim', 'Interface')
    fields = [f for f in StaticRoute._meta.concrete_fields if f.name != 'id']

    routes = StaticRoute.objects.exclude(interface_next_hop__isnull=True).exclude(
        interface_next_hop=''
    )
    for route in list(routes):
        text = route.interface_next_hop
        matched, unmatched = [], []
        for device in route.devices.all():
            interface = Interface.objects.filter(device_id=device.pk, name=text).first()
            (matched if interface else unmatched).append((device, interface))

        if not matched:
            route.comments = f'{route.comments}\nInterface next hop: {text}'.strip()
            route.save()
            continue

        keep = [] if unmatched else [matched.pop(0)]
        if unmatched:
            route.comments = f'{route.comments}\nInterface next hop: {text}'.strip()
            route.save()
            route.devices.set([device for device, _ in unmatched])
        for device, interface in keep:
            route.interface_id = interface.pk
            route.save()
            route.devices.set([device])
        for device, interface in matched:
            clone = StaticRoute(**{f.attname: getattr(route, f.attname) for f in fields})
            clone.interface_id = interface.pk
            clone.save()
            clone.devices.set([device])


class Migration(migrations.Migration):
    dependencies = [
        ('dcim', '0251_fix_ltree_cascade_triggers'),
        ('netbox_routing_protocols', '0092_staticroute_next_hop_type_interface_vrf'),
    ]

    operations = [
        migrations.RunPython(interface_text_to_foreign_key, migrations.RunPython.noop),
    ]
