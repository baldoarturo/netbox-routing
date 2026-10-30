from django.core.exceptions import ValidationError
from django.test import TestCase

from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_protocols.models import StaticRoute

__all__ = ('StaticRouteTestCase',)


class StaticRouteTestCase(TestCase):
    def test_next_hop_required(self):
        route = StaticRoute(prefix='10.0.0.0/8')
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('next_hop', cm.exception.message_dict)

    def test_interface_next_hop_is_enough(self):
        StaticRoute(prefix='10.0.0.0/8', interface_next_hop='Gi0/1').full_clean()

    def test_distance_bounds(self):
        route = StaticRoute(
            prefix='10.0.0.0/8', interface_next_hop='Gi0/1', distance=256
        )
        with self.assertRaises(ValidationError):
            route.full_clean()

    def test_distance_zero_is_invalid(self):
        route = StaticRoute(prefix='10.0.0.0/8', interface_next_hop='Gi0/1', distance=0)
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('distance', cm.exception.message_dict)

    def test_tag_range(self):
        route = StaticRoute(prefix='10.0.0.0/8', interface_next_hop='Gi0/1')
        route.tag = 4294967295
        route.full_clean()
        route.tag = 4294967296
        with self.assertRaises(ValidationError):
            route.full_clean()
        route.tag = -1
        with self.assertRaises(ValidationError):
            route.full_clean()

    def test_defaults(self):
        route = StaticRoute.objects.create(prefix='10.0.0.0/8', next_hop='10.0.0.1')
        route.refresh_from_db()
        self.assertEqual(route.name, '')
        self.assertIs(route.permanent, False)
        self.assertEqual(route.distance, 1)

    def test_prefix_host_bits(self):
        route = StaticRoute(prefix='10.0.0.1/24', next_hop='10.0.0.254')
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('prefix', cm.exception.message_dict)
        StaticRoute(prefix='10.0.0.1/32', next_hop='10.0.0.254').full_clean()

    def test_next_hop_family_must_match(self):
        for prefix, nh in (
            ('10.0.0.0/8', '2001:db8::1'),
            ('2001:db8::/32', '10.0.0.1'),
        ):
            with self.assertRaises(ValidationError) as cm:
                StaticRoute(prefix=prefix, next_hop=nh).full_clean()
            self.assertIn('next_hop', cm.exception.message_dict)

    def test_unusable_next_hop(self):
        for nh in ('0.0.0.0', '127.0.0.1', '224.0.0.5'):
            with self.assertRaises(ValidationError, msg=nh) as cm:
                StaticRoute(prefix='10.0.0.0/8', next_hop=nh).full_clean()
            self.assertIn('next_hop', cm.exception.message_dict)

    def test_ipv6_link_local_needs_interface(self):
        route = StaticRoute(prefix='2001:db8::/32', next_hop='fe80::1')
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('interface_next_hop', cm.exception.message_dict)
        route.interface_next_hop = 'Gi0/1'
        route.full_clean()

    def test_duplicate_on_same_device_and_vrf(self):
        device = create_test_device(name='Device 1')
        other = create_test_device(name='Device 2')
        vrf = VRF.objects.create(name='VRF 1')
        route = StaticRoute.objects.create(
            prefix='10.0.0.0/8', next_hop='10.1.1.1', vrf=vrf
        )
        route.devices.set([device])

        same = StaticRoute(prefix='10.0.0.0/8', next_hop='10.1.1.1', vrf=vrf)
        with self.assertRaises(ValidationError):
            same.validate_devices([device])
        same.validate_devices([other])  # another device
        StaticRoute(prefix='10.0.0.0/8', next_hop='10.1.1.1').validate_devices(
            [device]
        )  # another VRF
        StaticRoute(prefix='10.0.0.0/8', next_hop='10.1.1.2', vrf=vrf).validate_devices(
            [device]
        )  # another next hop
        route.validate_devices([device])  # a route is not its own duplicate
