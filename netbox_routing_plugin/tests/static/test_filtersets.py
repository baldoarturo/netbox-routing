import netaddr
from django.test import TestCase

from dcim.models import Device, Interface
from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_plugin.filtersets import *
from netbox_routing_plugin.models import *

__all__ = ('StaticRouteTestCase',)


class StaticRouteTestCase(TestCase):
    queryset = StaticRoute.objects.all()
    filterset = StaticRouteFilterSet

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
        routes[2].devices.set([devices[1]])

    def test_q(self):
        params = {'q': 'Route 1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_name(self):
        params = {'name': ['Route 1', 'Route 2']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_device(self):
        params = {'device': ['Device 1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_vrf(self):
        params = {'vrf': ['Test VRF']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_prefix(self):
        params = {'prefix': '0.0.0.0/0'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_next_hop(self):
        params = {'next_hop': '10.10.10.1'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_distance(self):
        params = {'distance': [1]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_q_device_name(self):
        params = {'q': 'Device 2'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_q_matching_several_devices_returns_route_once(self):
        route = StaticRoute.objects.get(name='Route 1')
        route.devices.add(*Device.objects.all())
        params = {'q': 'Device'}
        qs = self.filterset(params, self.queryset).qs
        self.assertEqual(qs.filter(pk=route.pk).count(), 1)
        self.assertEqual(qs.count(), 3)

    def test_interface_next_hop(self):
        interface = Interface.objects.create(
            device=Device.objects.get(name='Device 1'), name='Gi0/1', type='1000base-t'
        )
        StaticRoute.objects.filter(name='Route 1').update(interface=interface)
        params = {'interface': ['Gi0/1']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_route_tag(self):
        StaticRoute.objects.filter(name='Route 2').update(tag=4294967295)
        params = {'route_tag': [4294967295]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_permanent(self):
        StaticRoute.objects.filter(name='Route 3').update(permanent=True)
        self.assertEqual(
            self.filterset({'permanent': True}, self.queryset).qs.count(), 1
        )
        self.assertEqual(
            self.filterset({'permanent': False}, self.queryset).qs.count(), 2
        )

    def test_distance_range(self):
        params = {'distance__gte': [50]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_family(self):
        StaticRoute.objects.filter(name='Route 3').update(
            prefix='2001:db8::/32', next_hop='2001:db8::1'
        )
        self.assertEqual(self.filterset({'family': 6}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'family': 4}, self.queryset).qs.count(), 2)

    def test_prefix_within_and_contains(self):
        qs = self.queryset
        self.assertEqual(self.filterset({'within': '1.0.0.0/8'}, qs).qs.count(), 1)
        self.assertEqual(
            self.filterset({'within_include': '0.0.0.0/0'}, qs).qs.count(), 3
        )
        self.assertEqual(self.filterset({'within': '0.0.0.0/0'}, qs).qs.count(), 1)
        self.assertEqual(self.filterset({'contains': '1.1.1.5/32'}, qs).qs.count(), 3)
        self.assertEqual(self.filterset({'within': 'bad'}, qs).qs.count(), 0)

    def test_q_matches_interface_and_description(self):
        interface = Interface.objects.create(
            device=Device.objects.get(name='Device 1'), name='Tunnel7', type='virtual'
        )
        StaticRoute.objects.filter(name='Route 1').update(
            interface=interface, description='uplink to ISP'
        )
        self.assertEqual(self.filterset({'q': 'Tunnel7'}, self.queryset).qs.count(), 1)
        self.assertEqual(self.filterset({'q': 'uplink'}, self.queryset).qs.count(), 1)

    def test_next_hop_type_and_leaking(self):
        other = VRF.objects.create(name='Other')
        StaticRoute.objects.filter(name='Route 1').update(
            next_hop_type='blackhole', next_hop=None
        )
        StaticRoute.objects.filter(name='Route 2').update(next_hop_vrf=other)
        qs = self.queryset
        self.assertEqual(
            self.filterset({'next_hop_type': ['blackhole']}, qs).qs.count(), 1
        )
        self.assertEqual(
            self.filterset({'next_hop_vrf_id': [other.pk]}, qs).qs.count(), 1
        )
