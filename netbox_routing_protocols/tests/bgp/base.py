from netbox_routing_protocols.models import (
    BGPInstance,
    BGPAddressFamily,
    BGPPeerGroup,
    BGPPeer,
)
from netbox_routing_protocols.tests.base import ASNMixin, AddressesMixin
from utilities.testing import create_test_device

__all__ = (
    'BGPInstanceMixin',
    'BGPAddressFamilyMixin',
    'BGPPeerMixin',
    'create_peer_address_family',
)


class BGPInstanceMixin(ASNMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.device = create_test_device(name='BGP Device')
        cls.bgp_instance = BGPInstance.objects.create(
            name='BGP Instance', device=cls.device, asn=cls.asn
        )


class BGPAddressFamilyMixin(BGPInstanceMixin):
    afs = (
        'ipv4-unicast',
        'ipv6-unicast',
        'vpnv4-unicast',
        'vpnv6-unicast',
        'l2vpn-vpls',
        'l2vpn-evpn',
        'ipv4-multicast',
        'ipv6-multicast',
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for af in cls.afs:
            BGPAddressFamily.objects.create(
                instance=cls.bgp_instance, address_family=af
            )
        cls.af = BGPAddressFamily.objects.first()


class BGPPeerMixin(BGPInstanceMixin, AddressesMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.peer_group = BGPPeerGroup.objects.create(
            name='Group', instance=cls.bgp_instance, remote_as=cls.asns[1]
        )
        cls.peer = BGPPeer.objects.create(
            name='BGP Peer',
            instance=cls.bgp_instance,
            peer=cls.peer_address,
            remote_as=cls.asns[1],
        )


def create_peer_address_family(**fields):
    """A BGP peer address family (with its device, instance, peer group and address
    family) to give a prefix list or a route policy something that uses it"""
    from ipam.models import ASN, RIR

    from netbox_routing_protocols.models import BGPPeerAddressFamily

    count = BGPInstance.objects.count() + 1
    rir = RIR.objects.get_or_create(name='Test RIR', slug='test-rir')[0]
    instance = BGPInstance.objects.create(
        name=f'Instance {count}',
        device=create_test_device(name=f'BGP device {count}'),
        asn=ASN.objects.create(asn=64000 + count, rir=rir),
    )
    return BGPPeerAddressFamily.objects.create(
        peer_group=BGPPeerGroup.objects.create(name='Group', instance=instance),
        address_family=BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv4-unicast'
        ),
        **fields,
    )
