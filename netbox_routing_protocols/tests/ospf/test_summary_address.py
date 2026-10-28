import netaddr
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.filtersets import OSPFSummaryAddressFilterSet
from netbox_routing_protocols.models import OSPFInstance, OSPFSummaryAddress

__all__ = (
    'OSPFSummaryAddressModelTestCase',
    'OSPFSummaryAddressFilterSetTestCase',
    'OSPFSummaryAddressViewTestCase',
    'OSPFSummaryAddressAPITestCase',
)


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instances = [
        OSPFInstance.objects.create(
            name=f'Instance {i}',
            device=cls.device,
            router_id=f'1.1.1.{i}',
        )
        for i in (1, 2)
    ]


class OSPFSummaryAddressModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _summary(self, prefix='10.0.0.0/8', **kwargs):
        return OSPFSummaryAddress(instance=self.instances[0], prefix=prefix, **kwargs)

    def test_defaults(self):
        summary = self._summary()
        summary.full_clean()
        self.assertFalse(summary.not_advertise)
        self.assertIsNone(summary.route_tag)
        self.assertEqual(str(summary), '10.0.0.0/8')

    def test_only_ipv4_prefixes(self):
        with self.assertRaises(ValidationError) as cm:
            self._summary('2001:db8::/32').full_clean()
        self.assertIn('prefix', cm.exception.error_dict)

    def test_the_prefix_cannot_have_host_bits(self):
        with self.assertRaises(ValidationError) as cm:
            self._summary('10.0.0.1/8').full_clean()
        self.assertIn('prefix', cm.exception.error_dict)

    def test_route_tag_limits(self):
        for route_tag in (0, 4294967295):
            self._summary(route_tag=route_tag).full_clean()
        with self.assertRaises(ValidationError) as cm:
            self._summary(route_tag=4294967296).full_clean()
        self.assertIn('route_tag', cm.exception.error_dict)

    def test_a_prefix_is_summarized_once_per_instance(self):
        OSPFSummaryAddress.objects.create(
            instance=self.instances[0], prefix='10.0.0.0/8'
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            OSPFSummaryAddress.objects.create(
                instance=self.instances[0], prefix='10.0.0.0/8'
            )
        OSPFSummaryAddress.objects.create(
            instance=self.instances[1], prefix='10.0.0.0/8'
        )

    def test_deleting_the_instance_deletes_its_summary_addresses(self):
        OSPFSummaryAddress.objects.create(
            instance=self.instances[0], prefix='10.0.0.0/8'
        )
        self.instances[0].delete()
        self.assertFalse(OSPFSummaryAddress.objects.exists())


class OSPFSummaryAddressFilterSetTestCase(TestCase):
    queryset = OSPFSummaryAddress.objects.all()
    filterset = OSPFSummaryAddressFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFSummaryAddress.objects.bulk_create(
            (
                OSPFSummaryAddress(
                    instance=cls.instances[0], prefix='10.0.0.0/8', route_tag=7
                ),
                OSPFSummaryAddress(
                    instance=cls.instances[0],
                    prefix='172.16.0.0/12',
                    not_advertise=True,
                ),
                OSPFSummaryAddress(instance=cls.instances[1], prefix='10.0.0.0/8'),
            )
        )

    def test_filters(self):
        for params, expected in (
            ({'instance_id': [self.instances[0].pk]}, 2),
            ({'instance': ['Instance 2']}, 1),
            ({'device_id': [self.device.pk]}, 3),
            ({'prefix': '10.0.0.0/8'}, 2),
            ({'prefix': 'not a prefix'}, 0),
            ({'not_advertise': True}, 1),
            ({'route_tag': [7]}, 1),
            ({'q': '172.16'}, 1),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.filterset(params, self.queryset).qs.count(), expected
                )


class OSPFSummaryAddressViewTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFSummaryAddress

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFSummaryAddress.objects.bulk_create(
            (
                OSPFSummaryAddress(instance=cls.instances[0], prefix='10.0.0.0/8'),
                OSPFSummaryAddress(instance=cls.instances[0], prefix='172.16.0.0/12'),
                OSPFSummaryAddress(instance=cls.instances[1], prefix='10.0.0.0/8'),
            )
        )
        cls.form_data = {
            'instance': cls.instances[1].pk,
            'prefix': netaddr.IPNetwork('192.168.0.0/16'),
            'not_advertise': True,
            'route_tag': 5,
        }
        cls.bulk_edit_data = {'description': 'A test description', 'route_tag': 9}

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfsummaryaddress_{}'


class OSPFSummaryAddressAPITestCase(APIViewTestCases.APIViewTestCase):
    model = OSPFSummaryAddress
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['display', 'id', 'instance', 'prefix', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'dcim.view_device',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFSummaryAddress.objects.bulk_create(
            (
                OSPFSummaryAddress(instance=cls.instances[0], prefix='10.0.0.0/8'),
                OSPFSummaryAddress(instance=cls.instances[0], prefix='172.16.0.0/12'),
                OSPFSummaryAddress(instance=cls.instances[1], prefix='10.0.0.0/8'),
            )
        )
        cls.create_data = [
            {
                'instance': cls.instances[1].pk,
                'prefix': '192.168.0.0/16',
                'not_advertise': True,
                'route_tag': 5,
            },
        ]
