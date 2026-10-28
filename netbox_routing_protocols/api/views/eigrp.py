from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api.serializers import (
    EIGRPRouterSerializer,
    EIGRPAddressFamilySerializer,
    EIGRPInterfaceSerializer,
    EIGRPNetworkSerializer,
)
from netbox_routing_protocols.models import (
    EIGRPRouter,
    EIGRPAddressFamily,
    EIGRPNetwork,
    EIGRPInterface,
)

__all__ = (
    'EIGRPRouterViewSet',
    'EIGRPAddressFamilyViewSet',
    'EIGRPNetworkViewSet',
    'EIGRPInterfaceViewSet',
)


class EIGRPRouterViewSet(NetBoxModelViewSet):
    queryset = EIGRPRouter.objects.select_related('device')
    serializer_class = EIGRPRouterSerializer
    filterset_class = filtersets.EIGRPRouterFilterSet


class EIGRPAddressFamilyViewSet(NetBoxModelViewSet):
    queryset = EIGRPAddressFamily.objects.select_related('router__device', 'vrf')
    serializer_class = EIGRPAddressFamilySerializer
    filterset_class = filtersets.EIGRPAddressFamilyFilterSet


class EIGRPNetworkViewSet(NetBoxModelViewSet):
    queryset = EIGRPNetwork.objects.select_related(
        'router__device', 'address_family', 'network'
    )
    serializer_class = EIGRPNetworkSerializer
    filterset_class = filtersets.EIGRPNetworkFilterSet


class EIGRPInterfaceViewSet(NetBoxModelViewSet):
    queryset = EIGRPInterface.objects.select_related(
        'router__device', 'address_family', 'interface__device'
    )
    serializer_class = EIGRPInterfaceSerializer
    filterset_class = filtersets.EIGRPInterfaceFilterSet
