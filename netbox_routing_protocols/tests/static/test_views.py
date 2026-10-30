import netaddr

from ipam.models import VRF
from utilities.testing import ViewTestCases, create_test_device

from netbox_routing_protocols.models import StaticRoute

__all__ = ('StaticRouteTestCase',)


class StaticRouteTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkImportObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = StaticRoute

    @classmethod
    def setUpTestData(cls):
        devices = [
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
        ]
        vrf = VRF.objects.create(name='Test VRF')

        nh = netaddr.IPAddress('10.10.10.1')

        routes = (
            StaticRoute(name="Route 1", vrf=vrf, prefix='0.0.0.0/0', next_hop=nh),
            StaticRoute(
                name="Route 2",
                vrf=vrf,
                prefix='1.1.1.0/24',
                next_hop=netaddr.IPAddress('10.10.10.2'),
            ),
            StaticRoute(name="Route 3", prefix='0.0.0.0/0', next_hop=nh, distance=100),
        )

        StaticRoute.objects.bulk_create(routes)

        routes[0].devices.set([devices[0]])
        routes[1].devices.set([devices[0]])
        routes[2].devices.set([devices[0]])

        cls.form_data = {
            'name': 'Route X',
            'devices': [devices[1].pk],
            'vrf': vrf.pk,
            'prefix': netaddr.IPNetwork('1.1.1.1/32'),
            'next_hop': nh,
        }

        cls.bulk_edit_data = {
            'distance': 10,
            'tag': 7,
        }

        cls.csv_data = (
            'devices,vrf,prefix,next_hop,next_hop_type,distance,tag',
            'Device 1,,10.1.0.0/16,10.10.10.9,,5,3',
            '"Device 1,Device 2",Test VRF,10.2.0.0/16,,blackhole,1,',
        )

        cls.csv_update_data = (
            'id,distance,tag',
            f'{routes[0].pk},50,1',
            f'{routes[1].pk},60,2',
        )

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:staticroute_{}'
