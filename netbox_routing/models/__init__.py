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
    ISISSRv6Locator,
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
    # IS-IS
    'ISISInstance',
    'ISISInterface',
    'ISISSetting',
    'ISISLevel',
    'ISISInterfaceLevel',
    'ISISSegmentRouting',
    'ISISFlexAlgo',
    'ISISPrefixSID',
    'ISISSRv6Locator',
    # Objects -> AS Path
    'ASPath',
    'ASPathEntry',
    # Objects -> Prefix Lists
    'PrefixList',
    'PrefixListEntry',
    'CustomPrefix',
    # Objects -> Route Maps
    'RouteMap',
    'RouteMapEntry',
    # Static Routing
    'StaticRoute',
)
