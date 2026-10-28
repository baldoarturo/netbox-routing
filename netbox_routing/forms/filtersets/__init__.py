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
    RouteMapFilterForm,
    RouteMapEntryFilterForm,
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
    # Routing Objects
    'PrefixListFilterForm',
    'PrefixListEntryFilterForm',
    'RouteMapFilterForm',
    'RouteMapEntryFilterForm',
)
