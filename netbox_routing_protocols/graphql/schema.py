import strawberry
import strawberry_django

from .bgp.types import (
    BGPPeerTemplateType,
    BGPPolicyTemplateType,
    BGPSessionTemplateType,
    BGPRouterType,
    BGPScopeType,
    BGPAddressFamilyType,
    BGPPeerType,
    BGPPeerAddressFamilyType,
    BFDProfileType,
)
from .community.types import CommunityType, CommunityListType, CommunityListEntryType
from .eigrp.types import (
    EIGRPRouterType,
    EIGRPAddressFamilyType,
    EIGRPNetworkType,
    EIGRPInterfaceType,
)
from .objects.types import (
    ASPathType,
    ASPathEntryType,
    PrefixListType,
    PrefixListEntryType,
    RoutePolicyType,
    RoutePolicyEntryType,
)
from .isis.types import (
    ISISInstanceType,
    ISISInterfaceType,
    ISISSettingType,
    ISISLevelType,
    ISISInterfaceLevelType,
    ISISSegmentRoutingType,
    ISISFlexAlgoType,
    ISISPrefixSIDType,
    ISISSRv6LocatorType,
    ISISAddressFamilyType,
    ISISSRMappingEntryType,
    ISISAdjacencySIDType,
    ISISAreaAddressType,
    ISISRedistributionType,
    ISISSummaryAddressType,
    ISISRouteLeakType,
)
from .ospf.types import (
    OSPFInstanceType,
    OSPFAreaType,
    OSPFInterfaceType,
    OSPFNetworkType,
    OSPFRedistributionType,
    OSPFVirtualLinkType,
    OSPFSummaryAddressType,
    OSPFNeighborType,
    OSPFAreaRangeType,
    OSPFPrefixSIDType,
    OSPFAuthenticationKeyType,
)
from .static.types import StaticRouteType


@strawberry.type(name="Query")
class StaticRouteQuery:
    static_route: StaticRouteType = strawberry_django.field()
    static_route_list: list[StaticRouteType] = strawberry_django.field()


@strawberry.type(name="Query")
class OSPFQuery:
    ospf_instance: OSPFInstanceType = strawberry_django.field()
    ospf_instance_list: list[OSPFInstanceType] = strawberry_django.field()

    ospf_area: OSPFAreaType = strawberry_django.field()
    ospf_area_list: list[OSPFAreaType] = strawberry_django.field()

    ospf_interface: OSPFInterfaceType = strawberry_django.field()
    ospf_interface_list: list[OSPFInterfaceType] = strawberry_django.field()

    ospf_network: OSPFNetworkType = strawberry_django.field()
    ospf_network_list: list[OSPFNetworkType] = strawberry_django.field()

    ospf_redistribution: OSPFRedistributionType = strawberry_django.field()
    ospf_redistribution_list: list[OSPFRedistributionType] = strawberry_django.field()

    ospf_virtual_link: OSPFVirtualLinkType = strawberry_django.field()
    ospf_virtual_link_list: list[OSPFVirtualLinkType] = strawberry_django.field()

    ospf_summary_address: OSPFSummaryAddressType = strawberry_django.field()
    ospf_summary_address_list: list[OSPFSummaryAddressType] = strawberry_django.field()

    ospf_neighbor: OSPFNeighborType = strawberry_django.field()
    ospf_neighbor_list: list[OSPFNeighborType] = strawberry_django.field()

    ospf_area_range: OSPFAreaRangeType = strawberry_django.field()
    ospf_area_range_list: list[OSPFAreaRangeType] = strawberry_django.field()

    ospf_prefix_sid: OSPFPrefixSIDType = strawberry_django.field()
    ospf_prefix_sid_list: list[OSPFPrefixSIDType] = strawberry_django.field()

    ospf_authentication_key: OSPFAuthenticationKeyType = strawberry_django.field()
    ospf_authentication_key_list: list[OSPFAuthenticationKeyType] = (
        strawberry_django.field()
    )


@strawberry.type(name="Query")
class ISISQuery:
    isis_instance: ISISInstanceType = strawberry_django.field()
    isis_instance_list: list[ISISInstanceType] = strawberry_django.field()

    isis_interface: ISISInterfaceType = strawberry_django.field()
    isis_interface_list: list[ISISInterfaceType] = strawberry_django.field()

    isis_setting: ISISSettingType = strawberry_django.field()
    isis_setting_list: list[ISISSettingType] = strawberry_django.field()

    isis_level: ISISLevelType = strawberry_django.field()
    isis_level_list: list[ISISLevelType] = strawberry_django.field()

    isis_interface_level: ISISInterfaceLevelType = strawberry_django.field()
    isis_interface_level_list: list[ISISInterfaceLevelType] = strawberry_django.field()

    isis_segment_routing: ISISSegmentRoutingType = strawberry_django.field()
    isis_segment_routing_list: list[ISISSegmentRoutingType] = strawberry_django.field()

    isis_flex_algo: ISISFlexAlgoType = strawberry_django.field()
    isis_flex_algo_list: list[ISISFlexAlgoType] = strawberry_django.field()
    isis_address_family: ISISAddressFamilyType = strawberry_django.field()
    isis_address_family_list: list[ISISAddressFamilyType] = strawberry_django.field()
    isis_sr_mapping_entry: ISISSRMappingEntryType = strawberry_django.field()
    isis_sr_mapping_entry_list: list[ISISSRMappingEntryType] = strawberry_django.field()
    isis_adjacency_sid: ISISAdjacencySIDType = strawberry_django.field()
    isis_adjacency_sid_list: list[ISISAdjacencySIDType] = strawberry_django.field()
    isis_area_address: ISISAreaAddressType = strawberry_django.field()
    isis_area_address_list: list[ISISAreaAddressType] = strawberry_django.field()
    isis_redistribution: ISISRedistributionType = strawberry_django.field()
    isis_redistribution_list: list[ISISRedistributionType] = strawberry_django.field()
    isis_summary_address: ISISSummaryAddressType = strawberry_django.field()
    isis_summary_address_list: list[ISISSummaryAddressType] = strawberry_django.field()
    isis_route_leak: ISISRouteLeakType = strawberry_django.field()
    isis_route_leak_list: list[ISISRouteLeakType] = strawberry_django.field()

    isis_prefix_sid: ISISPrefixSIDType = strawberry_django.field()
    isis_prefix_sid_list: list[ISISPrefixSIDType] = strawberry_django.field()

    isis_srv6_locator: ISISSRv6LocatorType = strawberry_django.field()
    isis_srv6_locator_list: list[ISISSRv6LocatorType] = strawberry_django.field()


@strawberry.type(name="Query")
class EIGRPQuery:
    eigrp_router: EIGRPRouterType = strawberry_django.field()
    eigrp_router_list: list[EIGRPRouterType] = strawberry_django.field()

    eigrp_address_family: EIGRPAddressFamilyType = strawberry_django.field()
    eigrp_address_family_list: list[EIGRPAddressFamilyType] = strawberry_django.field()

    eigrp_network: EIGRPNetworkType = strawberry_django.field()
    eigrp_network_list: list[EIGRPNetworkType] = strawberry_django.field()

    eigrp_interface: EIGRPInterfaceType = strawberry_django.field()
    eigrp_interface_list: list[EIGRPInterfaceType] = strawberry_django.field()


@strawberry.type(name="Query")
class CommunityQuery:
    community: CommunityType = strawberry_django.field()
    community_list: list[CommunityType] = strawberry_django.field()


@strawberry.type(name="Query")
class CommunityListQuery:
    communitylist: CommunityListType = strawberry_django.field()
    communitylist_list: list[CommunityListType] = strawberry_django.field()


@strawberry.type(name="Query")
class CommunityListEntryQuery:
    communitylistentry: CommunityListEntryType = strawberry_django.field()
    communitylistentry_list: list[CommunityListEntryType] = strawberry_django.field()


@strawberry.type(name="Query")
class ASPathQuery:
    aspath: ASPathType = strawberry_django.field()
    aspath_list: list[ASPathType] = strawberry_django.field()


@strawberry.type(name="Query")
class ASPathEntryQuery:
    aspath_entry: ASPathEntryType = strawberry_django.field()
    aspath_entry_list: list[ASPathEntryType] = strawberry_django.field()


@strawberry.type(name="Query")
class PrefixListQuery:
    prefixlist: PrefixListType = strawberry_django.field()
    prefixlist_list: list[PrefixListType] = strawberry_django.field()


@strawberry.type(name="Query")
class PrefixListEntryQuery:
    prefixlist_entry: PrefixListEntryType = strawberry_django.field()
    prefixlist_entry_list: list[PrefixListEntryType] = strawberry_django.field()


@strawberry.type(name="Query")
class RoutePolicyQuery:
    route_policy: RoutePolicyType = strawberry_django.field()
    route_policy_list: list[RoutePolicyType] = strawberry_django.field()


@strawberry.type(name="Query")
class RoutePolicyEntryQuery:
    route_policy_entry: RoutePolicyEntryType = strawberry_django.field()
    route_policy_entry_list: list[RoutePolicyEntryType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPPeerTemplateQuery:
    bgp_peer_template: BGPPeerTemplateType = strawberry_django.field()
    bgp_peer_template_list: list[BGPPeerTemplateType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPPolicyTemplateQuery:
    bgp_policy_template: BGPPolicyTemplateType = strawberry_django.field()
    bgp_policy_template_list: list[BGPPolicyTemplateType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPSessionTemplateQuery:
    bgp_session_template: BGPSessionTemplateType = strawberry_django.field()
    bgp_session_template_list: list[BGPSessionTemplateType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPRouterQuery:
    bgp_router: BGPRouterType = strawberry_django.field()
    bgp_router_list: list[BGPRouterType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPScopeQuery:
    bgp_scope: BGPScopeType = strawberry_django.field()
    bgp_scope_list: list[BGPScopeType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPAddressFamilyQuery:
    bgp_address_family: BGPAddressFamilyType = strawberry_django.field()
    bgp_address_family_list: list[BGPAddressFamilyType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPPeerQuery:
    bgp_peer: BGPPeerType = strawberry_django.field()
    bgp_peer_list: list[BGPPeerType] = strawberry_django.field()


@strawberry.type(name="Query")
class BGPPeerAddressFamilyQuery:
    bgp_peer_address_family: BGPPeerAddressFamilyType = strawberry_django.field()
    bgp_peer_address_family_list: list[BGPPeerAddressFamilyType] = (
        strawberry_django.field()
    )


@strawberry.type(name="Query")
class BFDProfileQuery:
    bfd_profile: BFDProfileType = strawberry_django.field()
    bfd_profile_list: list[BFDProfileType] = strawberry_django.field()


schema = [
    StaticRouteQuery,
    OSPFQuery,
    ISISQuery,
    EIGRPQuery,
    CommunityQuery,
    CommunityListQuery,
    CommunityListEntryQuery,
    ASPathQuery,
    ASPathEntryQuery,
    PrefixListQuery,
    PrefixListEntryQuery,
    RoutePolicyQuery,
    RoutePolicyEntryQuery,
    BGPPeerTemplateQuery,
    BGPPolicyTemplateQuery,
    BGPSessionTemplateQuery,
    BGPRouterQuery,
    BGPScopeQuery,
    BGPAddressFamilyQuery,
    BGPPeerQuery,
    BGPPeerAddressFamilyQuery,
    BFDProfileQuery,
]
