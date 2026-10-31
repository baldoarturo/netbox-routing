from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('OSPFAreaInstanceMigrationTestCase',)

BEFORE = [('netbox_routing_plugin', '0046_ospfnetwork')]
AFTER = [('netbox_routing_plugin', '0049_ospfarea_instance_required')]


class OSPFAreaInstanceMigrationTestCase(TransactionTestCase):
    """Areas used to be global; they are now split per instance."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_areas_are_assigned_copied_or_deleted(self):
        apps = self._migrate(BEFORE)
        Site = apps.get_model('dcim', 'Site')
        Manufacturer = apps.get_model('dcim', 'Manufacturer')
        DeviceType = apps.get_model('dcim', 'DeviceType')
        DeviceRole = apps.get_model('dcim', 'DeviceRole')
        Device = apps.get_model('dcim', 'Device')
        Interface = apps.get_model('dcim', 'Interface')
        VRF = apps.get_model('ipam', 'VRF')
        Instance = apps.get_model('netbox_routing_plugin', 'OSPFInstance')
        Area = apps.get_model('netbox_routing_plugin', 'OSPFArea')
        OSPFInterface = apps.get_model('netbox_routing_plugin', 'OSPFInterface')

        site = Site.objects.create(name='Site', slug='site')
        manufacturer = Manufacturer.objects.create(name='M', slug='m')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='T', slug='t'
        )
        role = DeviceRole.objects.create(name='R', slug='r')
        device = Device.objects.create(
            name='D', site=site, device_type=device_type, role=role
        )
        instances = [
            Instance.objects.create(
                name=f'I{i}',
                device=device,
                vrf=VRF.objects.create(name='VRF 2') if i == 2 else None,
                router_id=f'1.1.1.{i}',
                process_id=i,
            )
            for i in (1, 2)
        ]
        shared = Area.objects.create(area_id='0', area_type='backbone')
        single = Area.objects.create(area_id='1')
        Area.objects.create(area_id='2')  # no interface: cannot be assigned
        for n, (instance, area) in enumerate(
            ((instances[0], shared), (instances[1], shared), (instances[0], single))
        ):
            interface = Interface.objects.create(
                device=device, name=f'eth{n}', type='virtual'
            )
            OSPFInterface.objects.create(
                instance=instance, area=area, interface=interface
            )

        apps = self._migrate(AFTER)
        Area = apps.get_model('netbox_routing_plugin', 'OSPFArea')
        OSPFInterface = apps.get_model('netbox_routing_plugin', 'OSPFInterface')

        self.assertEqual(Area.objects.count(), 3)
        self.assertFalse(Area.objects.filter(area_id='2').exists())
        self.assertEqual(Area.objects.filter(area_id='0').count(), 2)
        for area in Area.objects.filter(area_id='0'):
            self.assertEqual(area.area_type, 'backbone')
        for ospf_interface in OSPFInterface.objects.all():
            self.assertEqual(
                ospf_interface.area.instance_id, ospf_interface.instance_id
            )

    def tearDown(self):
        # Leave the database at the latest migration for the other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()
