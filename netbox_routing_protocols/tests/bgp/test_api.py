from dcim.models import Interface
from ipam.models import ASN, IPAddress, Prefix, RIR, VRF
from netaddr import IPNetwork
from utilities.testing import APIViewTestCases, create_test_device

from netbox_routing_protocols.models.bgp import *
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'BGPInstanceTestCase',
    'BGPAddressFamilyTestCase',
    'BGPPeerGroupTestCase',
    'BGPListenRangeTestCase',
    'BGPPeerTestCase',
    'BGPPeerAddressFamilyTestCase',
    'BFDProfileTestCase',
)

NAMESPACE = 'plugins-api:netbox_routing_protocols'


def _asns():
    rir = RIR.objects.create(name='ARIN')
    return [ASN.objects.create(rir=rir, asn=64512 + i) for i in range(4)]


class BGPInstanceTestCase(APIViewTestCases.APIViewTestCase):
    model = BGPInstance
    view_namespace = NAMESPACE
    brief_fields = ['asn', 'device', 'display', 'id', 'name', 'url', 'vrf']
    user_permissions = ('dcim.view_device', 'ipam.view_asn', 'ipam.view_vrf')
    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        asns = _asns()
        devices = [create_test_device(name=f'Device {i}') for i in range(1, 6)]
        cls.model.objects.bulk_create(
            [
                cls.model(name=f'Instance {i}', device=devices[i], asn=asns[0])
                for i in range(3)
            ]
        )
        vrf = VRF.objects.create(name='Test VRF')
        cls.create_data = [
            {
                'name': 'Instance X',
                'device': devices[3].pk,
                'asn': asns[0].pk,
                'router_id': '192.0.2.1',
                'asdot': True,
                'graceful_restart': True,
                'graceful_restart_time': 120,
                'cluster_id': '10.0.0.1',
                'confederation_identifier': asns[2].pk,
                'confederation_peers': [asns[3].pk],
            },
            {
                'name': 'Instance Y',
                'device': devices[3].pk,
                'vrf': vrf.pk,
                'asn': asns[1].pk,
            },
            {'name': 'Instance Z', 'device': devices[4].pk, 'asn': asns[1].pk},
        ]


class _BGPChildAPI:
    view_namespace = NAMESPACE
    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def _parents(cls):
        asns = _asns()
        instance = BGPInstance.objects.create(
            name='Instance', device=create_test_device(name='Device'), asn=asns[0]
        )
        return asns, instance


class BGPAddressFamilyTestCase(
    LeanCoreTestsMixin, _BGPChildAPI, APIViewTestCases.APIViewTestCase
):
    model = BGPAddressFamily
    brief_fields = ['address_family', 'display', 'id', 'instance', 'url']

    @classmethod
    def setUpTestData(cls):
        _asns, instance = cls._parents()
        cls.model.objects.bulk_create(
            [
                cls.model(instance=instance, address_family=af)
                for af in ('ipv4-unicast', 'ipv6-unicast', 'vpnv4-unicast')
            ]
        )
        cls.create_data = [
            {
                'instance': instance.pk,
                'address_family': 'ipv4-multicast',
                'maximum_paths': 4,
                'default_metric': 4294967295,
                'additional_paths_send': True,
            },
            {'instance': instance.pk, 'address_family': 'l2vpn-evpn'},
        ]


class BGPPeerGroupTestCase(
    LeanCoreTestsMixin, _BGPChildAPI, APIViewTestCases.APIViewTestCase
):
    model = BGPPeerGroup
    brief_fields = ['display', 'id', 'instance', 'name', 'url']

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        cls.model.objects.bulk_create(
            [cls.model(name=f'Group {i}', instance=instance) for i in range(3)]
        )
        cls.create_data = [
            {
                'name': f'Group {i}',
                'instance': instance.pk,
                'remote_as': asns[1].pk,
                'hold_time': 90,
                'keepalive': 30,
            }
            for i in range(4, 6)
        ]


class BGPListenRangeTestCase(
    LeanCoreTestsMixin, _BGPChildAPI, APIViewTestCases.APIViewTestCase
):
    model = BGPListenRange
    brief_fields = ['display', 'id', 'peer_group', 'prefix', 'url']

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asns[1]
        )
        prefixes = [Prefix.objects.create(prefix=f'10.{i}.0.0/24') for i in range(1, 6)]
        cls.model.objects.bulk_create(
            [cls.model(peer_group=group, prefix=prefixes[i]) for i in range(3)]
        )
        cls.create_data = [
            {'peer_group': group.pk, 'prefix': prefixes[3].pk},
            {'peer_group': group.pk, 'prefix': prefixes[4].pk},
        ]


class BGPPeerTestCase(
    LeanCoreTestsMixin, _BGPChildAPI, APIViewTestCases.APIViewTestCase
):
    model = BGPPeer
    brief_fields = ['display', 'id', 'instance', 'name', 'peer', 'url']

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        addresses = [
            IPAddress.objects.create(address=IPNetwork(f'10.0.0.{i}/24'))
            for i in range(1, 7)
        ]
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asns[1]
        )
        cls.model.objects.bulk_create(
            [
                cls.model(instance=instance, peer=addresses[i], remote_as=asns[1])
                for i in range(3)
            ]
        )
        cls.create_data = [
            {
                'instance': instance.pk,
                'peer': addresses[3].pk,
                'peer_group': group.pk,
                'status': 'planned',
            },
            {
                'instance': instance.pk,
                'interface': Interface.objects.create(
                    device=instance.device, name='eth0', type='1000base-t'
                ).pk,
                'remote_as': asns[2].pk,
                'extended_nexthop': True,
                'passphrase': 'secret',
                'show_md5': True,
            },
            {
                'instance': instance.pk,
                'peer': addresses[4].pk,
                'source': addresses[5].pk,
                'remote_as': asns[2].pk,
                'ttl_security_hops': 1,
                'passive': True,
            },
        ]


class BGPPeerAddressFamilyTestCase(
    LeanCoreTestsMixin, _BGPChildAPI, APIViewTestCases.APIViewTestCase
):
    model = BGPPeerAddressFamily
    brief_fields = ['address_family', 'display', 'id', 'peer', 'peer_group', 'url']

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        afs = [
            BGPAddressFamily.objects.create(instance=instance, address_family=af)
            for af in ('ipv4-unicast', 'ipv6-unicast', 'vpnv4-unicast', 'l2vpn-evpn')
        ]
        peer = BGPPeer.objects.create(
            instance=instance,
            peer=IPAddress.objects.create(address=IPNetwork('10.0.0.1/24')),
            remote_as=asns[1],
        )
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asns[1]
        )
        cls.model.objects.bulk_create(
            [cls.model(peer=peer, address_family=afs[i]) for i in range(3)]
        )
        cls.create_data = [
            {
                'peer': peer.pk,
                'address_family': afs[3].pk,
                'enabled': True,
                'send_community': ['standard', 'large'],
                'maximum_prefix': 100,
                'maximum_prefix_action': 'restart',
                'maximum_prefix_restart': 30,
            },
            {'peer_group': group.pk, 'address_family': afs[0].pk},
        ]


class BFDProfileTestCase(LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase):
    model = BFDProfile
    view_namespace = NAMESPACE
    brief_fields = ['display', 'id', 'name', 'url']
    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.model.objects.bulk_create(
            [
                cls.model(
                    name=f'Test BFD Profile {i}',
                    min_rx_int=60,
                    min_tx_int=60,
                    multiplier=3,
                )
                for i in range(1, 4)
            ]
        )
        cls.create_data = [
            {
                'name': f'Test BFD Profile {i}',
                'min_rx_int': 60,
                'min_tx_int': 60,
                'multiplier': 3,
            }
            for i in range(4, 6)
        ]
