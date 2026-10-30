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

    def test_metric_bounds(self):
        route = StaticRoute(prefix='10.0.0.0/8', interface_next_hop='Gi0/1', metric=256)
        with self.assertRaises(ValidationError):
            route.full_clean()
