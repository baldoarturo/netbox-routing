from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from ipam.models import IPAddress
from netaddr import IPNetwork

from netbox_routing_protocols.choices.bgp import BGPAddressFamilyChoices
from netbox_routing_protocols.models import PrefixList, RoutePolicy
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
    'BGPRoutePolicyTestCase',
    'BGPGracefulRestartTestCase',
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

    def test_ttl_security_and_multihop_exclude_each_other(self):
        group = self.model(
            name='G', instance=self.bgp_instance, ebgp_multihop=5, ttl_security_hops=1
        )
        with self.assertRaises(ValidationError) as cm:
            group.full_clean()
        self.assertIn('ttl_security_hops', cm.exception.error_dict)
        group.ebgp_multihop = None
        group.full_clean()

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


class BGPGracefulRestartTestCase(BGPInstanceMixin, TestCase):
    def test_the_timers_need_graceful_restart(self):
        instance = self.bgp_instance
        instance.graceful_restart_time = 120
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn('graceful_restart_time', cm.exception.error_dict)
        instance.graceful_restart = True
        instance.full_clean()
        # 12 bits (RFC 4724)
        instance.graceful_restart_time = 4096
        with self.assertRaises(ValidationError) as cm:
            instance.full_clean()
        self.assertIn('graceful_restart_time', cm.exception.error_dict)

    def test_long_lived_needs_graceful_restart_on_the_instance(self):
        af = BGPAddressFamily(
            instance=self.bgp_instance,
            address_family='ipv4-unicast',
            long_lived_stale_time=3600,
        )
        with self.assertRaises(ValidationError) as cm:
            af.full_clean()
        self.assertIn('long_lived_stale_time', cm.exception.error_dict)
        self.bgp_instance.graceful_restart = True
        self.bgp_instance.save()
        af.full_clean()
        # 24 bits (RFC 9494)
        af.long_lived_stale_time = 16777216
        with self.assertRaises(ValidationError):
            af.full_clean()


class BGPRoutePolicyTestCase(BGPInstanceMixin, AddressesMixin, TestCase):
    """The most specific import or export policy wins (peer address family, group
    address family, peer, peer group, instance); RFC 8212 and the other options of
    the peer address family"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.policies = [RoutePolicy.objects.create(name=f'P{i}') for i in range(5)]
        cls.ipv4 = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv4-unicast'
        )
        cls.group = BGPPeerGroup.objects.create(
            name='G', instance=cls.bgp_instance, remote_as=cls.asns[1]
        )
        cls.peer = BGPPeer.objects.create(
            instance=cls.bgp_instance,
            peer=cls.peer_address,
            peer_group=cls.group,
        )
        cls.peer_af = BGPPeerAddressFamily.objects.create(
            peer=cls.peer, address_family=cls.ipv4
        )

    def _set(self, obj, policy):
        obj.import_policy = policy
        obj.save()

    def test_most_specific_wins(self):
        self.assertEqual(self.peer_af.effective_policy('import'), (None, None))
        self.assertIsNone(self.peer_af.effective_import_policy_display)

        self._set(self.bgp_instance, self.policies[0])
        self.assertEqual(
            self.peer_af.effective_policy('import'),
            (self.policies[0], self.bgp_instance),
        )
        self._set(self.group, self.policies[1])
        self.assertEqual(self.peer_af.effective_policy('import')[0], self.policies[1])
        self._set(self.peer, self.policies[2])
        self.assertEqual(self.peer_af.effective_policy('import')[0], self.policies[2])
        group_af = BGPPeerAddressFamily.objects.create(
            peer_group=self.group, address_family=self.ipv4
        )
        self._set(group_af, self.policies[3])
        self.assertEqual(
            self.peer_af.effective_policy('import'), (self.policies[3], group_af)
        )
        self._set(self.peer_af, self.policies[4])
        self.assertEqual(
            self.peer_af.effective_policy('import'), (self.policies[4], self.peer_af)
        )
        self.assertIn(
            'from BGP Peer Address Family', self.peer_af.effective_import_policy_display
        )
        # export is independent
        self.assertEqual(self.peer_af.effective_policy('export'), (None, None))

    def test_a_policy_in_use_cannot_be_deleted(self):
        self._set(self.peer, self.policies[0])
        with self.assertRaises(ProtectedError):
            self.policies[0].delete()

    def test_rfc_8212_only_for_ebgp_sessions_without_policy(self):
        # the group's AS is not the instance's: eBGP
        missing = self.peer.sessions_without_policy()
        self.assertEqual(
            {(af.pk, direction) for af, direction in missing},
            {(self.peer_af.pk, 'import'), (self.peer_af.pk, 'export')},
        )
        self._set(self.bgp_instance, self.policies[0])
        self.assertEqual(
            [direction for _af, direction in self.peer.sessions_without_policy()],
            ['export'],
        )
        self.peer_af.export_policy = self.policies[1]
        self.peer_af.save()
        self.assertEqual(self.peer.sessions_without_policy(), [])

    def test_rfc_8212_does_not_apply_to_ibgp_nor_disabled_families(self):
        self.group.remote_as = self.asn  # the AS of the instance: iBGP
        self.group.save()
        self.peer.refresh_from_db()
        self.assertEqual(self.peer.sessions_without_policy(), [])
        self.assertEqual(self.group.sessions_without_policy(), [])
        self.group.remote_as = self.asns[1]
        self.group.save()
        self.peer_af.enabled = False
        self.peer_af.save()
        self.assertEqual(self.peer.sessions_without_policy(), [])

    def test_a_group_family_counts_for_the_peers_of_the_group(self):
        group_af = BGPPeerAddressFamily.objects.create(
            peer_group=self.group,
            address_family=BGPAddressFamily.objects.create(
                instance=self.bgp_instance, address_family='ipv6-unicast'
            ),
        )
        families = {af.pk for af, _direction in self.peer.sessions_without_policy()}
        self.assertEqual(families, {self.peer_af.pk, group_af.pk})
        self.assertEqual(
            {af.pk for af, _d in self.group.sessions_without_policy()}, {group_af.pk}
        )

    def test_send_community_is_inherited_from_the_group(self):
        group_af = BGPPeerAddressFamily.objects.create(
            peer_group=self.group,
            address_family=self.ipv4,
            send_community=['standard', 'large'],
        )
        self.assertEqual(
            self.peer_af.effective('send_community'), ['standard', 'large']
        )
        self.peer_af.send_community = ['extended']
        self.assertEqual(self.peer_af.effective('send_community'), ['extended'])
        self.assertEqual(group_af.send_community_display, 'Standard, Large')
        self.peer_af.send_community = ['bogus']
        with self.assertRaises(ValidationError) as cm:
            self.peer_af.full_clean()
        self.assertIn('send_community', cm.exception.error_dict)

    def test_maximum_prefix_options(self):
        peer_af = self.peer_af
        # nothing else without the limit
        peer_af.maximum_prefix_warning = 80
        with self.assertRaises(ValidationError) as cm:
            peer_af.full_clean()
        self.assertIn('maximum_prefix_warning', cm.exception.error_dict)
        peer_af.maximum_prefix = 1000
        peer_af.full_clean()
        # the restart time goes with the restart action only
        peer_af.maximum_prefix_action = 'restart'
        with self.assertRaises(ValidationError) as cm:
            peer_af.full_clean()
        self.assertIn('maximum_prefix_restart', cm.exception.error_dict)
        peer_af.maximum_prefix_restart = 30
        peer_af.full_clean()
        peer_af.maximum_prefix_action = 'stop'
        with self.assertRaises(ValidationError) as cm:
            peer_af.full_clean()
        self.assertIn('maximum_prefix_restart', cm.exception.error_dict)
        peer_af.maximum_prefix_restart = None
        peer_af.full_clean()
        peer_af.maximum_prefix_warning = 101
        with self.assertRaises(ValidationError):
            peer_af.full_clean()
