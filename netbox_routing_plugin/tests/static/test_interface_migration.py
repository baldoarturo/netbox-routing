from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

__all__ = ('StaticRouteInterfaceMigrationTestCase',)

BEFORE = [('netbox_routing_plugin', '0091_staticroute_distance_and_field_types')]
AFTER = [('netbox_routing_plugin', '0093_staticroute_interface_data')]


class StaticRouteInterfaceMigrationTestCase(TransactionTestCase):
    """The interface next hop text becomes a foreign key, one route per device."""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_text_becomes_interface_and_route_is_split(self):
        apps = self._migrate(BEFORE)
        Site = apps.get_model('dcim', 'Site')
        Manufacturer = apps.get_model('dcim', 'Manufacturer')
        DeviceType = apps.get_model('dcim', 'DeviceType')
        DeviceRole = apps.get_model('dcim', 'DeviceRole')
        Device = apps.get_model('dcim', 'Device')
        Interface = apps.get_model('dcim', 'Interface')
        StaticRoute = apps.get_model('netbox_routing_plugin', 'StaticRoute')

        site = Site.objects.create(name='Site', slug='site')
        manufacturer = Manufacturer.objects.create(name='M', slug='m')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='T', slug='t'
        )
        role = DeviceRole.objects.create(name='R', slug='r')

        def device(name):
            return Device.objects.create(
                name=name, site=site, device_type=device_type, role=role
            )

        d1, d2, d3 = device('D1'), device('D2'), device('D3')
        for d in (d1, d2):
            Interface.objects.create(device=d, name='eth0', type='virtual')

        both = StaticRoute.objects.create(
            prefix='10.0.0.0/8', interface_next_hop='eth0', name='both'
        )
        both.devices.set([d1, d2])
        partial = StaticRoute.objects.create(
            prefix='10.1.0.0/16', interface_next_hop='eth0', name='partial'
        )
        partial.devices.set([d1, d3])
        missing = StaticRoute.objects.create(
            prefix='10.2.0.0/16', interface_next_hop='eth9', name='missing'
        )
        missing.devices.set([d1])
        plain = StaticRoute.objects.create(prefix='10.3.0.0/16', next_hop='10.0.0.1')
        plain.devices.set([d1])

        apps = self._migrate(AFTER)
        StaticRoute = apps.get_model('netbox_routing_plugin', 'StaticRoute')

        # Both devices have the interface: one route each
        routes = StaticRoute.objects.filter(prefix='10.0.0.0/8')
        self.assertEqual(routes.count(), 2)
        for route in routes:
            devices = list(route.devices.all())
            self.assertEqual(len(devices), 1)
            self.assertEqual(route.interface.device_id, devices[0].pk)
            self.assertEqual(route.interface.name, 'eth0')

        # D3 has no eth0: it stays on the original route, with the old text noted
        partial_routes = {
            r.interface_id is None: r
            for r in StaticRoute.objects.filter(prefix='10.1.0.0/16')
        }
        self.assertEqual([d.name for d in partial_routes[True].devices.all()], ['D3'])
        self.assertIn('eth0', partial_routes[True].comments)
        self.assertEqual([d.name for d in partial_routes[False].devices.all()], ['D1'])

        # No interface of that name anywhere: nothing lost, text kept in comments
        missing = StaticRoute.objects.get(prefix='10.2.0.0/16')
        self.assertIsNone(missing.interface)
        self.assertIn('eth9', missing.comments)

        plain = StaticRoute.objects.get(prefix='10.3.0.0/16')
        self.assertEqual(plain.next_hop_type, 'forward')

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
