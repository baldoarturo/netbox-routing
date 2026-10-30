from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api._serializers.bgp import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceViewSet',
    'BGPAddressFamilyViewSet',
    'BGPPeerGroupViewSet',
    'BGPListenRangeViewSet',
    'BGPRedistributionViewSet',
    'BGPOriginatedNetworkViewSet',
    'BGPAggregateViewSet',
    'BGPPeerViewSet',
    'BGPPeerAddressFamilyViewSet',
    'BFDProfileViewSet',
)


class BGPInstanceViewSet(NetBoxModelViewSet):
    queryset = BGPInstance.objects.select_related(
        'device',
        'vrf',
        'asn',
        'confederation_identifier',
        'import_policy',
        'export_policy',
        'tenant',
    ).prefetch_related('confederation_peers')
    serializer_class = BGPInstanceSerializer
    filterset_class = filtersets.BGPInstanceFilterSet


class BGPAddressFamilyViewSet(NetBoxModelViewSet):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    serializer_class = BGPAddressFamilySerializer
    filterset_class = filtersets.BGPAddressFamilyFilterSet


class BGPPeerGroupViewSet(NetBoxModelViewSet):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
        'tenant',
    )
    serializer_class = BGPPeerGroupSerializer
    filterset_class = filtersets.BGPPeerGroupFilterSet


class BGPListenRangeViewSet(NetBoxModelViewSet):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix__vrf',
    )
    serializer_class = BGPListenRangeSerializer
    filterset_class = filtersets.BGPListenRangeFilterSet


class BGPRedistributionViewSet(NetBoxModelViewSet):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    serializer_class = BGPRedistributionSerializer
    filterset_class = filtersets.BGPRedistributionFilterSet


class BGPOriginatedNetworkViewSet(NetBoxModelViewSet):
    queryset = BGPOriginatedNetwork.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'prefix',
        'tenant',
    )
    serializer_class = BGPOriginatedNetworkSerializer
    filterset_class = filtersets.BGPOriginatedNetworkFilterSet


class BGPAggregateViewSet(NetBoxModelViewSet):
    queryset = BGPAggregate.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'prefix',
        'tenant',
    )
    serializer_class = BGPAggregateSerializer
    filterset_class = filtersets.BGPAggregateFilterSet


class BGPPeerViewSet(NetBoxModelViewSet):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'interface__device',
        'interface__cable',
        'source',
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
        'tenant',
    )
    serializer_class = BGPPeerSerializer
    filterset_class = filtersets.BGPPeerFilterSet


class BGPPeerAddressFamilyViewSet(NetBoxModelViewSet):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance__device',
        'peer__instance__vrf',
        'peer__instance__asn',
        'peer__peer',
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'prefixlist_in',
        'prefixlist_out',
        'import_policy',
        'export_policy',
        'tenant',
    )
    serializer_class = BGPPeerAddressFamilySerializer
    filterset_class = filtersets.BGPPeerAddressFamilyFilterSet


class BFDProfileViewSet(NetBoxModelViewSet):
    queryset = BFDProfile.objects.select_related('tenant')
    serializer_class = BFDProfileSerializer
    filterset_class = filtersets.BFDProfileFilterSet
