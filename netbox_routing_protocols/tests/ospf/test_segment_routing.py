import netaddr
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.filtersets import OSPFPrefixSIDFilterSet
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFPrefixSID,
)
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'OSPFSegmentRoutingTestCase',
    'OSPFPrefixSIDFilterSetTestCase',
    'OSPFPrefixSIDViewTestCase',
    'OSPFPrefixSIDAPITestCase',
)


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instance = OSPFInstance.objects.create(
        name='Instance 1',
        device=cls.device,
        router_id='1.1.1.1',
        opaque_capability=True,
        segment_routing=True,
        srgb_start=16000,
        srgb_size=8000,
    )
    OSPFPrefixSID.objects.bulk_create(
        (
            OSPFPrefixSID(
                instance=cls.instance, prefix='10.0.0.1/32', sid=1, node_sid=True
            ),
            OSPFPrefixSID(instance=cls.instance, prefix='10.0.0.2/32', sid=2),
            OSPFPrefixSID(
                instance=cls.instance,
                prefix='10.0.1.0/24',
                sid_type='absolute',
                sid=20000,
            ),
        )
    )


class OSPFSegmentRoutingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1',
            device=cls.device,
            router_id='1.1.1.1',
            opaque_capability=True,
            segment_routing=True,
            srgb_start=16000,
            srgb_size=8000,
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def _sid(self, **kwargs):
        data = {'instance': self.instance, 'prefix': '10.0.0.1/32', 'sid': 1}
        data.update(kwargs)
        return OSPFPrefixSID(**data)

    def test_srgb_needs_opaque_lsas(self):
        self.instance.opaque_capability = False
        self._assert_invalid(self.instance, 'segment_routing')

    def test_srgb_start_and_size_go_together_and_fit_the_label_space(self):
        self.instance.full_clean()
        self.instance.srgb_size = None
        self._assert_invalid(self.instance, 'srgb_size')
        self.instance.srgb_size = 8000
        self.instance.srgb_start = 15
        self._assert_invalid(self.instance, 'srgb_start')
        self.instance.srgb_start = 1048000
        self.instance.srgb_size = 1000
        self._assert_invalid(self.instance, 'srgb_size')
        self.instance.srgb_start = 1048575
        self.instance.srgb_size = 1
        self.instance.full_clean()

    def test_prefix_sid_index_must_fit_the_srgb(self):
        self._sid(sid=7999).full_clean()
        self._assert_invalid(self._sid(sid=8000), 'sid')

    def test_prefix_sid_absolute_label_range(self):
        self._sid(sid_type='absolute', sid=16000).full_clean()
        for label in (15, 1048576):
            with self.subTest(label=label):
                self._assert_invalid(self._sid(sid_type='absolute', sid=label), 'sid')

    def test_node_sid_must_be_a_host_prefix(self):
        self._sid(node_sid=True).full_clean()
        self._assert_invalid(self._sid(prefix='10.0.0.0/24', node_sid=True), 'node_sid')
        self._sid(prefix='10.0.0.0/24').full_clean()

    def test_prefix_must_be_ipv4_without_host_bits(self):
        self._assert_invalid(self._sid(prefix='2001:db8::/32'), 'prefix')
        self._assert_invalid(self._sid(prefix='10.0.0.1/24'), 'prefix')

    def test_prefix_sid_needs_segment_routing(self):
        OSPFInstance.objects.filter(pk=self.instance.pk).update(segment_routing=False)
        self.instance.refresh_from_db()
        self._assert_invalid(self._sid(), 'instance')

    def test_segment_routing_cannot_be_disabled_while_sids_exist(self):
        self._sid().save()
        self.instance.segment_routing = False
        self.instance.srgb_start = None
        self.instance.srgb_size = None
        self._assert_invalid(self.instance, 'segment_routing')

    def test_srgb_cannot_shrink_below_existing_index_sids(self):
        self._sid(sid=5000).save()
        self.instance.srgb_size = 4000
        self._assert_invalid(self.instance, 'srgb_size')

    def test_unique_prefix_and_sid_per_algorithm(self):
        self._sid().save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._sid(sid=2).save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._sid(prefix='10.0.0.2/32').save()
        self._sid(algorithm=1).save()

    def test_adjacency_sid(self):
        interface = OSPFInterface(
            instance=self.instance,
            area=self.area,
            interface=self.interface,
            adjacency_sid=24000,
        )
        interface.full_clean()
        for label in (15, 1048576):
            with self.subTest(label=label):
                interface.adjacency_sid = label
                self._assert_invalid(interface, 'adjacency_sid')
        interface.adjacency_sid = 24000
        OSPFInstance.objects.filter(pk=self.instance.pk).update(segment_routing=False)
        interface.instance.refresh_from_db()
        self._assert_invalid(interface, 'adjacency_sid')


class OSPFPrefixSIDFilterSetTestCase(TestCase):
    queryset = OSPFPrefixSID.objects.all()
    filterset = OSPFPrefixSIDFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def test_filters(self):
        for params, expected in (
            ({'instance_id': [self.instance.pk]}, 3),
            ({'device_id': [self.device.pk]}, 3),
            ({'prefix': '10.0.0.1/32'}, 1),
            ({'prefix': 'bad'}, 0),
            ({'sid_type': ['absolute']}, 1),
            ({'node_sid': True}, 1),
            ({'algorithm': ['0']}, 3),
            ({'q': '10.0.1'}, 1),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.filterset(params, self.queryset).qs.count(), expected
                )


class OSPFPrefixSIDViewTestCase(
    LeanCoreTestsMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFPrefixSID

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        cls.form_data = {
            'instance': cls.instance.pk,
            'prefix': netaddr.IPNetwork('10.0.2.0/24'),
            'sid_type': 'index',
            'sid': 30,
            'algorithm': 0,
            'node_sid': False,
        }
        cls.bulk_edit_data = {'description': 'A test description', 'no_php': True}

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfprefixsid_{}'


class OSPFPrefixSIDAPITestCase(LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFPrefixSID
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['display', 'id', 'instance', 'prefix', 'sid', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'dcim.view_device',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        cls.create_data = [
            {
                'instance': cls.instance.pk,
                'prefix': '10.0.2.0/24',
                'sid': 30,
                'node_sid': False,
            },
        ]
