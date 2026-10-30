from .bgp import *
from .community import *
from .eigrp import *
from .isis import (
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISAddressFamily,
    ISISAreaAddress,
    ISISRedistribution,
    ISISRouteLeak,
    ISISAdjacencySID,
    ISISSRMappingEntry,
    ISISSRv6Locator,
    ISISSummaryAddress,
)
from .objects import *
from .ospf import (
    OSPFArea,
    OSPFAuthenticationMixin,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
    OSPFAreaRange,
    OSPFPrefixSID,
    OSPFAuthenticationKey,
)
from .static import StaticRoute

__all__ = (
    # BGP
    'BGPRouter',
    'BGPScope',
    'BGPAddressFamily',
    'BGPPeerTemplate',
    'BGPPolicyTemplate',
    'BGPSessionTemplate',
    'BGPSetting',
    'BGPPeer',
    'BGPPeerAddressFamily',
    # Communities
    'Community',
    'CommunityList',
    'CommunityListEntry',
    # EIGRP
    'EIGRPRouter',
    'EIGRPAddressFamily',
    'EIGRPNetwork',
    'EIGRPInterface',
    # OSPF
    'OSPFArea',
    'OSPFAuthenticationMixin',
    'OSPFInstance',
    'OSPFInterface',
    'OSPFNetwork',
    'OSPFRedistribution',
    'OSPFVirtualLink',
    'OSPFSummaryAddress',
    'OSPFNeighbor',
    'OSPFAreaRange',
    'OSPFPrefixSID',
    'OSPFAuthenticationKey',
    # IS-IS
    'ISISInstance',
    'ISISInterface',
    'ISISSetting',
    'ISISLevel',
    'ISISInterfaceLevel',
    'ISISSegmentRouting',
    'ISISFlexAlgo',
    'ISISPrefixSID',
    'ISISAddressFamily',
    'ISISAreaAddress',
    'ISISRedistribution',
    'ISISRouteLeak',
    'ISISAdjacencySID',
    'ISISSRMappingEntry',
    'ISISSRv6Locator',
    'ISISSummaryAddress',
    # Objects -> AS Path
    'ASPath',
    'ASPathEntry',
    # Objects -> Prefix Lists
    'PrefixList',
    'PrefixListEntry',
    # Objects -> Route Policies
    'RoutePolicy',
    'RoutePolicyEntry',
    # Static Routing
    'StaticRoute',
)
