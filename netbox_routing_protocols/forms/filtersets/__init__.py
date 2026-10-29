from .static import StaticRouteFilterForm
from .bgp import (
    BGPRouterFilterForm,
    BGPScopeFilterForm,
    BGPAddressFamilyFilterForm,
    BGPSettingFilterForm,
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
    'BGPRouterFilterForm',
    'BGPScopeFilterForm',
    'BGPAddressFamilyFilterForm',
    'BGPSettingFilterForm',
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
    # Routing Objects
    'PrefixListFilterForm',
    'PrefixListEntryFilterForm',
    'RoutePolicyFilterForm',
    'RoutePolicyEntryFilterForm',
)
