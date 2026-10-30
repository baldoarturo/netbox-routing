from django.test import TestCase

from dcim.models import Device
from utilities.testing import create_test_device

from netbox_routing_protocols.forms import *
from netbox_routing_protocols.forms.bulk_edit import StaticRouteBulkEditForm
from netbox_routing_protocols.forms.bulk_import import StaticRouteImportForm

__all__ = ('StaticRouteTestCase',)


class StaticRouteTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def test_staticroute(self):
        form = StaticRouteForm(
            data={
                'name': 'Route 1',
                'devices': [Device.objects.first().pk],
                'vrf': None,
                'prefix': '0.0.0.0/0',
                'next_hop': '10.10.10.1',
                'distance': 1,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_import_assigns_devices(self):
        create_test_device(name='Device 2')
        form = StaticRouteImportForm(
            data={
                'devices': 'Device 1,Device 2',
                'prefix': '10.0.0.0/8',
                'next_hop': '10.10.10.1',
                'interface_next_hop': 'Gi0/1',
                'tag': 5,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        route = form.save()
        self.assertEqual(route.devices.count(), 2)
        self.assertEqual(route.interface_next_hop, 'Gi0/1')
        self.assertEqual(route.tag, 5)

    def test_bulk_edit_form_fields(self):
        form = StaticRouteBulkEditForm()
        for field in ('name', 'interface_next_hop', 'tag', 'distance'):
            self.assertIn(field, form.fields)
        for _, names in [(fs.name, fs.items) for fs in form.fieldsets]:
            for name in names:
                self.assertIn(name, form.fields)

    def test_bulk_edit_distance_bounds(self):
        form = StaticRouteBulkEditForm(data={'distance': 300})
        self.assertFalse(form.is_valid())
        self.assertIn('distance', form.errors)

    def test_duplicate_route_on_device_is_refused(self):
        data = {
            'devices': [self.device.pk],
            'prefix': '10.0.0.0/8',
            'next_hop': '10.10.10.1',
        }
        form = StaticRouteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        form = StaticRouteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('devices', form.errors)

    def test_host_bits_are_refused(self):
        form = StaticRouteForm(
            data={
                'devices': [self.device.pk],
                'prefix': '10.0.0.1/24',
                'next_hop': '10.10.10.1',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)
