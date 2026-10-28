from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api._serializers.community import *
from netbox_routing_protocols.models.community import *

__all__ = (
    'CommunityListViewSet',
    'CommunityViewSet',
    'CommunityListEntryViewSet',
)


class CommunityListViewSet(NetBoxModelViewSet):
    queryset = CommunityList.objects.select_related('tenant')
    serializer_class = CommunityListSerializer
    filterset_class = filtersets.CommunityListFilterSet


class CommunityViewSet(NetBoxModelViewSet):
    queryset = Community.objects.select_related('role', 'tenant')
    serializer_class = CommunitySerializer
    filterset_class = filtersets.CommunityFilterSet


class CommunityListEntryViewSet(NetBoxModelViewSet):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    serializer_class = CommunityListEntrySerializer
    filterset_class = filtersets.CommunityListEntryFilterSet
