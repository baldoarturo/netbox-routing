from django.test import TestCase
from dcim.models import Interface
from ipam.models import ASN, IPAddress, Prefix, RIR, VRF

from netbox_routing_plugin.forms.bulk_import import (
    BGPAddressFamilyImportForm,
    BGPInstanceImportForm,
    BGPListenRangeImportForm,
    BGPPeerAddressFamilyImportForm,
    BGPPeerGroupImportForm,
    BGPPeerImportForm,
)
from netbox_routing_plugin.models import (
    BGPAddressFamily,
    BGPInstance,
    BGPPeer,
    BGPPeerAddressFamily,
    BGPPeerGroup,
)
from utilities.testing import create_test_device

__all__ = ('BGPBulkImportTestCase',)


class BGPBulkImportTestCase(TestCase):
    """The CSV import of the BGP objects: each row names its instance by device and VRF,
    and the names and addresses are resolved inside that instance (#527)"""

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='RIR')
        cls.asn = ASN.objects.create(rir=rir, asn=64512)
        cls.remote = ASN.objects.create(rir=rir, asn=64513)
        cls.device = create_test_device(name='Router')
        cls.other = create_test_device(name='Other')
        cls.vrf = VRF.objects.create(name='Blue')
        cls.instance = BGPInstance.objects.create(
            name='BGP', device=cls.device, asn=cls.asn
        )
        cls.vrf_instance = BGPInstance.objects.create(
            name='BGP Blue', device=cls.device, vrf=cls.vrf, asn=cls.asn
        )
        cls.af = BGPAddressFamily.objects.create(
            instance=cls.instance, address_family='ipv4-unicast'
        )
        cls.group = BGPPeerGroup.objects.create(
            name='Customers', instance=cls.instance, remote_as=cls.remote
        )
        cls.interface = Interface.objects.create(
            device=cls.device, name='eth0', type='1000base-t'
        )
        Prefix.objects.create(prefix='10.9.0.0/24', vrf=cls.vrf)
        IPAddress.objects.create(address='10.1.1.1/24', vrf=cls.vrf)
        IPAddress.objects.create(address='10.1.1.2/24')

    def _form(self, form_class, data):
        form = form_class(data=data)
        return form

    def test_instance(self):
        form = self._form(
            BGPInstanceImportForm,
            {
                'name': 'New',
                'device': self.other.name,
                'asn': 64512,
                'router_id': '1.1.1.1',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(
            BGPInstance.objects.filter(name='New', device=self.other).exists()
        )

    def test_address_family_in_the_instance_of_the_device_and_vrf(self):
        form = self._form(
            BGPAddressFamilyImportForm,
            {
                'device': self.device.name,
                'vrf': self.vrf.name,
                'address_family': 'ipv6-unicast',
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(
            BGPAddressFamily.objects.filter(
                instance=self.vrf_instance, address_family='ipv6-unicast'
            ).exists()
        )
        # the same family twice in the instance is an error
        form = self._form(
            BGPAddressFamilyImportForm,
            {'device': self.device.name, 'address_family': 'ipv4-unicast'},
        )
        self.assertFalse(form.is_valid())

    def test_no_instance_on_the_device_in_the_vrf(self):
        form = self._form(
            BGPAddressFamilyImportForm,
            {'device': self.other.name, 'address_family': 'ipv4-unicast'},
        )
        self.assertFalse(form.is_valid())

    def test_peer_group(self):
        form = self._form(
            BGPPeerGroupImportForm,
            {
                'name': 'Second',
                'device': self.device.name,
                'remote_as': 64513,
                'hold_time': 90,
                'keepalive': 30,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(
            BGPPeerGroup.objects.filter(name='Second', instance=self.instance).exists()
        )

    def test_peer_by_address_in_the_vrf(self):
        form = self._form(
            BGPPeerImportForm,
            {
                'device': self.device.name,
                'vrf': self.vrf.name,
                'peer': '10.1.1.2/24',
                'remote_as': 64513,
            },
        )
        # 10.1.1.2 is in the global table, not in the VRF
        self.assertFalse(form.is_valid())
        self.assertIn('peer', form.errors)
        form = self._form(
            BGPPeerImportForm,
            {
                'device': self.device.name,
                'vrf': self.vrf.name,
                'peer': '10.1.1.1/24',
                'remote_as': 64513,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(BGPPeer.objects.filter(instance=self.vrf_instance).exists())

    def test_peer_address_that_is_not_an_address(self):
        form = self._form(
            BGPPeerImportForm,
            {'device': self.device.name, 'peer': 'not-an-address', 'remote_as': 64513},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('peer', form.errors)

    def test_unnumbered_peer_on_an_interface_of_the_device(self):
        form = self._form(
            BGPPeerImportForm,
            {'device': self.device.name, 'interface': 'eth0', 'remote_as': 64513},
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(BGPPeer.objects.filter(interface=self.interface).exists())
        # an address and an interface together are not allowed
        form = self._form(
            BGPPeerImportForm,
            {
                'device': self.device.name,
                'peer': '10.1.1.1/24',
                'interface': 'eth0',
                'remote_as': 64513,
            },
        )
        self.assertFalse(form.is_valid())

    def test_listen_range_in_the_group_and_the_vrf(self):
        form = self._form(
            BGPListenRangeImportForm,
            {
                'device': self.device.name,
                'peer_group': 'Customers',
                'prefix': '10.9.0.0/24',
            },
        )
        # the prefix is in another VRF than the instance (global)
        self.assertFalse(form.is_valid())
        form = self._form(
            BGPListenRangeImportForm,
            {
                'device': self.device.name,
                'vrf': self.vrf.name,
                'peer_group': 'Customers',
                'prefix': '10.9.0.0/24',
            },
        )
        self.assertFalse(form.is_valid())  # the group is in the global instance
        form = self._form(
            BGPListenRangeImportForm,
            {'device': self.device.name, 'peer_group': 'Nope', 'prefix': '10.9.0.0/24'},
        )
        self.assertFalse(form.is_valid())
        self.assertIn('peer_group', form.errors)

    def test_peer_address_family_of_a_group_or_a_peer(self):
        form = self._form(
            BGPPeerAddressFamilyImportForm,
            {
                'device': self.device.name,
                'peer_group': 'Customers',
                'address_family': 'ipv4-unicast',
                'enabled': True,
                'import_policy': None,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(
            BGPPeerAddressFamily.objects.filter(
                peer_group=self.group, address_family=self.af
            ).exists()
        )
        form = self._form(
            BGPPeerAddressFamilyImportForm,
            {'device': self.device.name, 'address_family': 'ipv4-unicast'},
        )
        self.assertFalse(form.is_valid())
