from django.test import TestCase
from django.urls import reverse
from ipam.models import ASN, RIR, VRF
from users.models import User
from utilities.testing import create_test_device

from netbox_routing_protocols.models import (
    BGPInstance,
    EIGRPAddressFamily,
    EIGRPRouter,
    ISISAddressFamily,
    ISISInstance,
    OSPFInstance,
    StaticRoute,
)

__all__ = ('DeviceRoutingTabTestCase',)


class DeviceRoutingTabTestCase(TestCase):
    """The device page has one Routing tab with a section per protocol (#528 UI)"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='routing', is_superuser=True)
        cls.device = create_test_device(name='Router 1')
        cls.other = create_test_device(name='Router 2')
        rir = RIR.objects.create(name='RIR')
        cls.asn = ASN.objects.create(rir=rir, asn=64512)
        cls.vrf = VRF.objects.create(name='Blue')
        route = StaticRoute.objects.create(
            prefix='198.51.100.0/24', next_hop_type='blackhole', name='drop'
        )
        route.devices.add(cls.device)
        OSPFInstance.objects.create(
            name='core', device=cls.device, router_id='10.0.0.1', address_family='ipv4'
        )
        isis = ISISInstance.objects.create(
            device=cls.device, process_tag='backbone', net='49.0001.0000.0000.0001.00'
        )
        ISISAddressFamily.objects.create(instance=isis, address_family='ipv4')
        eigrp = EIGRPRouter.objects.create(
            device=cls.device, mode='classic', pid=100, name='edge'
        )
        EIGRPAddressFamily.objects.create(router=eigrp, family=4)
        BGPInstance.objects.create(
            name='edge-bgp', device=cls.device, asn=cls.asn, router_id='10.0.0.1'
        )
        BGPInstance.objects.create(
            name='other-bgp', device=cls.other, asn=cls.asn, router_id='10.0.0.2'
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_the_routing_tab_shows_one_section_per_protocol(self):
        response = self.client.get(
            reverse('dcim:device', args=[self.device.pk]) + 'routing/'
        )
        self.assertEqual(response.status_code, 200)
        for title in (
            'Static routes',
            'OSPF instances',
            'IS-IS instances',
            'EIGRP routers',
            'BGP instances',
        ):
            self.assertContains(response, title)
        # the instances of this device, and not those of the other one
        self.assertContains(response, 'core')
        self.assertContains(response, 'backbone')
        self.assertContains(response, 'edge-bgp')
        self.assertNotContains(response, 'other-bgp')
        self.assertContains(response, '198.51.100.0/24')

    def test_the_device_column_is_left_out_of_the_sections(self):
        response = self.client.get(
            reverse('dcim:device', args=[self.device.pk]) + 'routing/'
        )
        self.assertEqual(response.context['sections'][0]['table'].exclude, ('devices',))
        for section in response.context['sections'][1:]:
            self.assertNotIn('device', section['table'].columns.names())

    def test_the_old_static_routes_tab_is_gone(self):
        response = self.client.get(f'/dcim/devices/{self.device.pk}/static_routes/')
        self.assertEqual(response.status_code, 404)
