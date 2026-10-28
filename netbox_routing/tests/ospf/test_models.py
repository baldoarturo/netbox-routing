from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing.choices import OSPFNetworkTypeChoices
from netbox_routing.models import *

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def _instance(self, router_id):
        return OSPFInstance(
            name='Instance 1', device=self.device, router_id=router_id, process_id=1
        )

    def test_default_originate_defaults(self):
        instance = self._instance('10.0.0.1')
        instance.full_clean()
        self.assertFalse(instance.default_originate)
        self.assertFalse(instance.default_originate_always)
        self.assertIsNone(instance.default_originate_metric)
        self.assertEqual(instance.default_originate_metric_type, '2')

    def test_default_originate_options(self):
        instance = self._instance('10.0.0.1')
        instance.default_originate = True
        instance.default_originate_always = True
        for metric in (0, 16777214):
            instance.default_originate_metric = metric
            instance.full_clean()
        for metric in (-1, 16777215):
            instance.default_originate_metric = metric
            with self.assertRaises(ValidationError) as cm:
                instance.full_clean()
            self.assertIn('default_originate_metric', cm.exception.error_dict)

    def test_default_originate_options_require_default_originate(self):
        instance = self._instance('10.0.0.1')
        instance.default_originate_always = True
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn('default_originate', cm.exception.error_dict)

        instance.default_originate_always = False
        instance.default_originate_metric = 10
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn('default_originate', cm.exception.error_dict)

    def test_router_id_ipv4_is_valid(self):
        self._instance('10.0.0.1').full_clean()

    def test_router_id_ipv6_is_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            self._instance('2001:db8::1').full_clean()
        self.assertIn('router_id', cm.exception.error_dict)

    def test_router_id_zero_is_rejected(self):
        with self.assertRaises(ValidationError) as cm:
            self._instance('0.0.0.0').full_clean()
        self.assertIn('router_id', cm.exception.error_dict)

    def test_router_id_with_mask_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._instance('10.0.0.1/24').full_clean()


class OSPFAreaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=device, router_id='1.1.1.1', process_id=1
        )

    def _area(self, area_type, **kwargs):
        return OSPFArea(
            instance=self.instance, area_id='1', area_type=area_type, **kwargs
        )

    def test_options_default_to_off(self):
        area = self._area('standard')
        area.full_clean()
        self.assertIsNone(area.default_cost)
        self.assertFalse(area.nssa_translate_always)
        self.assertFalse(area.nssa_no_redistribution)
        self.assertFalse(area.nssa_default_originate)

    def test_default_cost_only_for_stub_and_nssa_areas(self):
        for area_type in ('stub', 'tsa', 'nssa', 'tnssa'):
            with self.subTest(area_type=area_type):
                self._area(area_type, default_cost=10).full_clean()
        for area_type in ('standard', 'backbone'):
            with self.subTest(area_type=area_type):
                with self.assertRaises(ValidationError) as cm:
                    self._area(area_type, default_cost=10).full_clean()
                self.assertIn('default_cost', cm.exception.error_dict)

    def test_default_cost_limits(self):
        self._area('stub', default_cost=0).full_clean()
        self._area('stub', default_cost=16777215).full_clean()
        with self.assertRaises(ValidationError) as cm:
            self._area('stub', default_cost=16777216).full_clean()
        self.assertIn('default_cost', cm.exception.error_dict)

    def test_nssa_options_only_for_nssa_areas(self):
        for field in (
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
        ):
            for area_type in ('nssa', 'tnssa'):
                with self.subTest(field=field, area_type=area_type):
                    self._area(area_type, **{field: True}).full_clean()
            for area_type in ('standard', 'backbone', 'stub', 'tsa'):
                with self.subTest(field=field, area_type=area_type):
                    with self.assertRaises(ValidationError) as cm:
                        self._area(area_type, **{field: True}).full_clean()
                    self.assertIn(field, cm.exception.error_dict)


class OSPFInterfaceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1',
            device=cls.device,
            router_id='1.1.1.1',
            process_id=1,
        )
        area = OSPFArea.objects.create(instance=cls.instance, area_id='0.0.0.0')
        OSPFInterface.objects.create(
            instance=cls.instance, area=area, interface=interface
        )

    def test_network_type_defaults_to_broadcast(self):
        self.assertEqual(
            OSPFInterface.objects.get().network_type, OSPFNetworkTypeChoices.BROADCAST
        )

    def test_cost_limits(self):
        ospf_interface = OSPFInterface.objects.get()
        for cost in (1, 65535, None):
            ospf_interface.cost = cost
            ospf_interface.full_clean()
        for cost in (0, 65536):
            ospf_interface.cost = cost
            with self.assertRaises(ValidationError) as cm:
                ospf_interface.full_clean()
            self.assertIn('cost', cm.exception.error_dict)

    def test_mtu_ignore_defaults_to_false(self):
        self.assertFalse(OSPFInterface.objects.get().mtu_ignore)

    def test_timers_default_to_rfc_2328_values(self):
        ospf_interface = OSPFInterface.objects.get()
        self.assertEqual(ospf_interface.hello_interval, 10)
        self.assertEqual(ospf_interface.dead_interval, 40)
        self.assertEqual(ospf_interface.retransmit_interval, 5)
        self.assertEqual(ospf_interface.transmit_delay, 1)

    def test_timer_limits(self):
        # dead_interval must also exceed hello_interval, so its lowest valid
        # value is 2 while hello_interval is at its minimum of 1.
        limits = {
            'hello_interval': (1, 65535),
            'dead_interval': (2, 4294967295),
            'retransmit_interval': (1, 65535),
            'transmit_delay': (1, 65535),
        }
        for name, (low, high) in limits.items():
            with self.subTest(name=name):
                for value in (low, high):
                    ospf_interface = OSPFInterface.objects.get()
                    ospf_interface.hello_interval = 1
                    ospf_interface.dead_interval = 4294967295
                    setattr(ospf_interface, name, value)
                    if name == 'dead_interval':
                        ospf_interface.hello_interval = 1
                    ospf_interface.full_clean()
                for value in (
                    1 if name == 'dead_interval' else low - 1,
                    high + 1,
                ):
                    ospf_interface = OSPFInterface.objects.get()
                    setattr(ospf_interface, name, value)
                    if name == 'dead_interval' and value == 1:
                        ospf_interface.hello_interval = 1
                    with self.assertRaises(ValidationError) as cm:
                        ospf_interface.full_clean()
                    self.assertTrue(
                        {name, 'dead_interval'} & set(cm.exception.error_dict)
                    )

    def test_dead_interval_must_exceed_hello_interval(self):
        ospf_interface = OSPFInterface.objects.get()
        ospf_interface.hello_interval = 30
        ospf_interface.dead_interval = 30
        with self.assertRaises(ValidationError) as cm:
            ospf_interface.full_clean()
        self.assertIn('dead_interval', cm.exception.error_dict)

    def test_delete_device_with_ospf_interfaces(self):
        self.device.delete()
        self.assertFalse(OSPFInstance.objects.exists())
        self.assertFalse(OSPFInterface.objects.exists())

    def test_delete_instance_with_interfaces_is_blocked(self):
        with self.assertRaises(RestrictedError):
            self.instance.delete()
