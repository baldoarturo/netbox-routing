from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('OSPFInterfacePriorityMigrationTestCase',)

BEFORE = [('netbox_routing_plugin', '0052_ospfinstance_advanced_options')]
AFTER = [('netbox_routing_plugin', '0053_ospf_rfc_defaults_and_validations')]


class OSPFInterfacePriorityMigrationTestCase(TransactionTestCase):
    """An interface without a priority gets the default one."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_empty_priority_becomes_the_default(self):
        apps = self._migrate(BEFORE)
        Site = apps.get_model('dcim', 'Site')
        Manufacturer = apps.get_model('dcim', 'Manufacturer')
        DeviceType = apps.get_model('dcim', 'DeviceType')
        DeviceRole = apps.get_model('dcim', 'DeviceRole')
        Device = apps.get_model('dcim', 'Device')
        Interface = apps.get_model('dcim', 'Interface')
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
        instance = Instance.objects.create(
            name='I', device=device, router_id='1.1.1.1', process_id=1
        )
        area = Area.objects.create(instance=instance, area_id='1')
        for n, priority in enumerate((None, 0, 200)):
            interface = Interface.objects.create(
                device=device, name=f'eth{n}', type='virtual'
            )
            OSPFInterface.objects.create(
                instance=instance, area=area, interface=interface, priority=priority
            )

        apps = self._migrate(AFTER)
        OSPFInterface = apps.get_model('netbox_routing_plugin', 'OSPFInterface')
        priorities = sorted(OSPFInterface.objects.values_list('priority', flat=True))
        self.assertEqual(priorities, [0, 1, 200])

    def tearDown(self):
        # Leave the database at the latest migration for the other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()
