from netbox_routing_plugin.api._serializers.objects import *
from netbox_routing_plugin.api._serializers.community import *
from netbox_routing_plugin.api._serializers.static import StaticRouteSerializer
from netbox_routing_plugin.api._serializers.bgp import *
from netbox_routing_plugin.api._serializers.isis import *
from netbox_routing_plugin.api._serializers.ospf import *
from netbox_routing_plugin.api._serializers.isis_routes import *
from netbox_routing_plugin.api._serializers.eigrp import *

__all__ = (
    'CommunitySerializer',
    'CommunityListSerializer',
    'CommunityListEntrySerializer',
    'StaticRouteSerializer',
    'OSPFInstanceSerializer',
    'OSPFAreaSerializer',
    'OSPFInterfaceSerializer',
    'OSPFNetworkSerializer',
    'OSPFRedistributionSerializer',
    'OSPFVirtualLinkSerializer',
    'OSPFSummaryAddressSerializer',
    'OSPFNeighborSerializer',
    'OSPFAreaRangeSerializer',
    'OSPFPrefixSIDSerializer',
    'OSPFAuthenticationKeySerializer',
    'ISISInstanceSerializer',
    'ISISInterfaceSerializer',
    'ISISSettingSerializer',
    'ISISLevelSerializer',
    'ISISInterfaceLevelSerializer',
    'ISISSegmentRoutingSerializer',
    'ISISFlexAlgoSerializer',
    'ISISPrefixSIDSerializer',
    'ISISSRv6LocatorSerializer',
    'ISISAddressFamilySerializer',
    'ISISSRMappingEntrySerializer',
    'ISISAdjacencySIDSerializer',
    'ISISAreaAddressSerializer',
    'ISISRedistributionSerializer',
    'ISISSummaryAddressSerializer',
    'ISISRouteLeakSerializer',
    'EIGRPRouterSerializer',
    'EIGRPAddressFamilySerializer',
    'EIGRPNetworkSerializer',
    'EIGRPInterfaceSerializer',
    'PrefixListSerializer',
    'PrefixListEntrySerializer',
    'RoutePolicySerializer',
    'RoutePolicyEntrySerializer',
    'BGPInstanceSerializer',
    'BGPAddressFamilySerializer',
    'BGPPeerGroupSerializer',
    'BGPListenRangeSerializer',
    'BGPRedistributionSerializer',
    'BGPOriginatedNetworkSerializer',
    'BGPAggregateSerializer',
    'BGPPeerSerializer',
    'BGPPeerAddressFamilySerializer',
)
