# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from dcim.models import Interface
from ipam.models import VRF
from utilities.exceptions import AbortRequest
from utilities.testing import create_test_device

from netbox_routing_plugin.helpers.isis import net_error
from netbox_routing_plugin.models import (
    OSPFInstance,
    ISISFlexAlgo,
    ISISInstance,
    ISISInterface,
    ISISInterfaceLevel,
    ISISLevel,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISAddressFamily,
    ISISSRMappingEntry,
    ISISAdjacencySID,
    ISISAreaAddress,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
    ISISSegmentRouting,
    ISISSetting,
)

__all__ = (
    'ISISInstanceModelTestCase',
    'ISISInterfaceModelTestCase',
    'ISISSettingModelTestCase',
    'ISISFlexAlgoModelTestCase',
    'ISISPrefixSIDModelTestCase',
    'ISISSegmentRoutingCleanTestCase',
    'ISISSRv6LocatorModelTestCase',
    'ISISMigrationStateTestCase',
    'ISISConsistencyTestCase',
    'ISISRoutingModelsTestCase',
    'ISISAreaAddressTestCase',
    'ISISAuthenticationTestCase',
    'ISISSegmentRoutingExtrasTestCase',
    'ISISAddressFamilyTestCase',
    'ISISNetTestCase',
    'ISISRangeTestCase',
    'ISISSegmentRoutingRulesTestCase',
    'ISISLongTailSettingTestCase',
    'ISISInterfaceOptionsTestCase',
)


class ISISInstanceModelTestCase(TestCase):
    """Model-level (clean()) coverage for ISISInstance auth pairing."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def _instance(self, **kwargs):
        kwargs.setdefault('net', '49.0001.0000.0000.0001.00')
        return ISISInstance(
            device=self.device,
            process_tag='CORE',
            is_type='level-1-2',
            **kwargs,
        )

    def test_clean_accepts_complete_auth_pair(self):
        self._instance(area_auth_type='md5', area_auth_key='secret').clean()

    def test_hmac_sha_auth_types_accepted(self):
        # Modern deployments authenticate with HMAC-SHA rather than md5/text
        # (IOS-XR hmac-sha-256, Junos/Nokia key-chain algorithms). full_clean
        # exercises both choice membership and the column length ('hmac-sha-256'
        # is 12 chars — longer than the original max_length=10).
        self._instance(
            area_auth_type='hmac-sha-256', area_auth_key='secret'
        ).full_clean()
        self._instance(
            domain_auth_type='hmac-sha-1', domain_auth_key='secret'
        ).full_clean()

    def test_fast_reroute_and_microloop_accepted(self):
        # Process-wide IP-FRR flavour (LFA / Remote-LFA / TI-LFA — IOS-XR
        # fast-reroute per-prefix [ti-lfa], Junos backup-spf-options, Nokia
        # loopfree-alternate) and micro-loop
        # avoidance, TI-LFA's usual companion knob.
        for flavour in ('lfa', 'remote-lfa', 'ti-lfa'):
            self._instance(fast_reroute=flavour).full_clean()
        self._instance(microloop_avoidance=True).full_clean()

    def test_clean_accepts_no_auth(self):
        self._instance().clean()

    def test_clean_rejects_type_without_key(self):
        with self.assertRaises(ValidationError) as ctx:
            self._instance(area_auth_type='md5').clean()
        self.assertIn('area_auth_key', ctx.exception.error_dict)

    def test_clean_rejects_key_without_type(self):
        with self.assertRaises(ValidationError) as ctx:
            self._instance(domain_auth_key='secret').clean()
        self.assertIn('domain_auth_type', ctx.exception.error_dict)

    def test_clean_accepts_valid_net(self):
        self._instance(net='49.0001.1921.6800.1001.00').clean()  # should not raise

    def test_clean_accepts_blank_net(self):
        # net is optional (blank=True, default=''); an empty NET must pass.
        self._instance(net='').clean()

    def test_clean_rejects_malformed_net(self):
        # A NET has a fixed hex-grouped syntax; a malformed value must be rejected at
        # the model layer (form + API + import all run full_clean) rather than only
        # failing downstream when the adapter pushes it to the device.
        for bad in ('49.0001.bogus', 'not-a-net', '49.0001', '0000.0000.0001'):
            with self.subTest(net=bad):
                with self.assertRaises(ValidationError) as ctx:
                    self._instance(net=bad).clean()
                self.assertIn('net', ctx.exception.error_dict)

    def test_unique_device_process_tag(self):
        # A device can't hold two IS-IS instances with the same process tag
        # (including two untagged '' defaults) — they'd be indistinguishable.
        ISISInstance.objects.create(device=self.device, process_tag='CORE')
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISInstance.objects.create(device=self.device, process_tag='CORE')

    def test_unique_default_process_tag(self):
        ISISInstance.objects.create(device=self.device, process_tag='')
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISInstance.objects.create(device=self.device, process_tag='')

    def test_same_process_tag_other_device_allowed(self):
        other = create_test_device(name='Device 2')
        ISISInstance.objects.create(device=self.device, process_tag='CORE')
        ISISInstance.objects.create(device=other, process_tag='CORE')  # no raise


class ISISInterfaceModelTestCase(TestCase):
    """Model-level (clean()) coverage for ISISInterface.

    Exercises the same-device enforcement at the ORM layer, which the
    form-layer tests in test_forms.py do not cover.
    """

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.other_device = create_test_device(name='Device 2')
        cls.instance = ISISInstance.objects.create(
            device=cls.device,
            process_tag='CORE',
            net='49.0001.0000.0000.0001.00',
            is_type='level-1-2',
        )

    def test_clean_accepts_matching_device(self):
        interface = Interface.objects.create(
            name='Interface 1', device=self.device, type='virtual'
        )
        isis_interface = ISISInterface(
            instance=self.instance,
            interface=interface,
            address_family='ipv4',
        )
        isis_interface.clean()  # should not raise

    def test_clean_rejects_device_mismatch(self):
        interface = Interface.objects.create(
            name='Interface 1', device=self.other_device, type='virtual'
        )
        isis_interface = ISISInterface(
            instance=self.instance,
            interface=interface,
            address_family='ipv4',
        )
        with self.assertRaises(ValidationError) as ctx:
            isis_interface.clean()
        self.assertIn('interface', ctx.exception.error_dict)

    def _iface(self, **kwargs):
        interface = Interface.objects.create(
            name=f'Interface {kwargs.pop("n", 1)}', device=self.device, type='virtual'
        )
        return ISISInterface(
            instance=self.instance, interface=interface, address_family='ipv4', **kwargs
        )

    def test_clean_accepts_complete_hello_auth_pair(self):
        self._iface(n=10, hello_auth_type='md5', hello_auth_key='secret').clean()

    def test_hello_auth_hmac_sha_accepted(self):
        self._iface(
            n=14, hello_auth_type='hmac-sha-256', hello_auth_key='secret'
        ).full_clean()

    def test_frr_fields_accepted(self):
        # Per-interface fast-reroute: protection coverage (link/node — Junos
        # link-protection/node-link-protection, IOS-XR per-prefix protection)
        # and the tri-state enable, whose False is the EXPLICIT exclude form
        # (Nokia loopfree-alternate-exclude, IOS-XR fast-reroute exclude).
        self._iface(n=15, frr_enabled=True, frr_protection='node').full_clean()
        self._iface(n=16, frr_enabled=False).full_clean()
        self._iface(n=17, frr_protection='link').full_clean()

    def test_clean_accepts_no_hello_auth(self):
        self._iface(n=11).clean()

    def test_clean_rejects_hello_type_without_key(self):
        with self.assertRaises(ValidationError) as ctx:
            self._iface(n=12, hello_auth_type='md5').clean()
        self.assertIn('hello_auth_key', ctx.exception.error_dict)

    def test_clean_rejects_hello_key_without_type(self):
        with self.assertRaises(ValidationError) as ctx:
            self._iface(n=13, hello_auth_key='secret').clean()
        self.assertIn('hello_auth_type', ctx.exception.error_dict)

    def test_clone_omits_hello_auth_secret(self):
        # Cloning serializes clone_fields into the add-form URL query string, so
        # the plaintext hello auth key must never be a clone field. Its paired
        # type is excluded too (mirrors ISISInstance/ISISLevel, which keep their
        # auth secrets out of clone_fields), otherwise a type-without-key prefill
        # would trip the paired-auth validation on every clone.
        iface = self._iface(n=18, hello_auth_type='md5', hello_auth_key='secret')
        iface.save()
        attrs = iface.clone()
        self.assertNotIn('hello_auth_key', attrs)
        self.assertNotIn('hello_auth_type', attrs)

    def test_optional_charfields_default_to_empty_string(self):
        # circuit_type / network_type are blank=True, default='' (not nullable),
        # so an unset value round-trips as '' rather than NULL.
        iface = self._iface(n=20)
        iface.save()
        iface.refresh_from_db()
        self.assertEqual(iface.circuit_type, '')
        self.assertEqual(iface.network_type, '')

    def test_unique_interface_address_family(self):
        # One IS-IS interface per (interface, address_family).
        iface = self._iface(n=21)
        iface.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISInterface.objects.create(
                instance=self.instance,
                interface=iface.interface,
                address_family=iface.address_family,
            )


class ISISSettingModelTestCase(TestCase):
    """An ISISSetting must be attached to an assigned object.

    The form enforces this (ISISSettingForm.clean); these tests cover the model
    layer (used by the API/bulk-import paths) and the DB CheckConstraint, so an
    orphan row cannot be persisted through any path.
    """

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )

    def test_clean_accepts_assigned_setting(self):
        ISISSetting(
            assigned_object=self.instance, key='graceful_restart', value='true'
        ).clean()  # should not raise

    def test_clean_rejects_orphan_setting(self):
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(key='graceful_restart', value='true').clean()
        self.assertIn('assigned to an object', str(ctx.exception))

    def test_clean_rejects_nonexistent_object(self):
        # A dangling assigned_object_id (valid type, no such row) is rejected by
        # NetBox's base NetBoxModel.clean() GFK-existence check, surfaced as a
        # field error. (The end-to-end API rejection is asserted in
        # ISISSettingAssignmentAPITestCase.)
        ct = ContentType.objects.get_for_model(ISISInstance)
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(
                assigned_object_type=ct,
                assigned_object_id=self.instance.pk + 9999,
                key='graceful_restart',
                value='true',
            ).clean()
        self.assertIn('assigned_object_id', ctx.exception.message_dict)

    def test_db_constraint_rejects_orphan_setting(self):
        # The CheckConstraint is the backstop for any path that bypasses
        # clean() (e.g. a raw create / bulk_create).
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISSetting.objects.create(key='graceful_restart', value='true')

    def test_clean_rejects_non_isis_assignment_type(self):
        # limit_choices_to only constrains the form picker; the model layer must
        # reject a non-IS-IS assigned type so the API/bulk-import paths cannot
        # attach a setting to (e.g.) a Device. The device exists, so the GFK
        # existence check passes and the type check is what fires.
        device_ct = ContentType.objects.get_for_model(self.instance.device)
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(
                assigned_object_type=device_ct,
                assigned_object_id=self.instance.device.pk,
                key='graceful_restart',
                value='true',
            ).clean()
        self.assertIn('assigned_object_type', ctx.exception.message_dict)

    def test_clean_rejects_non_integer_value_for_integer_key(self):
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(
                assigned_object=self.instance,
                key='spf_second_wait',
                value='not-a-number',
            ).clean()
        self.assertIn('value', ctx.exception.message_dict)

    def test_clean_accepts_integer_value_for_integer_key(self):
        ISISSetting(
            assigned_object=self.instance, key='spf_second_wait', value='250'
        ).clean()  # should not raise

    def test_clean_rejects_negative_integer_value_for_integer_key(self):
        # The form path enforces min_value=0; the model clean() is the backstop for the
        # API / import / direct-write paths, so it must reject negatives too.
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(
                assigned_object=self.instance, key='spf_second_wait', value='-1'
            ).clean()
        self.assertIn('value', ctx.exception.message_dict)

    def test_te_router_id_keys_accepted(self):
        # The IS-IS traffic-engineering router-ID knob (IOS/XR 'mpls traffic-eng
        # router-id'; derived from the global
        # router-id on Junos/Nokia). Without vocabulary keys a reader-emitted
        # setting is silently filtered downstream and the value never lands.
        # full_clean exercises key choice membership; values are strings (an IP
        # or, on Cisco, an interface reference).
        for key, value in (
            ('te_ipv4_router_id', '192.0.2.1'),
            ('te_ipv6_router_id', '2001:db8::1'),
        ):
            ISISSetting(
                assigned_object=self.instance, key=key, value=value
            ).full_clean()

    def test_clean_rejects_non_boolean_value_for_boolean_key(self):
        with self.assertRaises(ValidationError) as ctx:
            ISISSetting(
                assigned_object=self.instance, key='graceful_restart', value='maybe'
            ).clean()
        self.assertIn('value', ctx.exception.message_dict)


class ISISFlexAlgoModelTestCase(TestCase):
    """algo_id is constrained to the IS-IS Flex-Algo range 128-255.

    The model validators (MinValueValidator/MaxValueValidator) cover the
    form/API/import paths via full_clean(); a DB CheckConstraint is the backstop
    for direct writes (objects.create / bulk_create) that bypass full_clean(), so
    an out-of-range algo_id cannot be persisted through any path.
    """

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )

    def test_db_constraint_rejects_out_of_range_algo_id(self):
        for bad in (0, 127, 256):
            with (
                self.subTest(algo_id=bad),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                ISISFlexAlgo.objects.create(instance=self.instance, algo_id=bad)

    def test_db_constraint_accepts_boundary_algo_ids(self):
        # The 128 and 255 boundaries are valid and must round-trip.
        ISISFlexAlgo.objects.create(instance=self.instance, algo_id=128)
        ISISFlexAlgo.objects.create(instance=self.instance, algo_id=255)
        self.assertEqual(self.instance.flex_algos.count(), 2)


class ISISPrefixSIDModelTestCase(TestCase):
    """Per-prefix prefix-SID: index and absolute label are mutually exclusive
    (clean()), and the algorithm is 0 or the Flex-Algo range 128-255 (DB CheckConstraint
    is the backstop for direct writes that bypass full_clean())."""

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )
        for algo_id in (128, 255):
            ISISFlexAlgo.objects.create(instance=instance, algo_id=algo_id)
        loopback = Interface.objects.create(
            name='Loopback0', device=device, type='virtual'
        )
        cls.isis_interface = ISISInterface.objects.create(
            instance=instance, interface=loopback, address_family='ipv4', passive=True
        )

    def test_clean_rejects_index_and_label_together(self):
        sid = ISISPrefixSID(
            interface=self.isis_interface, algorithm=0, sid_index=10, sid_label=16010
        )
        with self.assertRaises(ValidationError):
            sid.clean()

    def test_clean_accepts_index_only(self):
        ISISPrefixSID(interface=self.isis_interface, algorithm=0, sid_index=10).clean()

    def test_clean_accepts_label_only(self):
        ISISPrefixSID(
            interface=self.isis_interface, algorithm=128, sid_label=16010
        ).clean()

    def test_clean_rejects_out_of_range_algorithm(self):
        # clean() must reject the 1-127 gap (and >255) with a ValidationError
        # (HTTP 400) rather than deferring to the DB CheckConstraint, which would
        # surface as an IntegrityError (HTTP 500).
        for bad in (1, 127, 256):
            with self.subTest(algorithm=bad), self.assertRaises(ValidationError) as ctx:
                ISISPrefixSID(
                    interface=self.isis_interface, algorithm=bad, sid_index=1
                ).clean()
            self.assertIn('algorithm', ctx.exception.error_dict)

    def test_clean_accepts_valid_algorithm(self):
        for algo in (0, 128, 255):
            ISISPrefixSID(
                interface=self.isis_interface, algorithm=algo, sid_index=1
            ).clean()  # should not raise

    def test_db_constraint_rejects_out_of_range_algorithm(self):
        for bad in (1, 127, 256):
            with (
                self.subTest(algorithm=bad),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                ISISPrefixSID.objects.create(
                    interface=self.isis_interface, algorithm=bad, sid_index=1
                )

    def test_db_constraint_accepts_valid_algorithms(self):
        # 0 (SPF) and the 128/255 Flex-Algo boundaries must all round-trip.
        for algo in (0, 128, 255):
            ISISPrefixSID.objects.create(
                interface=self.isis_interface, algorithm=algo, sid_index=algo + 1
            )
        self.assertEqual(self.isis_interface.prefix_sids.count(), 3)

    def test_unique_interface_algorithm(self):
        ISISPrefixSID.objects.create(
            interface=self.isis_interface, algorithm=0, sid_index=1
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISPrefixSID.objects.create(
                interface=self.isis_interface, algorithm=0, sid_index=2
            )


class ISISSegmentRoutingCleanTestCase(TestCase):
    """SRGB and SRLB are each a (start, range) pair — a lone bound is rejected."""

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )

    def _sr(self, **kwargs):
        return ISISSegmentRouting(instance=self.instance, **kwargs)

    def test_clean_rejects_srgb_start_without_range(self):
        with self.assertRaises(ValidationError):
            self._sr(srgb_start=16000).clean()

    def test_clean_rejects_srgb_range_without_start(self):
        with self.assertRaises(ValidationError):
            self._sr(srgb_range=8000).clean()

    def test_clean_rejects_srlb_start_without_range(self):
        with self.assertRaises(ValidationError):
            self._sr(srlb_start=15000).clean()

    def test_clean_accepts_complete_blocks(self):
        self._sr(
            srgb_start=16000, srgb_range=8000, srlb_start=15000, srlb_range=1000
        ).clean()

    def test_clean_accepts_no_blocks(self):
        self._sr(enabled=True, srv6_enabled=True).clean()


class ISISSRv6LocatorModelTestCase(TestCase):
    """SRv6 locator: RFC 8986 SID structure (block+node+function+argument) must fit
    128 bits when pinned; (instance, name) is unique; the prefix round-trips."""

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )
        for algo_id in (128, 255):
            ISISFlexAlgo.objects.create(instance=cls.instance, algo_id=algo_id)

    def test_clean_rejects_oversized_sid_structure(self):
        # 40 + 24 + 48 + 32 = 144 > 128
        loc = ISISSRv6Locator(
            instance=self.instance,
            name='LOC1',
            prefix='2001:db8:0:a2::/64',
            block_length=40,
            node_length=24,
            function_length=48,
            argument_length=32,
        )
        with self.assertRaises(ValidationError):
            loc.clean()

    def test_clean_accepts_within_128(self):
        # 40 + 24 + 16 = 80
        ISISSRv6Locator(
            instance=self.instance,
            name='LOC1',
            prefix='2001:db8:0:a2::/64',
            block_length=40,
            node_length=24,
            function_length=16,
        ).clean()

    def test_clean_accepts_derived_lengths(self):
        # All lengths null → the device derives them; only the prefix is required.
        ISISSRv6Locator(
            instance=self.instance, name='LOC1', prefix='2001:db8:0:a2::/64'
        ).clean()

    def test_unique_instance_name(self):
        ISISSRv6Locator.objects.create(
            instance=self.instance, name='LOC1', prefix='2001:db8:0:a2::/64'
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISSRv6Locator.objects.create(
                instance=self.instance, name='LOC1', prefix='2001:db8:0:a3::/64'
            )

    def test_prefix_roundtrips(self):
        loc = ISISSRv6Locator.objects.create(
            instance=self.instance, name='LOC2', prefix='2001:db8:0:a2::/64'
        )
        loc.refresh_from_db()
        self.assertEqual(str(loc.prefix), '2001:db8:0:a2::/64')

    def test_clean_rejects_out_of_range_algorithm(self):
        # algorithm is 0 (SPF) or a Flex-Algo in 128-255; the 1-127 gap and >255
        # must be rejected at clean() (mirrors ISISPrefixSID).
        for bad in (1, 127, 256):
            with self.subTest(algorithm=bad), self.assertRaises(ValidationError) as ctx:
                ISISSRv6Locator(
                    instance=self.instance,
                    name='LOC-ALG',
                    prefix='2001:db8:0:a2::/64',
                    algorithm=bad,
                ).clean()
            self.assertIn('algorithm', ctx.exception.error_dict)

    def test_clean_accepts_valid_algorithm(self):
        for algo in (0, 128, 255, None):
            with self.subTest(algorithm=algo):
                ISISSRv6Locator(
                    instance=self.instance,
                    name='LOC-ALG',
                    prefix='2001:db8:0:a2::/64',
                    algorithm=algo,
                ).clean()

    def test_db_constraint_rejects_out_of_range_algorithm(self):
        # save() bypasses clean(); the DB CheckConstraint is the backstop.
        with self.assertRaises(IntegrityError), transaction.atomic():
            ISISSRv6Locator.objects.create(
                instance=self.instance,
                name='LOC-DBALG',
                prefix='2001:db8:0:a2::/64',
                algorithm=1,
            )

    def test_clean_rejects_oversized_derived_locator(self):
        # block/node unpinned → the locator length is the prefix length (120), not
        # 0; 120 + 16-bit function = 136 > 128 must be rejected.
        loc = ISISSRv6Locator(
            instance=self.instance,
            name='LOC-DERIVED',
            prefix='2001:db8:0:a2::/120',
            function_length=16,
        )
        with self.assertRaises(ValidationError):
            loc.clean()


class ISISMigrationStateTestCase(TestCase):
    """The IS-IS migration must faithfully capture the models.

    Every IS-IS model's *recorded* CreateModel bases must include PrimaryModel's
    DeleteMixin — a CreateModel that omits ``bases=`` silently records
    ``(models.Model,)`` instead, dropping DeleteMixin from the historical state used by
    data migrations (makemigrations does NOT detect a mixin-only bases drift, so nothing
    else catches it).
    """

    #: every IS-IS PrimaryModel — all subclass DeleteMixin via PrimaryModel
    ISIS_MODELS = (
        'isisinstance',
        'isisinterface',
        'isissetting',
        'isislevel',
        'isisinterfacelevel',
        'isissegmentrouting',
        'isisflexalgo',
        'isisprefixsid',
        'isissrv6locator',
    )

    def test_migration_bases_include_delete_mixin(self):
        from django.db import connection
        from django.db.migrations.loader import MigrationLoader

        from netbox.models.deletion import DeleteMixin

        state = MigrationLoader(connection).project_state()
        dropped = [
            name
            for name in self.ISIS_MODELS
            if DeleteMixin not in state.models['netbox_routing_plugin', name].bases
        ]
        self.assertEqual(
            dropped, [], f'CreateModel bases dropped DeleteMixin for: {dropped}'
        )


class ISISConsistencyTestCase(TestCase):
    """Rules between the instance, its interfaces and its levels (#419, #420, #421)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.other_device = create_test_device(name='Device 2')
        cls.vrf = VRF.objects.create(name='VRF 1')
        cls.instance = ISISInstance.objects.create(
            device=cls.device, process_tag='CORE', is_type='level-1-2'
        )

    def _interface(self, **kwargs):
        kwargs.setdefault('device', self.device)
        return Interface.objects.create(name='eth0', type='virtual', **kwargs)

    def test_interface_vrf_must_match_instance(self):
        entry = ISISInterface(
            instance=self.instance,
            interface=self._interface(vrf=self.vrf),
            address_family='ipv4',
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.clean()
        self.assertIn('interface', ctx.exception.message_dict)

    def test_interface_vrf_matching_is_accepted(self):
        instance = ISISInstance.objects.create(
            device=self.device, process_tag='VRF', vrf=self.vrf
        )
        ISISInterface(
            instance=instance,
            interface=self._interface(vrf=self.vrf),
            address_family='ipv4',
        ).clean()

    def test_moving_interface_to_another_vrf_is_refused(self):
        interface = self._interface()
        ISISInterface.objects.create(
            instance=self.instance, interface=interface, address_family='ipv4'
        )
        interface.vrf = self.vrf
        with self.assertRaises(AbortRequest):
            interface.save()

    def test_changing_instance_device_is_refused_with_interfaces(self):
        ISISInterface.objects.create(
            instance=self.instance,
            interface=self._interface(),
            address_family='ipv4',
        )
        self.instance.device = self.other_device
        with self.assertRaises(ValidationError):
            self.instance.clean()

    def test_circuit_type_must_share_a_level_with_is_type(self):
        self.instance.is_type = 'level-1'
        entry = ISISInterface(
            instance=self.instance,
            interface=self._interface(),
            address_family='ipv4',
            circuit_type='level-2-only',
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.clean()
        self.assertIn('circuit_type', ctx.exception.message_dict)

    def test_interface_level_must_be_run_by_circuit(self):
        entry = ISISInterface.objects.create(
            instance=self.instance,
            interface=self._interface(),
            address_family='ipv4',
            circuit_type='level-1',
        )
        with self.assertRaises(ValidationError) as ctx:
            ISISInterfaceLevel(interface=entry, level=2).clean()
        self.assertIn('level', ctx.exception.message_dict)
        ISISInterfaceLevel(interface=entry, level=1).clean()

    def test_changing_is_type_is_refused_with_existing_level(self):
        ISISLevel.objects.create(instance=self.instance, level=1)
        self.instance.is_type = 'level-2-only'
        with self.assertRaises(ValidationError):
            self.instance.clean()

    def test_level_not_run_is_accepted_when_disabled(self):
        self.instance.is_type = 'level-2-only'
        ISISLevel(instance=self.instance, level=1, disabled=True).clean()

    def test_wide_metrics_only_conflicts_with_narrow_style(self):
        self.instance.metric_style = 'narrow'
        level = ISISLevel(instance=self.instance, level=1, wide_metrics_only=True)
        with self.assertRaises(ValidationError) as ctx:
            level.clean()
        self.assertIn('wide_metrics_only', ctx.exception.message_dict)


class ISISNetTestCase(SimpleTestCase):
    """NET format (ISO 10589, RFC 1195) (#422)."""

    def test_valid_nets(self):
        for net in (
            '49.0001.1921.6800.1001.00',
            '49.01.1921.6800.1001.00',  # one-byte area
            '47.0005.80ff.f800.0000.0001.0000.0000.0001.00',  # long area
            '490001192168001001.00',
        ):
            with self.subTest(net=net):
                self.assertIsNone(net_error(net))

    def test_invalid_nets(self):
        for net in (
            '49.0001.1921.6800.1001.01',  # selector
            '49.0001.1921.6800.1001.0',  # odd digits
            '49.0001.zzzz.6800.1001.00',
            '1921.6800.1001.00',  # no area
            '49.' + '0001.' * 10 + '00',  # more than 20 bytes
        ):
            with self.subTest(net=net):
                self.assertIsNotNone(net_error(net))


class ISISRangeTestCase(TestCase):
    """Limits and ordering of the timers, counters and metrics (#425)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(device=cls.device)

    def _errors(self, obj):
        with self.assertRaises(ValidationError) as ctx:
            obj.clean()
        return ctx.exception.message_dict

    def test_instance_refresh_must_be_below_lifetime(self):
        self.instance.lsp_lifetime = 1200
        self.instance.lsp_refresh_interval = 1200
        self.assertIn('lsp_refresh_interval', self._errors(self.instance))
        self.instance.lsp_refresh_interval = 900
        self.instance.clean()

    def test_instance_max_wait_not_below_initial_wait(self):
        self.instance.spf_initial_wait = 500
        self.instance.spf_max_wait = 100
        self.assertIn('spf_max_wait', self._errors(self.instance))

    def test_instance_ranges(self):
        for field, value in (
            ('distance', 0),
            ('distance', 256),
            ('maximum_paths', 0),
            ('lsp_mtu', 100),
            ('lsp_lifetime', 70000),
        ):
            with self.subTest(field=field, value=value):
                instance = ISISInstance(device=self.device, process_tag='X')
                setattr(instance, field, value)
                self.assertIn(field, self._errors(instance))

    def test_overload_timeout_needs_overload_on_startup(self):
        self.instance.overload_timeout = 300
        self.assertIn('overload_timeout', self._errors(self.instance))
        self.instance.overload_on_startup = True
        self.instance.clean()

    def test_interface_metric_depends_on_metric_style(self):
        interface = Interface.objects.create(
            name='eth0', device=self.device, type='virtual'
        )
        entry = ISISInterface(
            instance=self.instance,
            interface=interface,
            address_family='ipv4',
            metric=100,
        )
        entry.clean()  # wide
        self.instance.metric_style = 'narrow'
        self.assertIn('metric', self._errors(entry))
        self.instance.metric_style = 'wide'
        entry.metric = 16777215
        self.assertIn('metric', self._errors(entry))

    def test_interface_level_ranges(self):
        interface = Interface.objects.create(
            name='eth0', device=self.device, type='virtual'
        )
        entry = ISISInterface.objects.create(
            instance=self.instance, interface=interface, address_family='ipv4'
        )
        for field, value in (
            ('priority', 128),
            ('hello_multiplier', 1),
            ('hello_interval', 0),
        ):
            with self.subTest(field=field):
                level = ISISInterfaceLevel(interface=entry, level=1)
                setattr(level, field, value)
                self.assertIn(field, self._errors(level))

    def test_te_router_id_family(self):
        setting = ISISSetting(
            assigned_object=self.instance,
            key='te_ipv4_router_id',
            value='2001:db8::1',
        )
        with self.assertRaises(ValidationError):
            setting.clean()
        setting.value = 'Loopback0'  # Cisco interface reference
        setting.clean()
        setting.value = '192.0.2.1'
        setting.clean()


class ISISSegmentRoutingRulesTestCase(TestCase):
    """RFC 8667, RFC 8986 and RFC 9350 rules of the segment routing models (#431, #436, #440)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(device=cls.device)
        interface = Interface.objects.create(
            name='lo0', device=cls.device, type='virtual'
        )
        cls.isis_interface = ISISInterface.objects.create(
            instance=cls.instance, interface=interface, address_family='ipv4'
        )

    def _errors(self, obj):
        with self.assertRaises(ValidationError) as ctx:
            obj.clean()
        return ctx.exception.message_dict

    def test_no_php_and_explicit_null_are_exclusive(self):
        sid = ISISPrefixSID(
            interface=self.isis_interface, sid_index=1, no_php=True, explicit_null=True
        )
        self.assertIn('no_php', self._errors(sid))

    def test_label_range(self):
        for label in (15, 1048576):
            with self.subTest(label=label):
                sid = ISISPrefixSID(interface=self.isis_interface, sid_label=label)
                self.assertIn('sid_label', self._errors(sid))
        ISISPrefixSID(interface=self.isis_interface, sid_label=16).clean()

    def test_flex_algo_sid_needs_the_flex_algo(self):
        sid = ISISPrefixSID(interface=self.isis_interface, algorithm=128, sid_index=1)
        self.assertIn('algorithm', self._errors(sid))
        ISISFlexAlgo.objects.create(instance=self.instance, algo_id=128)
        sid.clean()

    def test_index_must_fit_the_srgb(self):
        ISISSegmentRouting.objects.create(
            instance=self.instance, srgb_start=16000, srgb_range=8000
        )
        sid = ISISPrefixSID(interface=self.isis_interface, sid_index=8000)
        self.assertIn('sid_index', self._errors(sid))
        sid.sid_index = 7999
        sid.clean()

    def test_node_flag_needs_a_host_prefix(self):
        from ipam.models import IPAddress

        IPAddress.objects.create(
            address='192.0.2.1/24', assigned_object=self.isis_interface.interface
        )
        sid = ISISPrefixSID(interface=self.isis_interface, sid_index=1, n_flag=True)
        self.assertIn('n_flag', self._errors(sid))
        IPAddress.objects.create(
            address='192.0.2.2/32', assigned_object=self.isis_interface.interface
        )
        sid.clean()

    def test_srgb_and_srlb_limits_and_overlap(self):
        sr = ISISSegmentRouting(instance=self.instance, srgb_start=8, srgb_range=100)
        self.assertIn('srgb_start', self._errors(sr))
        sr = ISISSegmentRouting(
            instance=self.instance, srgb_start=1048000, srgb_range=1000
        )
        self.assertIn('srgb_start', self._errors(sr))
        sr = ISISSegmentRouting(
            instance=self.instance,
            srgb_start=16000,
            srgb_range=8000,
            srlb_start=20000,
            srlb_range=1000,
        )
        self.assertIn('srlb_start', self._errors(sr))
        sr.srlb_start = 15000
        sr.srlb_range = 1000
        sr.clean()

    def test_srv6_locator_prefix_rules(self):
        locator = ISISSRv6Locator(
            instance=self.instance, name='L', prefix='192.0.2.0/24'
        )
        self.assertIn('prefix', self._errors(locator))
        locator = ISISSRv6Locator(
            instance=self.instance,
            name='L',
            prefix='2001:db8:1::/48',
            block_length=32,
            node_length=8,
        )
        self.assertIn('prefix', self._errors(locator))
        locator.node_length = 16
        locator.clean()

    def test_srv6_locator_flex_algo_must_exist(self):
        locator = ISISSRv6Locator(
            instance=self.instance, name='L', prefix='2001:db8:1::/48', algorithm=130
        )
        self.assertIn('algorithm', self._errors(locator))

    def test_flex_algo_priority_range(self):
        algo = ISISFlexAlgo(instance=self.instance, algo_id=128, priority=256)
        self.assertIn('priority', self._errors(algo))

    def test_flex_algo_metric_type_is_a_choice(self):
        algo = ISISFlexAlgo(instance=self.instance, algo_id=128, metric_type='cost')
        with self.assertRaises(ValidationError) as ctx:
            algo.full_clean(exclude=['instance'])
        self.assertIn('metric_type', ctx.exception.message_dict)


class ISISLongTailSettingTestCase(TestCase):
    """The graceful restart, overload and limit settings (#449)."""

    @classmethod
    def setUpTestData(cls):
        cls.instance = ISISInstance.objects.create(
            device=create_test_device(name='Device 1')
        )

    def _setting(self, key, value):
        return ISISSetting(assigned_object=self.instance, key=key, value=value)

    def test_new_keys_are_typed(self):
        self._setting('graceful_restart_t3', '120').clean()
        self._setting('overload_wait_for_bgp', 'true').clean()
        with self.assertRaises(ValidationError):
            self._setting('graceful_restart_t3', 'soon').clean()
        with self.assertRaises(ValidationError):
            self._setting('adjacency_check', 'maybe').clean()

    def test_max_area_addresses_limit(self):
        self._setting('max_area_addresses', '3').clean()
        with self.assertRaises(ValidationError):
            self._setting('max_area_addresses', '255').clean()


class ISISInterfaceOptionsTestCase(TestCase):
    """Per-interface options and per-level hello authentication (#448)."""

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        instance = ISISInstance.objects.create(device=device)
        cls.isis_interface = ISISInterface.objects.create(
            instance=instance,
            interface=Interface.objects.create(
                name='eth0', device=device, type='virtual'
            ),
            address_family='ipv4',
            hello_padding=False,
            ldp_sync=True,
            three_way_handshake=False,
            route_tag=100,
        )

    def test_options_are_saved(self):
        self.isis_interface.refresh_from_db()
        self.assertIs(self.isis_interface.hello_padding, False)
        self.assertIs(self.isis_interface.ldp_sync, True)
        self.assertIsNone(self.isis_interface.prefix_suppression)
        self.assertEqual(self.isis_interface.route_tag, 100)

    def test_route_tag_range(self):
        self.isis_interface.route_tag = 4294967296
        with self.assertRaises(ValidationError) as ctx:
            self.isis_interface.clean()
        self.assertIn('route_tag', ctx.exception.message_dict)

    def test_level_hello_auth_needs_type_and_key(self):
        level = ISISInterfaceLevel(
            interface=self.isis_interface, level=1, hello_auth_type='md5'
        )
        with self.assertRaises(ValidationError) as ctx:
            level.clean()
        self.assertIn('hello_auth_key', ctx.exception.message_dict)
        level.hello_auth_key = 'secret'
        level.clean()


class ISISRoutingModelsTestCase(TestCase):
    """Redistribution, summary addresses and route leaking (#443, #444)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=cls.device, process_tag='CORE', metric_style='wide'
        )

    def assertRejects(self, obj, field):
        with self.assertRaises(ValidationError) as ctx:
            obj.full_clean()
        self.assertIn(field, ctx.exception.error_dict)

    def test_redistribution_connected_needs_no_source(self):
        ISISRedistribution(instance=self.instance, protocol='connected').full_clean()

    def test_redistribution_isis_requires_source(self):
        self.assertRejects(
            ISISRedistribution(instance=self.instance, protocol='isis'), 'isis_source'
        )

    def test_redistribution_rejects_source_of_other_protocol(self):
        other = ISISInstance.objects.create(device=self.device, process_tag='B')
        self.assertRejects(
            ISISRedistribution(
                instance=self.instance, protocol='connected', isis_source=other
            ),
            'isis_source',
        )

    def test_redistribution_isis_not_into_itself(self):
        self.assertRejects(
            ISISRedistribution(
                instance=self.instance, protocol='isis', isis_source=self.instance
            ),
            'isis_source',
        )

    def test_redistribution_source_on_instance_device(self):
        other_device = create_test_device(name='Device 2')
        ospf = OSPFInstance.objects.create(
            device=other_device, name='1', router_id='10.0.0.1'
        )
        self.assertRejects(
            ISISRedistribution(
                instance=self.instance, protocol='ospf', ospf_source=ospf
            ),
            'ospf_source',
        )
        same = OSPFInstance.objects.create(
            device=self.device, name='2', router_id='10.0.0.2'
        )
        ISISRedistribution(
            instance=self.instance, protocol='ospf', ospf_source=same
        ).full_clean()

    def test_redistribution_level_must_be_run_by_instance(self):
        l1 = ISISInstance.objects.create(
            device=self.device, process_tag='L1', is_type='level-1'
        )
        self.assertRejects(
            ISISRedistribution(instance=l1, protocol='static', level='level-2'),
            'level',
        )
        ISISRedistribution(
            instance=l1, protocol='static', level='level-1-2'
        ).full_clean()

    def test_redistribution_metric_follows_metric_style(self):
        narrow = ISISInstance.objects.create(
            device=self.device, process_tag='N', metric_style='narrow'
        )
        self.assertRejects(
            ISISRedistribution(instance=narrow, protocol='static', metric=64), 'metric'
        )
        ISISRedistribution(
            instance=self.instance, protocol='static', metric=64
        ).full_clean()
        self.assertRejects(
            ISISRedistribution(
                instance=self.instance, protocol='static', metric=16777215
            ),
            'metric',
        )

    def test_redistribution_unique_per_family_and_level(self):
        ISISRedistribution.objects.create(instance=self.instance, protocol='static')
        self.assertRejects(
            ISISRedistribution(instance=self.instance, protocol='static'),
            '__all__',
        )
        ISISRedistribution(
            instance=self.instance, protocol='static', address_family='ipv6'
        ).full_clean()

    def test_summary_address_rejects_host_bits(self):
        self.assertRejects(
            ISISSummaryAddress(instance=self.instance, prefix='10.0.0.1/8'), 'prefix'
        )

    def test_summary_address_accepts_both_families(self):
        ISISSummaryAddress(instance=self.instance, prefix='10.0.0.0/8').full_clean()
        ISISSummaryAddress(instance=self.instance, prefix='2001:db8::/32').full_clean()

    def test_summary_address_level_and_metric(self):
        l2 = ISISInstance.objects.create(
            device=self.device, process_tag='L2', is_type='level-2-only'
        )
        self.assertRejects(
            ISISSummaryAddress(instance=l2, prefix='10.0.0.0/8', level='level-1'),
            'level',
        )
        self.assertRejects(
            ISISSummaryAddress(
                instance=self.instance, prefix='10.0.0.0/8', metric=16777215
            ),
            'metric',
        )

    def test_summary_address_unique_per_level(self):
        ISISSummaryAddress.objects.create(instance=self.instance, prefix='10.0.0.0/8')
        self.assertRejects(
            ISISSummaryAddress(instance=self.instance, prefix='10.0.0.0/8'), '__all__'
        )
        ISISSummaryAddress(
            instance=self.instance, prefix='10.0.0.0/8', level='level-1'
        ).full_clean()

    def test_route_leak_needs_both_levels(self):
        ISISRouteLeak(instance=self.instance).full_clean()
        l2 = ISISInstance.objects.create(
            device=self.device, process_tag='L2', is_type='level-2-only'
        )
        self.assertRejects(ISISRouteLeak(instance=l2), 'instance')

    def test_route_leak_unique_per_family(self):
        ISISRouteLeak.objects.create(instance=self.instance)
        self.assertRejects(ISISRouteLeak(instance=self.instance), '__all__')
        ISISRouteLeak(instance=self.instance, address_family='ipv6').full_clean()


class ISISAreaAddressTestCase(TestCase):
    """Several area addresses on one instance (#446, ISO 10589 7.1.4)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=cls.device, process_tag='CORE', net='49.0001.0000.0000.0001.00'
        )

    def assertRejects(self, obj, field='net'):
        with self.assertRaises(ValidationError) as ctx:
            obj.full_clean()
        self.assertIn(field, ctx.exception.error_dict)

    def test_splits_area_and_system_id(self):
        extra = ISISAreaAddress(instance=self.instance, net='49.0002.0000.0000.0001.00')
        extra.full_clean()
        self.assertEqual(extra.area, '49.0002')
        self.assertEqual(extra.system_id, '0000.0000.0001')

    def test_rejects_malformed_net(self):
        self.assertRejects(ISISAreaAddress(instance=self.instance, net='zz'))

    def test_must_share_system_id(self):
        self.assertRejects(
            ISISAreaAddress(instance=self.instance, net='49.0002.0000.0000.0009.00')
        )

    def test_rejects_the_area_already_in_use(self):
        self.assertRejects(
            ISISAreaAddress(instance=self.instance, net='49.0001.0000.0000.0001.00')
        )

    def test_at_most_three_area_addresses(self):
        for area in ('0002', '0003'):
            ISISAreaAddress.objects.create(
                instance=self.instance, net=f'49.{area}.0000.0000.0001.00'
            )
        self.assertRejects(
            ISISAreaAddress(instance=self.instance, net='49.0004.0000.0000.0001.00')
        )

    def test_instance_system_id_must_match_area_addresses(self):
        ISISAreaAddress.objects.create(
            instance=self.instance, net='49.0002.0000.0000.0001.00'
        )
        self.instance.net = '49.0001.0000.0000.0007.00'
        with self.assertRaises(ValidationError) as ctx:
            self.instance.full_clean()
        self.assertIn('net', ctx.exception.error_dict)

    def test_duplicate_system_id_is_listed(self):
        other = ISISInstance.objects.create(
            device=create_test_device(name='Device 2'),
            process_tag='X',
            net='49.0001.0000.0000.0001.00',
        )
        self.assertEqual(self.instance.duplicate_system_ids, [other])
        self.assertIn('Device 2', self.instance.duplicate_system_ids_display)
        other.net = '49.0001.0000.0000.0005.00'
        other.save()
        self.assertEqual(self.instance.duplicate_system_ids, [])
        self.assertEqual(self.instance.duplicate_system_ids_display, '—')

    def test_duplicate_through_a_shared_added_area(self):
        other = ISISInstance.objects.create(
            device=create_test_device(name='Device 2'),
            process_tag='X',
            net='49.0005.0000.0000.0001.00',
        )
        self.assertEqual(self.instance.duplicate_system_ids, [])
        ISISAreaAddress.objects.create(instance=other, net='49.0001.0000.0000.0001.00')
        self.assertEqual(self.instance.duplicate_system_ids, [other])


class ISISAuthenticationTestCase(TestCase):
    """HMAC-SHA types, key chains, key IDs and send-only (#447, RFC 5310)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(device=cls.device)
        cls.interface = ISISInterface.objects.create(
            instance=cls.instance,
            interface=Interface.objects.create(
                name='Eth1', device=cls.device, type='virtual'
            ),
            address_family='ipv4',
        )

    def groups(self):
        """Every object with an authentication group: (object, prefix of the key)."""
        level = ISISLevel(instance=self.instance, level=1)
        interface_level = ISISInterfaceLevel(interface=self.interface, level=1)
        return (
            (ISISInstance.objects.get(pk=self.instance.pk), 'area_auth'),
            (ISISInstance.objects.get(pk=self.instance.pk), 'domain_auth'),
            (level, 'auth'),
            (self.interface, 'hello_auth'),
            (interface_level, 'hello_auth'),
        )

    def assertRejects(self, obj, field):
        with self.assertRaises(ValidationError) as ctx:
            obj.full_clean()
        self.assertIn(field, ctx.exception.error_dict)

    def set_auth(self, obj, prefix, **values):
        for name, value in values.items():
            setattr(obj, f'{prefix}_{name}', value)

    def clear_auth(self, obj, prefix):
        for name, value in (
            ('type', ''),
            ('key', ''),
            ('key_id', None),
            ('key_chain', ''),
        ):
            setattr(obj, f'{prefix}_{name}', value)
        setattr(obj, f'{prefix}_send_only', False)

    def test_new_hmac_types_are_choices(self):
        from netbox_routing_plugin.choices import ISISAuthTypeChoices

        values = {value for value, _label in ISISAuthTypeChoices.CHOICES}
        for value in ('hmac-sha-224', 'hmac-sha-384', 'hmac-sha-512', 'key-chain'):
            self.assertIn(value, values)

    def test_hmac_sha_accepts_key_and_key_id(self):
        for obj, prefix in self.groups():
            with self.subTest(prefix=prefix, model=type(obj).__name__):
                self.clear_auth(obj, prefix)
                self.set_auth(obj, prefix, type='hmac-sha-512', key='secret', key_id=7)
                obj.full_clean()

    def test_key_id_range_and_type(self):
        for obj, prefix in self.groups():
            with self.subTest(prefix=prefix, model=type(obj).__name__):
                self.clear_auth(obj, prefix)
                self.set_auth(obj, prefix, type='hmac-sha-256', key='s', key_id=65536)
                self.assertRejects(obj, f'{prefix}_key_id')
                self.set_auth(obj, prefix, type='md5', key='s', key_id=1)
                self.assertRejects(obj, f'{prefix}_key_id')

    def test_key_chain_needs_only_the_name(self):
        for obj, prefix in self.groups():
            with self.subTest(prefix=prefix, model=type(obj).__name__):
                self.clear_auth(obj, prefix)
                self.set_auth(obj, prefix, type='key-chain')
                self.assertRejects(obj, f'{prefix}_key_chain')
                self.set_auth(obj, prefix, key_chain='KC-1')
                obj.full_clean()
                self.set_auth(obj, prefix, key='secret')
                self.assertRejects(obj, f'{prefix}_key')
                self.set_auth(obj, prefix, key='', key_id=3)
                self.assertRejects(obj, f'{prefix}_key_id')

    def test_key_chain_name_needs_the_type(self):
        for obj, prefix in self.groups():
            with self.subTest(prefix=prefix, model=type(obj).__name__):
                self.clear_auth(obj, prefix)
                self.set_auth(obj, prefix, type='md5', key='s', key_chain='KC')
                self.assertRejects(obj, f'{prefix}_key_chain')

    def test_send_only_needs_a_type(self):
        for obj, prefix in self.groups():
            with self.subTest(prefix=prefix, model=type(obj).__name__):
                self.clear_auth(obj, prefix)
                setattr(obj, f'{prefix}_send_only', True)
                self.assertRejects(obj, f'{prefix}_send_only')
                self.set_auth(obj, prefix, type='text', key='pw')
                obj.full_clean()


class ISISSegmentRoutingExtrasTestCase(TestCase):
    """SR mapping entries, adjacency-SIDs and the link attributes of Flex-Algo (#450)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(device=cls.device)
        cls.interface = ISISInterface.objects.create(
            instance=cls.instance,
            interface=Interface.objects.create(
                name='Eth1', device=cls.device, type='virtual'
            ),
            address_family='ipv4',
        )
        ISISSegmentRouting.objects.create(
            instance=cls.instance,
            srgb_start=16000,
            srgb_range=8000,
            srlb_start=15000,
            srlb_range=1000,
        )

    def assertRejects(self, obj, field):
        with self.assertRaises(ValidationError) as ctx:
            obj.full_clean()
        self.assertIn(field, ctx.exception.error_dict)

    def entry(self, **kwargs):
        values = {'instance': self.instance, 'prefix': '10.0.0.0/24', 'sid_index': 100}
        values.update(kwargs)
        return ISISSRMappingEntry(**values)

    def test_mapping_entry_valid(self):
        self.entry().full_clean()
        self.entry(prefix='2001:db8::/64', sid_index=None, sid_label=17000).full_clean()

    def test_mapping_entry_needs_index_or_label(self):
        self.assertRejects(self.entry(sid_index=None), 'sid_index')
        self.assertRejects(self.entry(sid_label=17000), 'sid_label')

    def test_mapping_entry_prefix_and_range(self):
        self.assertRejects(self.entry(prefix='10.0.0.1/24'), 'prefix')
        self.assertRejects(self.entry(range_size=0), 'range_size')
        self.assertRejects(self.entry(range_size=65536), 'range_size')

    def test_mapping_entry_range_inside_srgb(self):
        self.entry(sid_index=7990, range_size=10).full_clean()
        self.assertRejects(self.entry(sid_index=7995, range_size=10), 'sid_index')

    def test_mapping_entry_algorithm_and_level(self):
        self.assertRejects(self.entry(algorithm=128), 'algorithm')
        ISISFlexAlgo.objects.create(instance=self.instance, algo_id=128)
        self.entry(algorithm=128).full_clean()
        self.assertRejects(self.entry(algorithm=5), 'algorithm')
        l2 = ISISInstance.objects.create(
            device=self.device, process_tag='L2', is_type='level-2-only'
        )
        self.assertRejects(self.entry(instance=l2, level='level-1'), 'level')

    def test_mapping_entry_unique(self):
        self.entry().save()
        self.assertRejects(self.entry(), '__all__')
        self.entry(level='level-1').full_clean()

    def test_adjacency_sid_inside_srlb(self):
        ISISAdjacencySID(interface=self.interface, sid_label=15500).full_clean()
        self.assertRejects(
            ISISAdjacencySID(interface=self.interface, sid_label=16500), 'sid_label'
        )
        self.assertRejects(
            ISISAdjacencySID(interface=self.interface, sid_label=10), 'sid_label'
        )

    def test_adjacency_sid_without_srlb(self):
        self.instance.segment_routing.delete()
        interface = ISISInterface.objects.get(pk=self.interface.pk)
        ISISAdjacencySID(interface=interface, sid_label=24000).full_clean()

    def test_adjacency_sid_unique_label(self):
        ISISAdjacencySID.objects.create(interface=self.interface, sid_label=15500)
        self.assertRejects(
            ISISAdjacencySID(interface=self.interface, sid_label=15500), '__all__'
        )

    def test_link_attributes(self):
        self.interface.admin_group = 'RED,BLUE'
        self.interface.te_metric = 10
        self.interface.delay_metric = 2500
        self.interface.full_clean()
        self.interface.delay_metric = 16777216
        self.assertRejects(self.interface, 'delay_metric')


class ISISAddressFamilyTestCase(TestCase):
    """Settings by address family of an instance (#445)."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = ISISInstance.objects.create(
            device=cls.device, metric_style='wide', distance=115, maximum_paths=4
        )
        cls.interface = ISISInterface.objects.create(
            instance=cls.instance,
            interface=Interface.objects.create(
                name='Eth1', device=cls.device, type='virtual'
            ),
            address_family='ipv6',
        )

    def assertRejects(self, obj, field):
        with self.assertRaises(ValidationError) as ctx:
            obj.full_clean()
        self.assertIn(field, ctx.exception.error_dict)

    def test_empty_family_uses_the_instance(self):
        ISISAddressFamily(instance=self.instance, address_family='ipv6').full_clean()
        self.assertEqual(self.instance.metric_style_for('ipv6'), 'wide')

    def test_family_metric_style_overrides_the_instance(self):
        ISISAddressFamily.objects.create(
            instance=self.instance, address_family='ipv4', metric_style='narrow'
        )
        self.assertEqual(self.instance.metric_style_for('ipv4'), 'narrow')
        self.assertEqual(self.instance.metric_style_for('ipv6'), 'wide')

    def test_narrow_family_limits_the_metrics_of_its_interfaces(self):
        ISISAddressFamily.objects.create(
            instance=self.instance, address_family='ipv6', metric_style='narrow'
        )
        self.interface.metric = 64
        self.assertRejects(self.interface, 'metric')
        self.interface.metric = 63
        self.interface.full_clean()

    def test_narrow_is_refused_with_wide_metrics_in_use(self):
        self.interface.metric = 500
        self.interface.save()
        self.assertRejects(
            ISISAddressFamily(
                instance=self.instance, address_family='ipv6', metric_style='narrow'
            ),
            'metric_style',
        )

    def test_ranges(self):
        for field, value in (('distance', 0), ('distance', 256), ('maximum_paths', 0)):
            with self.subTest(field=field, value=value):
                self.assertRejects(
                    ISISAddressFamily(
                        instance=self.instance,
                        address_family='ipv4',
                        **{field: value},
                    ),
                    field,
                )

    def test_unique_per_family(self):
        ISISAddressFamily.objects.create(instance=self.instance, address_family='ipv4')
        self.assertRejects(
            ISISAddressFamily(instance=self.instance, address_family='ipv4'),
            '__all__',
        )
        ISISAddressFamily(instance=self.instance, address_family='ipv6').full_clean()
