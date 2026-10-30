from .static import StaticRouteFilterForm
from .bgp import (
    BGPInstanceFilterForm,
    BGPAddressFamilyFilterForm,
    BGPPeerGroupFilterForm,
    BGPPeerFilterForm,
    BGPPeerAddressFamilyFilterForm,
    BFDProfileFilterForm,
)
from .ospf import (
    OSPFAreaFilterForm,
    OSPFInstanceFilterForm,
    OSPFInterfaceFilterForm,
    OSPFNetworkFilterForm,
    OSPFRedistributionFilterForm,
    OSPFVirtualLinkFilterForm,
    OSPFSummaryAddressFilterForm,
    OSPFNeighborFilterForm,
    OSPFAreaRangeFilterForm,
    OSPFPrefixSIDFilterForm,
    OSPFAuthenticationKeyFilterForm,
)
from .isis import (
    ISISInstanceFilterForm,
    ISISInterfaceFilterForm,
    ISISSettingFilterForm,
    ISISLevelFilterForm,
    ISISInterfaceLevelFilterForm,
    ISISSegmentRoutingFilterForm,
    ISISFlexAlgoFilterForm,
    ISISPrefixSIDFilterForm,
    ISISSRv6LocatorFilterForm,
    ISISAddressFamilyFilterForm,
    ISISSRMappingEntryFilterForm,
    ISISAdjacencySIDFilterForm,
    ISISAreaAddressFilterForm,
    ISISRedistributionFilterForm,
    ISISSummaryAddressFilterForm,
    ISISRouteLeakFilterForm,
)
from .objects import (
    PrefixListFilterForm,
    PrefixListEntryFilterForm,
    RoutePolicyFilterForm,
    RoutePolicyEntryFilterForm,
)
from .eigrp import *

__all__ = (
    # Static
    'StaticRouteFilterForm',
    # BGP
    'BGPInstanceFilterForm',
    'BGPAddressFamilyFilterForm',
    'BGPPeerGroupFilterForm',
    'BGPPeerFilterForm',
    'BGPPeerAddressFamilyFilterForm',
    # BFD
    'BFDProfileFilterForm',
    # EIGRP
    'EIGRPRouterFilterForm',
    'EIGRPAddressFamilyFilterForm',
    'EIGRPNetworkFilterForm',
    'EIGRPInterfaceFilterForm',
    # IS-IS
    'ISISInstanceFilterForm',
    'ISISInterfaceFilterForm',
    'ISISSettingFilterForm',
    'ISISLevelFilterForm',
    'ISISInterfaceLevelFilterForm',
    'ISISSegmentRoutingFilterForm',
    'ISISFlexAlgoFilterForm',
    'ISISPrefixSIDFilterForm',
    'ISISSRv6LocatorFilterForm',
    'ISISAddressFamilyFilterForm',
    'ISISSRMappingEntryFilterForm',
    'ISISAdjacencySIDFilterForm',
    'ISISAreaAddressFilterForm',
    'ISISRedistributionFilterForm',
    'ISISSummaryAddressFilterForm',
    'ISISRouteLeakFilterForm',
    # OSPF
    'OSPFAreaFilterForm',
    'OSPFInstanceFilterForm',
    'OSPFInterfaceFilterForm',
    'OSPFNetworkFilterForm',
    'OSPFRedistributionFilterForm',
    'OSPFVirtualLinkFilterForm',
    'OSPFSummaryAddressFilterForm',
    'OSPFNeighborFilterForm',
    'OSPFAreaRangeFilterForm',
    'OSPFPrefixSIDFilterForm',
    'OSPFAuthenticationKeyFilterForm',
    # Routing Objects
    'PrefixListFilterForm',
    'PrefixListEntryFilterForm',
    'RoutePolicyFilterForm',
    'RoutePolicyEntryFilterForm',
)
