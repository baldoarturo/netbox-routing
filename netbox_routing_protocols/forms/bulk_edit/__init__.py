from .static import *
from .objects import *
from .ospf import *
from .isis import *
from .eigrp import *
from .bgp import *

__all__ = (
    # Staticroute
    'StaticRouteBulkEditForm',
    # OSPF
    'OSPFInstanceBulkEditForm',
    'OSPFInterfaceBulkEditForm',
    'OSPFAreaBulkEditForm',
    'OSPFNetworkBulkEditForm',
    'OSPFRedistributionBulkEditForm',
    'OSPFVirtualLinkBulkEditForm',
    'OSPFSummaryAddressBulkEditForm',
    'OSPFNeighborBulkEditForm',
    'OSPFAreaRangeBulkEditForm',
    'OSPFPrefixSIDBulkEditForm',
    # IS-IS
    'ISISInstanceBulkEditForm',
    'ISISInterfaceBulkEditForm',
    'ISISSettingBulkEditForm',
    'ISISLevelBulkEditForm',
    'ISISInterfaceLevelBulkEditForm',
    'ISISSegmentRoutingBulkEditForm',
    'ISISFlexAlgoBulkEditForm',
    'ISISPrefixSIDBulkEditForm',
    'ISISSRv6LocatorBulkEditForm',
    'ISISSRMappingEntryBulkEditForm',
    'ISISAdjacencySIDBulkEditForm',
    'ISISRedistributionBulkEditForm',
    'ISISSummaryAddressBulkEditForm',
    'ISISRouteLeakBulkEditForm',
    # EIGRP
    'EIGRPRouterBulkEditForm',
    'EIGRPAddressFamilyBulkEditForm',
    'EIGRPNetworkBulkEditForm',
    'EIGRPInterfaceBulkEditForm',
    # Route Objects
    'PrefixListEntryBulkEditForm',
    'RoutePolicyEntryBulkEditForm',
    'ASPathBulkEditForm',
    'ASPathEntryBulkEditForm',
    # BFD
    'BFDProfileBulkEditForm',
    # BGP
    'BGPPeerTemplateBulkEditForm',
    'BGPPolicyTemplateBulkEditForm',
    'BGPSessionTemplateBulkEditForm',
    'BGPRouterBulkEditForm',
    'BGPScopeBulkEditForm',
    'BGPAddressFamilyBulkEditForm',
    'BGPPeerBulkEditForm',
    'BGPPeerAddressFamilyBulkEditForm',
    'BGPSettingBulkEditForm',
)
