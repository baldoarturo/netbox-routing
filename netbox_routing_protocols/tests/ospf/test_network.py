from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from dcim.models import Interface
from ipam.models import IPAddress
from utilities.testing import (
    APIViewTestCases,
    ViewTestCases,
    create_test_device,
)

from netbox_routing_protocols.filtersets import OSPFNetworkFilterSet
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
)
from netbox_routing_protocols.tests.base import IPAddressFieldMixin, LeanCoreTestsMixin

__all__ = (
    'OSPFNetworkModelTestCase',
    'OSPFNetworkFilterSetTestCase',
    'OSPFNetworkViewTestCase',
    'OSPFNetworkAPITestCase',
)


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.interfaces = (
        Interface(device=cls.device, name='Interface 1', type='virtual'),
        Interface(device=cls.device, name='Interface 2', type='virtual'),
    )
    Interface.objects.bulk_create(cls.interfaces)
    cls.interfaces = list(Interface.objects.order_by('name'))
    instance = OSPFInstance.objects.create(
        name='Instance 1', device=cls.device, router_id='1.1.1.1'
    )
    area = OSPFArea.objects.create(instance=instance, area_id='0')
    cls.ospf_interfaces = [
        OSPFInterface.objects.create(instance=instance, area=area, interface=interface)
        for interface in cls.interfaces
    ]
    cls.addresses = [
        IPAddress.objects.create(
            address='10.0.0.1/24', assigned_object=cls.interfaces[0]
        ),
        IPAddress.objects.create(
            address='10.0.1.1/24', assigned_object=cls.interfaces[0]
        ),
        IPAddress.objects.create(
            address='10.0.2.1/24', assigned_object=cls.interfaces[1]
        ),
        IPAddress.objects.create(
            address='10.0.3.1/24', assigned_object=cls.interfaces[1]
        ),
        IPAddress.objects.create(address='2001:db8::1/64', assigned_object=None),
    ]


class OSPFNetworkModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def test_subnet_is_the_network_of_the_ip_address(self):
        network = OSPFNetwork.objects.create(
            ospf_interface=self.ospf_interfaces[0], ip_address=self.addresses[0]
        )
        self.assertEqual(str(network.subnet), '10.0.0.0/24')
        self.assertEqual(str(network), '10.0.0.0/24')

    def test_ip_address_must_be_assigned_to_the_interface(self):
        network = OSPFNetwork(
            ospf_interface=self.ospf_interfaces[0], ip_address=self.addresses[2]
        )
        with self.assertRaises(ValidationError) as cm:
            network.full_clean()
        self.assertIn('ip_address', cm.exception.error_dict)

    def test_ipv6_is_rejected(self):
        self.addresses[4].assigned_object = self.interfaces[0]
        self.addresses[4].save()
        network = OSPFNetwork(
            ospf_interface=self.ospf_interfaces[0], ip_address=self.addresses[4]
        )
        with self.assertRaises(ValidationError) as cm:
            network.full_clean()
        self.assertIn('ip_address', cm.exception.error_dict)

    def test_several_networks_per_interface_but_not_duplicated(self):
        for address in self.addresses[:2]:
            OSPFNetwork.objects.create(
                ospf_interface=self.ospf_interfaces[0], ip_address=address
            )
        self.assertEqual(self.ospf_interfaces[0].networks.count(), 2)
        with self.assertRaises(IntegrityError):
            OSPFNetwork.objects.create(
                ospf_interface=self.ospf_interfaces[0], ip_address=self.addresses[0]
            )

    def test_deleting_the_ip_address_removes_the_network(self):
        OSPFNetwork.objects.create(
            ospf_interface=self.ospf_interfaces[0], ip_address=self.addresses[0]
        )
        self.addresses[0].delete()
        self.assertFalse(OSPFNetwork.objects.exists())


class OSPFNetworkFilterSetTestCase(TestCase):
    queryset = OSPFNetwork.objects.all()
    filterset = OSPFNetworkFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        for interface, address in zip((0, 0, 1, 1), cls.addresses[:4]):
            OSPFNetwork.objects.create(
                ospf_interface=cls.ospf_interfaces[interface], ip_address=address
            )

    def test_ospf_interface(self):
        params = {'ospf_interface_id': [self.ospf_interfaces[0].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_ip_address(self):
        params = {'ip_address_id': [self.addresses[0].pk, self.addresses[3].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_interface_and_device(self):
        params = {'interface_id': [self.interfaces[1].pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
        params = {'device_id': [self.device.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 4)

    def test_q(self):
        params = {'q': 'Interface 2'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)


class OSPFNetworkViewTestCase(
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
    model = OSPFNetwork

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        for address in cls.addresses[:3]:
            OSPFNetwork.objects.create(
                ospf_interface=cls.ospf_interfaces[
                    0 if address.assigned_object == cls.interfaces[0] else 1
                ],
                ip_address=address,
            )

        cls.form_data = {
            'ospf_interface': cls.ospf_interfaces[1].pk,
            'ip_address': cls.addresses[3].pk,
            'description': 'A network',
        }
        cls.bulk_edit_data = {'description': 'A test description'}

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfnetwork_{}'


class OSPFNetworkAPITestCase(
    LeanCoreTestsMixin, IPAddressFieldMixin, APIViewTestCases.APIViewTestCase
):
    model = OSPFNetwork
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['display', 'id', 'ip_address', 'ospf_interface', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfinterface',
        'netbox_routing_protocols.view_ospfinstance',
        'netbox_routing_protocols.view_ospfarea',
        'dcim.view_device',
        'dcim.view_interface',
        'ipam.view_ipaddress',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        for interface, address in zip((0, 0, 1), cls.addresses[:3]):
            OSPFNetwork.objects.create(
                ospf_interface=cls.ospf_interfaces[interface], ip_address=address
            )
        cls.create_data = [
            {
                'ospf_interface': cls.ospf_interfaces[1].pk,
                'ip_address': cls.addresses[3].pk,
            },
        ]

    def test_subnet_is_exposed(self):
        self.add_permissions('netbox_routing_protocols.view_ospfnetwork')
        obj = self.model.objects.get(ip_address=self.addresses[0])
        response = self.client.get(self._get_detail_url(obj), **self.header)
        self.assertEqual(response.data['subnet'], '10.0.0.0/24')
