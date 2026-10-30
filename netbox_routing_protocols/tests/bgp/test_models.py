from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from ipam.models import IPAddress
from netaddr import IPNetwork

from netbox_routing_protocols.choices.bgp import BGPAddressFamilyChoices
from netbox_routing_protocols.models import PrefixList
from netbox_routing_protocols.models.bgp import *
from netbox_routing_protocols.tests.base import *
from netbox_routing_protocols.tests.bgp.base import *
from utilities.testing import create_test_device

__all__ = (
    'BGPInstanceTestCase',
    'BGPAddressFamilyTestCase',
    'BGPPeerGroupTestCase',
    'BGPPeerTestCase',
    'BGPPeerAddressFamilyTestCase',
    'BFDProfileTestCase',
    'BGPChoicesTestCase',
)


class BGPChoicesTestCase(TestCase):
    def test_address_families_are_listed_once(self):
        values = [value for value, _label in BGPAddressFamilyChoices.CHOICES]
        self.assertEqual(len(values), len(set(values)))
        for constant in (
            'VPNV4_UNICAST',
            'VPNV4_MULTICAST',
            'L2VPNEVPN',
        ):
            self.assertIn(getattr(BGPAddressFamilyChoices, constant), values)


class BGPInstanceTestCase(BGPInstanceMixin, VRFMixin, TestCase):
    model = BGPInstance

    def test_one_instance_per_device_and_vrf(self):
        duplicate = self.model(name='Other', device=self.device, asn=self.asn)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            duplicate.save()

        # another VRF, or another device, is fine
        self.model(
            name='In a VRF', device=self.device, vrf=self.vrf, asn=self.asn
        ).full_clean()
        self.model(
            name='Other device', device=create_test_device(name='D2'), asn=self.asn
        ).full_clean()

    def test_router_id_cannot_be_zero(self):
        instance = self.model(
            name='X',
            device=create_test_device(name='D3'),
            asn=self.asn,
            router_id='0.0.0.0',
        )
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn('router_id', cm.exception.error_dict)
        instance.router_id = '192.0.2.1'
        instance.full_clean()


class BGPAddressFamilyTestCase(BGPInstanceMixin, TestCase):
    model = BGPAddressFamily

    def test_unique_per_instance(self):
        self.model.objects.create(
            instance=self.bgp_instance, address_family='ipv4-unicast'
        )
        duplicate = self.model(
            instance=self.bgp_instance, address_family='ipv4-unicast'
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_distance_limits(self):
        af = self.model(
            instance=self.bgp_instance, address_family='ipv4-unicast', distance_ebgp=0
        )
        with self.assertRaises(ValidationError) as cm:
            af.full_clean()
        self.assertIn('distance_ebgp', cm.exception.error_dict)


class BGPPeerGroupTestCase(BGPInstanceMixin, TestCase):
    model = BGPPeerGroup

    def test_unique_name_per_instance(self):
        self.model.objects.create(name='G', instance=self.bgp_instance)
        with self.assertRaises(ValidationError):
            self.model(name='G', instance=self.bgp_instance).full_clean()

    def test_timers(self):
        group = self.model(name='G', instance=self.bgp_instance)
        for hold in (1, 2):
            group.hold_time = hold
            with self.assertRaises(ValidationError) as cm:
                group.full_clean()
            self.assertIn('hold_time', cm.exception.error_dict)
        # zero or at least 3 seconds
        for hold in (0, 3, 90):
            group.hold_time = hold
            group.full_clean()
        # keepalive: at most a third of the hold time
        group.hold_time, group.keepalive = 90, 30
        group.full_clean()
        group.keepalive = 31
        with self.assertRaises(ValidationError) as cm:
            group.full_clean()
        self.assertIn('keepalive', cm.exception.error_dict)
        group.hold_time = 0
        group.keepalive = 1
        with self.assertRaises(ValidationError):
            group.full_clean()


class BGPPeerTestCase(BGPInstanceMixin, AddressesMixin, VRFMixin, TestCase):
    model = BGPPeer

    def _peer(self, **kwargs):
        kwargs.setdefault('instance', self.bgp_instance)
        kwargs.setdefault('peer', self.peer_address)
        return self.model(**kwargs)

    def test_needs_a_remote_as(self):
        with self.assertRaises(ValidationError) as cm:
            self._peer().full_clean()
        self.assertIn('remote_as', cm.exception.error_dict)
        self._peer(remote_as=self.asns[1]).full_clean()

    def test_remote_as_from_the_group(self):
        group = BGPPeerGroup.objects.create(
            name='G', instance=self.bgp_instance, remote_as=self.asns[1], hold_time=90
        )
        peer = self._peer(peer_group=group)
        peer.full_clean()
        self.assertEqual(peer.effective('remote_as'), self.asns[1])
        self.assertEqual(peer.effective('hold_time'), 90)
        peer.hold_time = 30
        self.assertEqual(peer.effective('hold_time'), 30)

    def test_group_of_another_instance(self):
        other = BGPInstance.objects.create(
            name='Other', device=create_test_device(name='D2'), asn=self.asn
        )
        group = BGPPeerGroup.objects.create(
            name='G', instance=other, remote_as=self.asns[1]
        )
        with self.assertRaises(ValidationError) as cm:
            self._peer(peer_group=group).full_clean()
        self.assertIn('peer_group', cm.exception.error_dict)

    def test_ibgp_or_ebgp(self):
        self.assertTrue(self._peer(remote_as=self.asn).is_ibgp)
        self.assertFalse(self._peer(remote_as=self.asns[1]).is_ibgp)
        self.assertIsNone(self._peer().is_ibgp)

    def test_one_session_per_address(self):
        self._peer(remote_as=self.asns[1]).save()
        duplicate = self._peer(remote_as=self.asns[1], name='Another name')
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError):
            duplicate.save()

    def test_addresses_in_the_vrf_of_the_instance(self):
        in_vrf = IPAddress.objects.create(
            address=IPNetwork('10.9.9.9/24'), vrf=self.vrf
        )
        with self.assertRaises(ValidationError) as cm:
            self._peer(peer=in_vrf, remote_as=self.asns[1]).full_clean()
        self.assertIn('peer', cm.exception.error_dict)
        with self.assertRaises(ValidationError) as cm:
            self._peer(source=in_vrf, remote_as=self.asns[1]).full_clean()
        self.assertIn('source', cm.exception.error_dict)


class BGPPeerAddressFamilyTestCase(BGPPeerMixin, TestCase):
    model = BGPPeerAddressFamily

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ipv4 = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv4-unicast'
        )
        cls.evpn = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='l2vpn-evpn'
        )

    def test_peer_or_peer_group(self):
        for kwargs in (
            {},
            {'peer': self.peer, 'peer_group': self.peer_group},
        ):
            with self.assertRaises(ValidationError):
                self.model(address_family=self.ipv4, **kwargs).full_clean()
        self.model(address_family=self.ipv4, peer=self.peer).full_clean()
        self.model(address_family=self.ipv4, peer_group=self.peer_group).full_clean()

    def test_unique(self):
        self.model.objects.create(address_family=self.ipv4, peer=self.peer)
        with self.assertRaises(ValidationError):
            self.model(address_family=self.ipv4, peer=self.peer).full_clean()
        self.model.objects.create(address_family=self.ipv4, peer_group=self.peer_group)
        with self.assertRaises(ValidationError):
            self.model(
                address_family=self.ipv4, peer_group=self.peer_group
            ).full_clean()

    def test_address_family_of_another_instance(self):
        other = BGPInstance.objects.create(
            name='Other', device=create_test_device(name='D2'), asn=self.asn
        )
        af = BGPAddressFamily.objects.create(
            instance=other, address_family='ipv4-unicast'
        )
        with self.assertRaises(ValidationError) as cm:
            self.model(address_family=af, peer=self.peer).full_clean()
        self.assertIn('address_family', cm.exception.error_dict)

    def test_prefix_list_family(self):
        v4 = PrefixList.objects.create(name='v4', family=4)
        v6 = PrefixList.objects.create(name='v6', family=6)
        self.model(
            address_family=self.ipv4, peer=self.peer, prefixlist_in=v4
        ).full_clean()
        for field in ('prefixlist_in', 'prefixlist_out'):
            with self.assertRaises(ValidationError) as cm:
                self.model(
                    address_family=self.ipv4, peer=self.peer, **{field: v6}
                ).full_clean()
            self.assertIn(field, cm.exception.error_dict)
        # EVPN does not carry IP prefixes
        with self.assertRaises(ValidationError) as cm:
            self.model(
                address_family=self.evpn, peer=self.peer, prefixlist_in=v4
            ).full_clean()
        self.assertIn('prefixlist_in', cm.exception.error_dict)


class BFDProfileTestCase(TestCase):
    model = BFDProfile

    def test_model(self):
        instance = self.model(
            name='Test BFD Profile X', min_rx_int=60, min_tx_int=60, multiplier=3
        )
        instance.full_clean()
        instance.save()
        self.assertEqual(str(instance), instance.name)

    def test_unique_name(self):
        data = {
            'name': 'Test BFD Profile X',
            'min_rx_int': 60,
            'min_tx_int': 60,
            'multiplier': 3,
        }
        self.model.objects.create(**data)
        with self.assertRaises(ValidationError):
            self.model(**data).full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.model(**data).save()
