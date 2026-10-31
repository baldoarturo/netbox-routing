from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_plugin import filtersets
from netbox_routing_plugin.api.serializers import StaticRouteSerializer
from netbox_routing_plugin.models import StaticRoute


class StaticRouteViewSet(NetBoxModelViewSet):
    queryset = StaticRoute.objects.select_related('vrf').prefetch_related('devices')
    serializer_class = StaticRouteSerializer
    filterset_class = filtersets.StaticRouteFilterSet
