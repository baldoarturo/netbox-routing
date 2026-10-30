from netbox.search import SearchIndex, register_search
from netbox_routing_protocols.models.bgp import *


@register_search
class BGPInstanceIndex(SearchIndex):
    model = BGPInstance
    fields = (
        ('name', 100),
        ('router_id', 200),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('device', 'vrf', 'asn')


@register_search
class BGPAddressFamilyIndex(SearchIndex):
    model = BGPAddressFamily
    fields = (
        ('address_family', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'address_family')


@register_search
class BGPPeerGroupIndex(SearchIndex):
    model = BGPPeerGroup
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'remote_as')


@register_search
class BGPListenRangeIndex(SearchIndex):
    model = BGPListenRange
    fields = (
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('peer_group', 'prefix')


@register_search
class BGPPeerIndex(SearchIndex):
    model = BGPPeer
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'peer', 'interface', 'peer_group', 'remote_as')


@register_search
class BGPPeerAddressFamilyIndex(SearchIndex):
    model = BGPPeerAddressFamily
    fields = (
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('peer', 'peer_group', 'address_family')


@register_search
class BFDProfileIndex(SearchIndex):
    model = BFDProfile
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('name',)
