from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api._serializers.objects import *
from netbox_routing_protocols.helpers import aspath as aspath_helpers
from netbox_routing_protocols.helpers import route_policy as route_policy_helpers
from netbox_routing_protocols.helpers.prefix_list import (
    SEQUENCE_STEP,
    resequence as resequence_entries,
)
from netbox_routing_protocols.models.objects import *

# the lists an entry matches on, read once for all the entries of a page
ENTRY_MATCHES = (
    'match_prefix_list',
    'match_community_list',
    'match_aspath',
)

__all__ = (
    'PrefixListViewSet',
    'PrefixListEntryViewSet',
    'RoutePolicyViewSet',
    'RoutePolicyEntryViewSet',
    'ASPathViewSet',
    'ASPathEntryViewSet',
)


class PrefixListViewSet(NetBoxModelViewSet):
    queryset = PrefixList.objects.all()
    serializer_class = PrefixListSerializer
    filterset_class = filtersets.PrefixListFilterSet

    @action(detail=True, methods=['patch'])
    def resequence(self, request, pk=None):
        """
        Renumber the entries of the list keeping their order: `start` (default 10), then
        every `step` (default 10). Needs the permission to change prefix list entries.
        """
        prefix_list = self.get_object()
        if not request.user.has_perm('netbox_routing_protocols.change_prefixlistentry'):
            raise PermissionDenied('You cannot change prefix list entries.')
        values = {}
        for name in ('start', 'step'):
            raw = request.data.get(name, SEQUENCE_STEP)
            if not str(raw).isdigit():
                return Response(
                    {name: 'A positive whole number is required.'}, status=400
                )
            values[name] = int(raw)
        try:
            changed = resequence_entries(prefix_list, **values)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=400)
        return Response({'changed': changed})


class PrefixListEntryViewSet(NetBoxModelViewSet):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    serializer_class = PrefixListEntrySerializer
    filterset_class = filtersets.PrefixListEntryFilterSet


class RoutePolicyViewSet(NetBoxModelViewSet):
    queryset = RoutePolicy.objects.all()
    serializer_class = RoutePolicySerializer
    filterset_class = filtersets.RoutePolicyFilterSet

    @action(detail=True, methods=['patch'])
    def resequence(self, request, pk=None):
        """
        Renumber the entries of the route policy keeping their order: `start` (default 10),
        then every `step` (default 10); the continue of the entries follows the entries it
        points to. Needs the permission to change route policy entries.
        """
        route_policy = self.get_object()
        if not request.user.has_perm(
            'netbox_routing_protocols.change_routepolicyentry'
        ):
            raise PermissionDenied('You cannot change route policy entries.')
        values = {}
        for name in ('start', 'step'):
            raw = request.data.get(name, SEQUENCE_STEP)
            if not str(raw).isdigit():
                return Response(
                    {name: 'A positive whole number is required.'}, status=400
                )
            values[name] = int(raw)
        try:
            changed = route_policy_helpers.resequence(route_policy, **values)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=400)
        return Response({'changed': changed})


class RoutePolicyEntryViewSet(NetBoxModelViewSet):
    queryset = RoutePolicyEntry.objects.select_related(
        'route_policy', 'match_next_hop', 'set_next_hop', 'set_community_list'
    ).prefetch_related(*ENTRY_MATCHES)
    serializer_class = RoutePolicyEntrySerializer
    filterset_class = filtersets.RoutePolicyEntryFilterSet


class ASPathViewSet(NetBoxModelViewSet):
    queryset = ASPath.objects.all()
    serializer_class = ASPathSerializer
    filterset_class = filtersets.ASPathFilterSet

    @action(detail=True, methods=['patch'])
    def resequence(self, request, pk=None):
        """
        Renumber the entries of the AS-path keeping their order: `start` (default 10), then
        every `step` (default 10). Needs the permission to change AS-path entries.
        """
        aspath = self.get_object()
        if not request.user.has_perm('netbox_routing_protocols.change_aspathentry'):
            raise PermissionDenied('You cannot change AS-path entries.')
        values = {}
        for name in ('start', 'step'):
            raw = request.data.get(name, SEQUENCE_STEP)
            if not str(raw).isdigit():
                return Response(
                    {name: 'A positive whole number is required.'}, status=400
                )
            values[name] = int(raw)
        try:
            changed = aspath_helpers.resequence(aspath, **values)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=400)
        return Response({'changed': changed})


class ASPathEntryViewSet(NetBoxModelViewSet):
    queryset = ASPathEntry.objects.select_related('aspath')
    serializer_class = ASPathEntrySerializer
    filterset_class = filtersets.ASPathEntryFilterSet
