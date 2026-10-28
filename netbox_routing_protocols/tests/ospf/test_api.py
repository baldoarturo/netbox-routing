from dcim.models import Interface
from ipam.models import VRF
from utilities.testing import APIViewTestCases, create_test_device

from netbox_routing_protocols.models import OSPFInstance, OSPFArea, OSPFInterface
from netbox_routing_protocols.tests.base import IPAddressFieldMixin

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFInstance
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = [
        'device',
        'display',
        'id',
        'name',
        'process_id',
        'router_id',
        'url',
        'vrf',
    ]

    user_permissions = ('dcim.view_device',)

    bulk_update_data = {'description': "A test description"}

    @classmethod
    def setUpTestData(cls):
        vrf = VRF.objects.create(name='Test VRF')
        device = create_test_device(name='Test Device')

        data = (
            cls.model(
                name='Instance 1',
                device=device,
                router_id='1.1.1.1',
                process_id=1,
                vrf=None,
            ),
            cls.model(
                name='Instance 2',
                device=device,
                router_id='2.2.2.2',
                process_id=2,
                vrf=vrf,
            ),
            cls.model(
                name='Instance 3',
                device=device,
                router_id='3.3.3.3',
                process_id=3,
                vrf=None,
            ),
        )
        cls.model.objects.bulk_create(data)

        cls.create_data = [
            {
                'name': 'Instance X',
                'device': device.pk,
                'router_id': '4.4.4.4',
                'process_id': 4,
                'vrf': vrf.pk,
                'graceful_restart': 'planned-unplanned',
                'graceful_restart_period': 300,
                'spf_initial_delay': 100,
                'rfc1583_compatibility': False,
                'max_lsa': 5000,
                'reference_bandwidth': 10000,
                'maximum_paths': 8,
                'distance_intra_area': 100,
                'distance_inter_area': 110,
                'distance_external': 150,
            },
        ]


class OSPFAreaTestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFArea
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = [
        'area_id',
        'area_type',
        'display',
        'id',
        'instance',
        'url',
    ]

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'dcim.view_device',
    )

    bulk_update_data = {'description': "A test description"}

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Test Device')
        instance = OSPFInstance.objects.create(
            name='Instance 1', device=device, router_id='1.1.1.1', process_id=1
        )
        data = (
            cls.model(instance=instance, area_id='1', area_type='stub'),
            cls.model(instance=instance, area_id='2', area_type='stub'),
            cls.model(instance=instance, area_id='3', area_type='stub'),
        )
        cls.model.objects.bulk_create(data)

        cls.create_data = [
            {
                'instance': instance.pk,
                'area_id': '4',
                'area_type': 'stub',
            },
        ]


class OSPFInterfaceTestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFInterface
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = [
        'area',
        'display',
        'id',
        'instance',
        'interface',
        'network_type',
        'passive',
        'url',
    ]

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'netbox_routing_protocols.view_ospfarea',
        'dcim.view_device',
        'dcim.view_interface',
    )

    bulk_update_data = {'description': "A test description"}

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Test Device')
        instance = OSPFInstance.objects.create(
            name='Instance 1', device=device, router_id='1.1.1.1', process_id=1
        )
        area = OSPFArea.objects.create(instance=instance, area_id='0')

        interfaces = (
            Interface(device=device, name='Interface 1', type='virtual'),
            Interface(device=device, name='Interface 2', type='virtual'),
            Interface(device=device, name='Interface 3', type='virtual'),
            Interface(device=device, name='Interface 4', type='virtual'),
        )
        Interface.objects.bulk_create(interfaces)

        data = (
            cls.model(
                instance=instance, area=area, interface=interfaces[0], passive=True
            ),
            cls.model(
                instance=instance, area=area, interface=interfaces[1], passive=False
            ),
            cls.model(
                instance=instance,
                area=area,
                interface=interfaces[2],
            ),
        )
        cls.model.objects.bulk_create(data)

        cls.create_data = [
            {
                'instance': instance.pk,
                'area': area.pk,
                'interface': interfaces[3].pk,
                'passive': True,
                'priority': 2,
                'authentication': 'message-digest',
                'authentication_key_id': 1,
                'passphrase': 'test-password',
                'show_md5': True,
                'bfd': True,
            },
        ]

    def test_the_authentication_in_use_comes_from_the_area(self):
        self.add_permissions('netbox_routing_protocols.view_ospfinterface')
        obj = self.model.objects.filter(authentication__isnull=True).first()
        OSPFArea.objects.filter(pk=obj.area_id).update(
            authentication='message-digest',
            authentication_key_id=1,
            passphrase='password',
        )
        response = self.client.get(self._get_detail_url(obj), **self.header)
        self.assertEqual(response.data['effective_authentication'], 'message-digest')
        self.assertEqual(response.data['authentication_source'], 'area')

    def test_mtu_comes_from_the_device_interface(self):
        self.add_permissions('netbox_routing_protocols.view_ospfinterface')
        obj = self.model.objects.first()
        Interface.objects.filter(pk=obj.interface_id).update(mtu=9000)
        response = self.client.get(self._get_detail_url(obj), **self.header)
        self.assertEqual(response.data['mtu'], 9000)
