from django.test import TestCase

from dcim.models import Device, Interface
from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing_plugin.forms import *
from netbox_routing_plugin.models import *

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.vrf = VRF.objects.create(name='Test VRF')
        cls.device = create_test_device(name='Device 1')

    def test_instance(self):
        form = OSPFInstanceForm(
            data={
                'name': 'Instance 1',
                'router_id': '10.10.10.1',
                'device': Device.objects.first().pk,
            }
        )
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_advanced_options_left_out_take_their_default(self):
        form = OSPFInstanceForm(
            data={
                'name': 'Instance 3',
                'router_id': '30.30.30.1',
                'device': self.device.pk,
                'graceful_restart': 'planned',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.graceful_restart, 'planned')
        self.assertEqual(instance.spf_initial_delay, 50)
        self.assertEqual(instance.graceful_restart_period, 120)
        self.assertEqual(instance.max_lsa_threshold, 75)

    def test_checkboxes_start_with_their_default(self):
        # A checkbox that is not sent means unchecked, so the form has to show
        # the default (RFC 2328: RFC 1583 compatibility is enabled).
        form = OSPFInstanceForm()
        self.assertIs(form.fields['rfc1583_compatibility'].initial, True)
        self.assertIs(form.fields['graceful_restart_helper'].initial, True)
        self.assertIs(form.fields['max_metric_router_lsa'].initial, False)

    def test_instance_with_vrf(self):
        form = OSPFInstanceForm(
            data={
                'name': 'Instance 2',
                'router_id': '20.20.20.1',
                'device': Device.objects.first().pk,
                'vrf': VRF.objects.first().pk,
            }
        )
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class OSPFAreaTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', router_id='10.10.10.1', device_id=device.pk
        )

    def test_valid_area_id_with_ip(self):
        form = OSPFAreaForm(
            data={
                'instance': self.instance.pk,
                'area_id': '0.0.0.0',
                'area_type': 'standard',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_valid_area_id_with_integer(self):
        form = OSPFAreaForm(
            data={
                'instance': self.instance.pk,
                'area_id': '0',
                'area_type': 'standard',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_area_zero_defaults_to_the_backbone_type(self):
        for area_id in ('0', '0.0.0.0'):
            with self.subTest(area_id=area_id):
                form = OSPFAreaForm(
                    data={
                        'instance': self.instance.pk,
                        'area_id': area_id,
                        'area_type': 'standard',
                    }
                )
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.save().area_type, 'backbone')
                OSPFArea.objects.all().delete()

    def test_area_zero_cannot_be_a_stub(self):
        form = OSPFAreaForm(
            data={'instance': self.instance.pk, 'area_id': '0', 'area_type': 'stub'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('area_type', form.errors)

    def test_invalid_area(self):
        form = OSPFAreaForm(
            data={
                'instance': self.instance.pk,
                'area_id': 'a.a.a.a',
                'area_type': 'standard',
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class OSPFInterfaceTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', router_id='10.10.10.1', device_id=device.pk
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='0.0.0.0')

    def test_interface_with_correct_device(self):
        form = OSPFInterfaceForm(
            data={
                'device': Device.objects.first().pk,
                'interface': Interface.objects.first().pk,
                'instance': OSPFInstance.objects.first().pk,
                'area': OSPFArea.objects.first().pk,
                'network_type': 'broadcast',
                'passive': True,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_priority_left_out_takes_its_default(self):
        form = OSPFInterfaceForm(
            data={
                'device': Device.objects.first().pk,
                'interface': Interface.objects.first().pk,
                'instance': OSPFInstance.objects.first().pk,
                'area': OSPFArea.objects.first().pk,
                'network_type': 'broadcast',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().priority, 1)

    def test_interface_with_incorrect_device(self):
        device = create_test_device(name='Device 2')
        interface = Interface.objects.create(
            name='Interface 1', device=device, type='virtual'
        )

        form = OSPFInterfaceForm(
            data={
                'device': device.pk,
                'interface': interface.pk,
                'instance': OSPFInstance.objects.first().pk,
                'area': OSPFArea.objects.first().pk,
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()
