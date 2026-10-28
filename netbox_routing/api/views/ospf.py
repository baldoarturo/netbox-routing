from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing import filtersets
from netbox_routing.api.serializers import (
    OSPFInstanceSerializer,
    OSPFAreaSerializer,
    OSPFInterfaceSerializer,
    OSPFNetworkSerializer,
    OSPFRedistributionSerializer,
)
from netbox_routing.models import (
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
)

__all__ = (
    'OSPFInstanceViewSet',
    'OSPFAreaViewSet',
    'OSPFInterfaceViewSet',
    'OSPFNetworkViewSet',
    'OSPFRedistributionViewSet',
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
    )
    serializer_class = OSPFRedistributionSerializer
    filterset_class = filtersets.OSPFRedistributionFilterSet
