from django.core.exceptions import ValidationError
from django.test import TestCase

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
