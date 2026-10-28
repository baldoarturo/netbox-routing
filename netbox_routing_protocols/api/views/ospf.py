from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api.serializers import (
    OSPFInstanceSerializer,
    OSPFAreaSerializer,
    OSPFInterfaceSerializer,
    OSPFNetworkSerializer,
    OSPFRedistributionSerializer,
    OSPFVirtualLinkSerializer,
    OSPFSummaryAddressSerializer,
    OSPFNeighborSerializer,
    OSPFAreaRangeSerializer,
)
from netbox_routing_protocols.models import (
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
    OSPFAreaRange,
)

__all__ = (
    'OSPFInstanceViewSet',
    'OSPFAreaViewSet',
    'OSPFInterfaceViewSet',
    'OSPFNetworkViewSet',
    'OSPFRedistributionViewSet',
    'OSPFVirtualLinkViewSet',
    'OSPFSummaryAddressViewSet',
    'OSPFNeighborViewSet',
    'OSPFAreaRangeViewSet',
)


class OSPFInstanceViewSet(NetBoxModelViewSet):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    serializer_class = OSPFInstanceSerializer
    filterset_class = filtersets.OSPFInstanceFilterSet


class OSPFAreaViewSet(NetBoxModelViewSet):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    serializer_class = OSPFAreaSerializer
    filterset_class = filtersets.OSPFAreaFilterSet


class OSPFInterfaceViewSet(NetBoxModelViewSet):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    serializer_class = OSPFInterfaceSerializer
    filterset_class = filtersets.OSPFInterfaceFilterSet


class OSPFNetworkViewSet(NetBoxModelViewSet):
    queryset = OSPFNetwork.objects.select_related(
        'ospf_interface__instance__device',
        'ospf_interface__instance__vrf',
        'ospf_interface__area',
        'ospf_interface__interface__device',
        'ip_address',
    )
    serializer_class = OSPFNetworkSerializer
    filterset_class = filtersets.OSPFNetworkFilterSet


class OSPFRedistributionViewSet(NetBoxModelViewSet):
    queryset = OSPFRedistribution.objects.select_related(
        'instance__device',
        'instance__vrf',
        'ospf_source__device',
        'eigrp_source__device',
        'bgp_source__asn',
        'isis_source__device',
    ).prefetch_related('bgp_source__assigned_object')
    serializer_class = OSPFRedistributionSerializer
    filterset_class = filtersets.OSPFRedistributionFilterSet


class OSPFVirtualLinkViewSet(NetBoxModelViewSet):
    queryset = OSPFVirtualLink.objects.select_related(
        'instance__device', 'instance__vrf', 'transit_area__instance'
    )
    serializer_class = OSPFVirtualLinkSerializer
    filterset_class = filtersets.OSPFVirtualLinkFilterSet


class OSPFSummaryAddressViewSet(NetBoxModelViewSet):
    queryset = OSPFSummaryAddress.objects.select_related(
        'instance__device', 'instance__vrf'
    )
    serializer_class = OSPFSummaryAddressSerializer
    filterset_class = filtersets.OSPFSummaryAddressFilterSet


class OSPFNeighborViewSet(NetBoxModelViewSet):
    queryset = OSPFNeighbor.objects.select_related(
        'ospf_interface__instance__device',
        'ospf_interface__instance__vrf',
        'ospf_interface__area',
        'ospf_interface__interface__device',
    )
    serializer_class = OSPFNeighborSerializer
    filterset_class = filtersets.OSPFNeighborFilterSet


class OSPFAreaRangeViewSet(NetBoxModelViewSet):
    queryset = OSPFAreaRange.objects.select_related(
        'area__instance__device', 'area__instance__vrf'
    )
    serializer_class = OSPFAreaRangeSerializer
    filterset_class = filtersets.OSPFAreaRangeFilterSet
