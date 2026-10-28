from netbox.search import SearchIndex, register_search
from netbox_routing_protocols.models.ospf import (
    OSPFArea,
    OSPFAreaRange,
    OSPFInstance,
    OSPFInterface,
    OSPFNeighbor,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFSummaryAddress,
    OSPFVirtualLink,
)

__all__ = (
    'OSPFInstanceIndex',
    'OSPFAreaIndex',
    'OSPFInterfaceIndex',
    'OSPFNetworkIndex',
    'OSPFRedistributionIndex',
    'OSPFVirtualLinkIndex',
    'OSPFSummaryAddressIndex',
    'OSPFNeighborIndex',
    'OSPFAreaRangeIndex',
)


@register_search
class OSPFInstanceIndex(SearchIndex):
    model = OSPFInstance
    fields = (
        ('name', 100),
        ('router_id', 200),
        ('process_id', 300),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('process_id', 'device', 'vrf')


@register_search
class OSPFAreaIndex(SearchIndex):
    model = OSPFArea
    fields = (
        ('area_id', 100),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'area_type')


@register_search
class OSPFInterfaceIndex(SearchIndex):
    model = OSPFInterface
    fields = (
        ('key_chain', 300),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'area', 'network_type')


@register_search
class OSPFNetworkIndex(SearchIndex):
    model = OSPFNetwork
    fields = (
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('ospf_interface', 'ip_address')


@register_search
class OSPFRedistributionIndex(SearchIndex):
    model = OSPFRedistribution
    fields = (
        ('route_policy', 100),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'protocol')


@register_search
class OSPFVirtualLinkIndex(SearchIndex):
    model = OSPFVirtualLink
    fields = (
        ('remote_router_id', 100),
        ('key_chain', 300),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'transit_area')


@register_search
class OSPFSummaryAddressIndex(SearchIndex):
    model = OSPFSummaryAddress
    fields = (
        ('prefix', 100),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('instance', 'not_advertise')


@register_search
class OSPFNeighborIndex(SearchIndex):
    model = OSPFNeighbor
    fields = (
        ('ip_address', 100),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('ospf_interface', 'priority')


@register_search
class OSPFAreaRangeIndex(SearchIndex):
    model = OSPFAreaRange
    fields = (
        ('prefix', 100),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('area', 'advertise')
