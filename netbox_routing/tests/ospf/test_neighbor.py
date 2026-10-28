from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dcim.models import Interface
from ipam.models import IPAddress
from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing.filtersets import OSPFNeighborFilterSet
from netbox_routing.models import OSPFArea, OSPFInstance, OSPFInterface, OSPFNeighbor
from netbox_routing.tests.base import IPAddressFieldMixin

__all__ = (
    'OSPFNeighborModelTestCase',
    'OSPFNeighborFilterSetTestCase',
    'OSPFNeighborViewTestCase',
    'OSPFNeighborAPITestCase',
)


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instance = OSPFInstance.objects.create(
        name='Instance 1', device=cls.device, router_id='1.1.1.1', process_id=1
    )
    cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def ospf_interface(name, network_type, address=None):
        interface = Interface.objects.create(
            name=name, device=cls.device, type='virtual'
        )
        if address:
            IPAddress.objects.create(address=address, assigned_object=interface)
        return OSPFInterface.objects.create(
            instance=cls.instance,
            area=cls.area,
            interface=interface,
            network_type=network_type,
        )

    cls.nbma = ospf_interface('nbma', 'non_broadcast', '10.1.0.1/24')
    cls.p2mp = ospf_interface('p2mp', 'point_to_multipoint', '10.2.0.1/24')
    cls.p2mp_nb = ospf_interface(
        'p2mp-nb', 'point_to_multipoint_non_broadcast', '10.3.0.1/24'
    )
    cls.broadcast = ospf_interface('broadcast', 'broadcast', '10.4.0.1/24')
    cls.point_to_point = ospf_interface('p2p', 'point_to_point', '10.5.0.1/24')
    cls.unnumbered = ospf_interface('unnumbered', 'non_broadcast')


class OSPFNeighborModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _neighbor(self, ospf_interface=None, ip_address='10.1.0.2', **kwargs):
        return OSPFNeighbor(
            ospf_interface=ospf_interface or self.nbma, ip_address=ip_address, **kwargs
        )

    def _assert_invalid(self, field, *args, **kwargs):
        with self.assertRaises(ValidationError) as cm:
            self._neighbor(*args, **kwargs).full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_non_broadcast_neighbor(self):
        self._neighbor(priority=1, poll_interval=120).full_clean()
        self._neighbor(priority=0).full_clean()
        self.assertEqual(str(self._neighbor(priority=0)), '10.1.0.2')

    def test_non_broadcast_needs_the_eligibility_to_be_designated_router(self):
        self._assert_invalid('priority')

    def test_priority_limits(self):
        for priority in (0, 255):
            self._neighbor(priority=priority).full_clean()
        self._assert_invalid('priority', priority=256)

    def test_the_poll_interval_must_exceed_the_hello_interval(self):
        hello = self.nbma.hello_interval
        self._neighbor(priority=0, poll_interval=hello + 1).full_clean()
        self._assert_invalid('poll_interval', priority=0, poll_interval=hello)

    def test_point_to_multipoint_neighbor_has_only_an_address(self):
        for ospf_interface, address in (
            (self.p2mp, '10.2.0.2'),
            (self.p2mp_nb, '10.3.0.2'),
        ):
            with self.subTest(interface=ospf_interface.interface.name):
                self._neighbor(ospf_interface, address).full_clean()
                self._assert_invalid('priority', ospf_interface, address, priority=1)
                self._assert_invalid(
                    'poll_interval', ospf_interface, address, poll_interval=120
                )

    def test_other_network_types_have_no_configured_neighbors(self):
        for ospf_interface, address in (
            (self.broadcast, '10.4.0.2'),
            (self.point_to_point, '10.5.0.2'),
        ):
            with self.subTest(interface=ospf_interface.interface.name):
                self._assert_invalid('ospf_interface', ospf_interface, address)

    def test_the_address_must_be_a_unicast_ipv4_address(self):
        for address in ('2001:db8::1', '127.0.0.1', '224.0.0.5'):
            with self.subTest(address=address):
                self._assert_invalid('ip_address', ip_address=address, priority=0)

    def test_the_address_cannot_be_the_one_of_the_interface(self):
        self._assert_invalid('ip_address', ip_address='10.1.0.1', priority=0)

    def test_the_address_must_be_on_a_network_of_the_interface(self):
        self._assert_invalid('ip_address', ip_address='10.9.0.2', priority=0)

    def test_an_interface_without_addresses_accepts_any_ipv4_address(self):
        self._neighbor(self.unnumbered, '10.9.0.2', priority=0).full_clean()

    def test_a_neighbor_is_configured_once_per_interface(self):
        OSPFNeighbor.objects.create(
            ospf_interface=self.nbma, ip_address='10.1.0.2', priority=0
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            OSPFNeighbor.objects.create(
                ospf_interface=self.nbma, ip_address='10.1.0.2', priority=1
            )

    def test_deleting_the_interface_deletes_its_neighbors(self):
        OSPFNeighbor.objects.create(
            ospf_interface=self.nbma, ip_address='10.1.0.2', priority=0
        )
        self.nbma.delete()
        self.assertFalse(OSPFNeighbor.objects.exists())


class OSPFNeighborFilterSetTestCase(TestCase):
    queryset = OSPFNeighbor.objects.all()
    filterset = OSPFNeighborFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFNeighbor.objects.bulk_create(
            (
                OSPFNeighbor(
                    ospf_interface=cls.nbma,
                    ip_address='10.1.0.2',
                    priority=1,
                    poll_interval=120,
                ),
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.3', priority=0
                ),
                OSPFNeighbor(ospf_interface=cls.p2mp, ip_address='10.2.0.2'),
            )
        )

    def test_filters(self):
        for params, expected in (
            ({'ospf_interface_id': [self.nbma.pk]}, 2),
            ({'instance_id': [self.instance.pk]}, 3),
            ({'device_id': [self.device.pk]}, 3),
            ({'ip_address': ['10.1.0.2']}, 1),
            ({'priority': [1]}, 1),
            ({'poll_interval': [120]}, 1),
            ({'q': 'p2mp'}, 1),
            ({'q': '10.1.0'}, 2),
        ):
            with self.subTest(params=params):
                self.assertEqual(
                    self.filterset(params, self.queryset).qs.count(), expected
                )


class OSPFNeighborViewTestCase(
    IPAddressFieldMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFNeighbor

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFNeighbor.objects.bulk_create(
            (
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.2', priority=1
                ),
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.3', priority=0
                ),
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.4', priority=0
                ),
            )
        )
        cls.form_data = {
            'ospf_interface': cls.nbma.pk,
            'ip_address': '10.1.0.9',
            'priority': 2,
            'poll_interval': 120,
        }
        cls.bulk_edit_data = {'description': 'A test description', 'priority': 3}

    def _get_base_url(self):
        return 'plugins:netbox_routing:ospfneighbor_{}'


class OSPFNeighborAPITestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFNeighbor
    view_namespace = 'plugins-api:netbox_routing'
    brief_fields = ['display', 'id', 'ip_address', 'ospf_interface', 'url']

    user_permissions = (
        'netbox_routing.view_ospfinterface',
        'netbox_routing.view_ospfinstance',
        'netbox_routing.view_ospfarea',
        'dcim.view_device',
        'dcim.view_interface',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFNeighbor.objects.bulk_create(
            (
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.2', priority=1
                ),
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.3', priority=0
                ),
                OSPFNeighbor(
                    ospf_interface=cls.nbma, ip_address='10.1.0.4', priority=0
                ),
            )
        )
        cls.create_data = [
            {
                'ospf_interface': cls.nbma.pk,
                'ip_address': '10.1.0.9',
                'priority': 2,
                'poll_interval': 120,
            },
        ]
