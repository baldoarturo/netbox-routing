from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Device, Interface
from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_protocols.models import StaticRoute

__all__ = ('StaticRouteTestCase',)


def make_interface(device_name, name):
    device = Device.objects.filter(name=device_name).first() or create_test_device(
        name=device_name
    )
    return Interface.objects.create(device=device, name=name, type='1000base-t')


class StaticRouteTestCase(TestCase):
    def test_next_hop_required(self):
        route = StaticRoute(prefix='10.0.0.0/8')
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('next_hop', cm.exception.message_dict)

    def test_interface_next_hop_is_enough(self):
        interface = make_interface('Device 1', 'Gi0/1')
        StaticRoute(prefix='10.0.0.0/8', interface=interface).full_clean()

    def test_distance_bounds(self):
        route = StaticRoute(
            prefix='10.0.0.0/8', next_hop_type='blackhole', distance=256
        )
        with self.assertRaises(ValidationError):
            route.full_clean()

    def test_distance_zero_is_invalid(self):
        route = StaticRoute(prefix='10.0.0.0/8', next_hop_type='blackhole', distance=0)
        with self.assertRaises(ValidationError) as cm:
            route.full_clean()
        self.assertIn('distance', cm.exception.message_dict)

    def test_tag_range(self):
        route = StaticRoute(prefix='10.0.0.0/8', next_hop_type='blackhole')
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
        self.assertIn('interface', cm.exception.message_dict)
        route.interface = make_interface('Device 1', 'Gi0/1')
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

    def test_special_next_hop_has_no_next_hop(self):
        for kind in ('blackhole', 'unreachable', 'prohibit', 'receive'):
            StaticRoute(prefix='10.0.0.0/8', next_hop_type=kind).full_clean()
            with self.assertRaises(ValidationError, msg=kind) as cm:
                StaticRoute(
                    prefix='10.0.0.0/8', next_hop_type=kind, next_hop='10.0.0.1'
                ).full_clean()
            self.assertIn('next_hop', cm.exception.message_dict)

    def test_str_of_special_route(self):
        self.assertEqual(
            str(StaticRoute(prefix='10.0.0.0/8', next_hop_type='blackhole')),
            '10.0.0.0/8 blackhole',
        )

    def test_route_leaking(self):
        vrf, other = VRF.objects.create(name='A'), VRF.objects.create(name='B')
        base = {'prefix': '10.0.0.0/8', 'next_hop': '10.1.1.1', 'vrf': vrf}
        StaticRoute(next_hop_vrf=other, **base).full_clean()
        StaticRoute(next_hop_global=True, **base).full_clean()
        for extra, field in (
            ({'next_hop_vrf': vrf}, 'next_hop_vrf'),
            ({'next_hop_vrf': other, 'next_hop_global': True}, 'next_hop_global'),
        ):
            with self.assertRaises(ValidationError) as cm:
                StaticRoute(**{**base, **extra}).full_clean()
            self.assertIn(field, cm.exception.message_dict)
        # global route cannot leak into the global table; leaking needs an address
        with self.assertRaises(ValidationError):
            StaticRoute(
                prefix='10.0.0.0/8', next_hop='10.1.1.1', next_hop_global=True
            ).full_clean()
        with self.assertRaises(ValidationError) as cm:
            StaticRoute(
                prefix='10.0.0.0/8',
                interface=make_interface('Device 1', 'Gi0/1'),
                next_hop_vrf=other,
            ).full_clean()
        self.assertIn('next_hop', cm.exception.message_dict)

    def test_interface_restricts_devices(self):
        interface = make_interface('Device 1', 'Gi0/1')
        other = create_test_device(name='Device 2')
        route = StaticRoute(prefix='10.0.0.0/8', interface=interface)
        route.validate_devices([interface.device])
        with self.assertRaises(ValidationError):
            route.validate_devices([interface.device, other])
        with self.assertRaises(ValidationError):
            route.validate_devices([other])
