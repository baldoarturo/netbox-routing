from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_protocols.choices import OSPFNetworkTypeChoices
from netbox_routing_protocols.models import *

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

    def test_advanced_options_default_to_the_rfc_values(self):
        instance = self._instance('10.0.0.1')
        instance.full_clean()
        self.assertEqual(
            (
                instance.spf_initial_delay,
                instance.spf_short_delay,
                instance.spf_long_delay,
                instance.spf_time_to_learn,
                instance.spf_holddown,
            ),
            (50, 200, 5000, 500, 10000),
        )
        self.assertEqual(
            (instance.lsa_min_interval, instance.lsa_min_arrival), (5000, 1000)
        )
        self.assertEqual(instance.graceful_restart, 'disabled')
        self.assertEqual(instance.graceful_restart_period, 120)
        self.assertTrue(instance.graceful_restart_helper_strict_lsa_checking)
        self.assertTrue(instance.rfc1583_compatibility)
        self.assertEqual(instance.exit_overflow_interval, 0)
        self.assertIsNone(instance.external_lsdb_limit)
        self.assertFalse(instance.max_metric_router_lsa)

    def _assert_invalid(self, field, **values):
        instance = self._instance('10.0.0.1')
        for name, value in values.items():
            setattr(instance, name, value)
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_spf_delays_must_be_ordered(self):
        self._assert_invalid('spf_short_delay', spf_initial_delay=300)
        self._assert_invalid('spf_long_delay', spf_long_delay=100)
        self._assert_invalid('spf_holddown', spf_holddown=500)
        instance = self._instance('10.0.0.1')
        instance.spf_initial_delay = instance.spf_short_delay = 200
        instance.full_clean()

    def test_bandwidth_paths_and_distances_are_optional(self):
        instance = self._instance('10.0.0.1')
        instance.full_clean()
        for name in (
            'reference_bandwidth',
            'maximum_paths',
            'distance_intra_area',
            'distance_inter_area',
            'distance_external',
        ):
            self.assertIsNone(getattr(instance, name))

    def test_bandwidth_paths_and_distances_limits(self):
        limits = {
            'reference_bandwidth': (1, 4294967),
            'maximum_paths': (1, 64),
            'distance_intra_area': (1, 255),
            'distance_inter_area': (1, 255),
            'distance_external': (1, 255),
        }
        for name, (low, high) in limits.items():
            with self.subTest(name=name):
                for value in (low, high):
                    instance = self._instance('10.0.0.1')
                    setattr(instance, name, value)
                    instance.full_clean()
                invalid = (0, high + 1) if name != 'reference_bandwidth' else (0,)
                for value in invalid:
                    self._assert_invalid(name, **{name: value})

    def test_graceful_restart_period_limits(self):
        instance = self._instance('10.0.0.1')
        for period in (1, 1800):
            instance.graceful_restart_period = period
            instance.full_clean()
        for period in (0, 1801):
            self._assert_invalid(
                'graceful_restart_period', graceful_restart_period=period
            )

    def test_max_lsa_threshold_limits(self):
        for threshold in (0, 101):
            self._assert_invalid('max_lsa_threshold', max_lsa_threshold=threshold)

    def test_dependent_options_need_their_parent(self):
        self._assert_invalid('max_metric_on_startup', max_metric_on_startup=60)
        self._assert_invalid(
            'log_adjacency_changes_detail', log_adjacency_changes_detail=True
        )
        self._assert_invalid('max_lsa_warning_only', max_lsa_warning_only=True)
        self._assert_invalid('exit_overflow_interval', exit_overflow_interval=30)

        instance = self._instance('10.0.0.1')
        instance.max_metric_router_lsa = True
        instance.max_metric_on_startup = 60
        instance.log_adjacency_changes = True
        instance.log_adjacency_changes_detail = True
        instance.max_lsa = 1000
        instance.max_lsa_warning_only = True
        instance.external_lsdb_limit = 500
        instance.exit_overflow_interval = 30
        instance.full_clean()

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

    def test_area_zero_must_be_the_backbone(self):
        for area_id in ('0', '0.0.0.0'):
            with self.subTest(area_id=area_id):
                OSPFArea(
                    instance=self.instance, area_id=area_id, area_type='backbone'
                ).full_clean()
                for area_type in ('standard', 'stub', 'tsa', 'nssa', 'tnssa'):
                    with self.assertRaises(ValidationError) as cm:
                        OSPFArea(
                            instance=self.instance, area_id=area_id, area_type=area_type
                        ).full_clean()
                    self.assertIn('area_type', cm.exception.error_dict)

    def test_only_area_zero_can_be_the_backbone(self):
        with self.assertRaises(ValidationError) as cm:
            self._area('backbone').full_clean()
        self.assertIn('area_id', cm.exception.error_dict)

    def test_area_id_limits(self):
        for area_id in ('1', '4294967295', '255.255.255.255', '0.0.0.1'):
            with self.subTest(area_id=area_id):
                OSPFArea(instance=self.instance, area_id=area_id).full_clean()
        for area_id in ('-1', '4294967296', 'a.a.a.a', '1.2.3.256'):
            with self.subTest(area_id=area_id):
                with self.assertRaises(ValidationError) as cm:
                    OSPFArea(instance=self.instance, area_id=area_id).full_clean()
                self.assertIn('area_id', cm.exception.error_dict)

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

    def test_priority_defaults_to_one_and_is_limited_to_8_bits(self):
        ospf_interface = OSPFInterface.objects.get()
        self.assertEqual(ospf_interface.priority, 1)
        for priority in (0, 255):
            ospf_interface.priority = priority
            ospf_interface.full_clean()
        for priority in (-1, 256):
            ospf_interface.priority = priority
            with self.assertRaises(ValidationError) as cm:
                ospf_interface.full_clean()
            self.assertIn('priority', cm.exception.error_dict)

    def test_misc_flags_are_optional(self):
        ospf_interface = OSPFInterface.objects.get()
        for flag in (
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
        ):
            with self.subTest(flag=flag):
                self.assertIsNone(getattr(ospf_interface, flag))
                for value in (True, False, None):
                    setattr(ospf_interface, flag, value)
                    ospf_interface.full_clean()

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
