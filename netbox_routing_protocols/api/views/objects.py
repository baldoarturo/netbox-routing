from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api._serializers.objects import *
from netbox_routing_protocols.models.objects import *

__all__ = (
    'PrefixListViewSet',
    'PrefixListEntryViewSet',
    'RouteMapViewSet',
    'RouteMapEntryViewSet',
    'ASPathViewSet',
    'ASPathEntryViewSet',
)


class PrefixListViewSet(NetBoxModelViewSet):
    queryset = PrefixList.objects.all()
    serializer_class = PrefixListSerializer
    filterset_class = filtersets.PrefixListFilterSet


class PrefixListEntryViewSet(NetBoxModelViewSet):
    queryset = PrefixListEntry.objects.select_related('prefix_list')
    serializer_class = PrefixListEntrySerializer
    filterset_class = filtersets.PrefixListEntryFilterSet


class CustomPrefixViewSet(NetBoxModelViewSet):
    queryset = CustomPrefix.objects.all()
    serializer_class = CustomPrefixSerializer
    filterset_class = filtersets.CustomPrefixFilterSet


class RouteMapViewSet(NetBoxModelViewSet):
    queryset = RouteMap.objects.all()
    serializer_class = RouteMapSerializer
    filterset_class = filtersets.RouteMapFilterSet


class RouteMapEntryViewSet(NetBoxModelViewSet):
    queryset = RouteMapEntry.objects.select_related('route_map')
    serializer_class = RouteMapEntrySerializer
    filterset_class = filtersets.RouteMapEntryFilterSet


class ASPathViewSet(NetBoxModelViewSet):
    queryset = ASPath.objects.all()
    serializer_class = ASPathSerializer
    filterset_class = filtersets.ASPathFilterSet


class ASPathEntryViewSet(NetBoxModelViewSet):
    queryset = ASPathEntry.objects.select_related('aspath')
    serializer_class = ASPathEntrySerializer
    filterset_class = filtersets.ASPathEntryFilterSet
