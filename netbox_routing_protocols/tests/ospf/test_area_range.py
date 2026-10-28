import netaddr
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.filtersets import OSPFAreaRangeFilterSet
from netbox_routing_protocols.models import OSPFArea, OSPFAreaRange, OSPFInstance
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'OSPFAreaRangeModelTestCase',
    'OSPFAreaRangeFilterSetTestCase',
    'OSPFAreaRangeViewTestCase',
    'OSPFAreaRangeAPITestCase',
)


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instance = OSPFInstance.objects.create(
        name='Instance 1', device=cls.device, router_id='1.1.1.1'
    )
    cls.areas = [
        OSPFArea.objects.create(instance=cls.instance, area_id=str(i)) for i in (1, 2)
    ]


class OSPFAreaRangeModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _range(self, prefix='10.0.0.0/8', **kwargs):
        return OSPFAreaRange(area=self.areas[0], prefix=prefix, **kwargs)

    def test_a_range_is_advertised_by_default(self):
        area_range = self._range()
        area_range.full_clean()
        self.assertTrue(area_range.advertise)
        self.assertEqual(str(area_range), '10.0.0.0/8')

    def test_a_range_summarizes_intra_area_routes_by_default(self):
        self.assertEqual(self._range().range_type, 'summary')

    def test_nssa_ranges_only_exist_on_nssa_areas(self):
        for number, area_type in enumerate(('nssa', 'tnssa'), start=90):
            with self.subTest(area_type=area_type):
                nssa = OSPFArea.objects.create(
                    instance=self.instance,
                    area_id=str(number),
                    area_type=area_type,
                )
                OSPFAreaRange(
                    area=nssa, prefix='10.0.0.0/8', range_type='nssa-external'
                ).full_clean()
        for number, area_type in enumerate(('standard', 'stub', 'tsa'), start=80):
            with self.subTest(area_type=area_type):
                other = OSPFArea.objects.create(
                    instance=self.instance,
                    area_id=str(number),
                    area_type=area_type,
                )
                with self.assertRaises(ValidationError) as cm:
                    OSPFAreaRange(
                        area=other, prefix='10.0.0.0/8', range_type='nssa-external'
                    ).full_clean()
                self.assertIn('range_type', cm.exception.error_dict)

    def test_the_same_prefix_can_be_a_summary_and_an_nssa_range(self):
        nssa = OSPFArea.objects.create(
            instance=self.instance, area_id='7', area_type='nssa'
        )
        OSPFAreaRange.objects.create(area=nssa, prefix='10.0.0.0/8')
        OSPFAreaRange.objects.create(
            area=nssa, prefix='10.0.0.0/8', range_type='nssa-external'
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            OSPFAreaRange.objects.create(
                area=nssa, prefix='10.0.0.0/8', range_type='nssa-external'
            )

    def test_a_range_can_be_not_advertised(self):
        self._range(advertise=False).full_clean()

    def test_only_ipv4_prefixes(self):
        with self.assertRaises(ValidationError) as cm:
            self._range('2001:db8::/32').full_clean()
        self.assertIn('prefix', cm.exception.error_dict)

    def test_the_prefix_cannot_have_host_bits(self):
        with self.assertRaises(ValidationError) as cm:
            self._range('10.0.0.1/8').full_clean()
        self.assertIn('prefix', cm.exception.error_dict)

    def test_a_range_exists_once_per_area(self):
        OSPFAreaRange.objects.create(area=self.areas[0], prefix='10.0.0.0/8')
        with self.assertRaises(IntegrityError), transaction.atomic():
            OSPFAreaRange.objects.create(area=self.areas[0], prefix='10.0.0.0/8')
        OSPFAreaRange.objects.create(area=self.areas[1], prefix='10.0.0.0/8')

    def test_deleting_the_area_deletes_its_ranges(self):
        OSPFAreaRange.objects.create(area=self.areas[0], prefix='10.0.0.0/8')
        self.areas[0].delete()
        self.assertFalse(OSPFAreaRange.objects.exists())


class OSPFAreaRangeFilterSetTestCase(TestCase):
    queryset = OSPFAreaRange.objects.all()
    filterset = OSPFAreaRangeFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFAreaRange.objects.bulk_create(
            (
                OSPFAreaRange(area=cls.areas[0], prefix='10.0.0.0/8'),
                OSPFAreaRange(
                    area=cls.areas[0], prefix='172.16.0.0/12', advertise=False
                ),
                OSPFAreaRange(area=cls.areas[1], prefix='10.0.0.0/8'),
                OSPFAreaRange(
                    area=cls.areas[1],
                    prefix='192.168.0.0/16',
                    range_type='nssa-external',
                ),
            )
        )

    def test_filters(self):
        for params, expected in (
            ({'area_id': [self.areas[0].pk]}, 2),
            ({'instance_id': [self.instance.pk]}, 4),
            ({'device_id': [self.device.pk]}, 4),
            ({'prefix': '10.0.0.0/8'}, 2),
            ({'prefix': 'not a prefix'}, 0),
            ({'range_type': ['nssa-external']}, 1),
            ({'advertise': False}, 1),
            ({'q': '172.16'}, 1),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.filterset(params, self.queryset).qs.count(), expected
                )


class OSPFAreaRangeViewTestCase(
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
    model = OSPFAreaRange

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFAreaRange.objects.bulk_create(
            (
                OSPFAreaRange(area=cls.areas[0], prefix='10.0.0.0/8'),
                OSPFAreaRange(area=cls.areas[0], prefix='172.16.0.0/12'),
                OSPFAreaRange(area=cls.areas[1], prefix='10.0.0.0/8'),
            )
        )
        cls.form_data = {
            'area': cls.areas[1].pk,
            'prefix': netaddr.IPNetwork('192.168.0.0/16'),
            'range_type': 'summary',
            'advertise': False,
        }
        cls.bulk_edit_data = {'description': 'A test description', 'advertise': False}

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfarearange_{}'


class OSPFAreaRangeAPITestCase(LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFAreaRange
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['area', 'display', 'id', 'prefix', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfarea',
        'netbox_routing_protocols.view_ospfinstance',
        'dcim.view_device',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFAreaRange.objects.bulk_create(
            (
                OSPFAreaRange(area=cls.areas[0], prefix='10.0.0.0/8'),
                OSPFAreaRange(area=cls.areas[0], prefix='172.16.0.0/12'),
                OSPFAreaRange(area=cls.areas[1], prefix='10.0.0.0/8'),
            )
        )
        cls.create_data = [
            {
                'area': cls.areas[1].pk,
                'prefix': '192.168.0.0/16',
                'advertise': False,
            },
        ]
