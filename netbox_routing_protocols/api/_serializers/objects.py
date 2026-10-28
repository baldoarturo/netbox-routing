from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from netbox.api.fields import ContentTypeField
from netbox.api.gfk_fields import GFKSerializerField
from netbox.api.serializers import NetBoxModelSerializer
from netbox_routing_protocols.constants.objects import PREFIX_ASSIGNMENT_MODELS
from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.api._serializers.community import *

__all__ = (
    'ASPathSerializer',
    'ASPathEntrySerializer',
    'CustomPrefixSerializer',
    'PrefixListSerializer',
    'PrefixListEntrySerializer',
    'RouteMapSerializer',
    'RouteMapEntrySerializer',
)


class ASPathSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:aspath-detail'
    )

    class Meta:
        model = ASPath
        fields = (
            'url',
            'id',
            'display',
            'name',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name')


class ASPathEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:aspathentry-detail'
    )
    aspath = ASPathSerializer(nested=True)

    class Meta:
        model = ASPathEntry
        fields = (
            'url',
            'id',
            'display',
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'aspath',
            'sequence',
            'action',
            'pattern',
        )


class PrefixListSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:prefixlist-detail'
    )

    class Meta:
        model = PrefixList
        fields = (
            'url',
            'id',
            'display',
            'name',
            'description',
            'comments',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
        )


class PrefixListEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:prefixlistentry-detail'
    )
    prefix_list = PrefixListSerializer(nested=True)
    assigned_prefix_type = ContentTypeField(
        queryset=ContentType.objects.filter(PREFIX_ASSIGNMENT_MODELS),
        allow_null=True,
        required=False,
        default=None,
    )
    assigned_prefix_id = serializers.IntegerField(
        allow_null=True, required=False, default=None
    )
    assigned_prefix = GFKSerializerField(read_only=True)

    class Meta:
        model = PrefixListEntry
        fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'assigned_prefix_type',
            'assigned_prefix_id',
            'assigned_prefix',
            'le',
            'ge',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'assigned_prefix_type',
            'assigned_prefix_id',
            'le',
            'ge',
        )


class CustomPrefixSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:customprefix-detail'
    )

    class Meta:
        model = CustomPrefix
        fields = (
            'url',
            'id',
            'display',
            'prefix',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'prefix',
        )


class RouteMapSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:routemap-detail'
    )

    class Meta:
        model = RouteMap
        fields = (
            'url',
            'id',
            'display',
            'name',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name')


class RouteMapEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:routemapentry-detail'
    )
    route_map = RouteMapSerializer(nested=True)
    match_prefix_list = PrefixListSerializer(nested=True, many=True, required=False)
    match_community_list = CommunityListSerializer(
        nested=True, many=True, required=False
    )
    match_community = CommunitySerializer(nested=True, many=True, required=False)
    match_aspath = ASPathSerializer(nested=True, many=True, required=False)

    class Meta:
        model = RouteMapEntry
        fields = (
            'url',
            'id',
            'display',
            'route_map',
            'sequence',
            'action',
            'flow_control',
            'match_prefix_list',
            'match_community_list',
            'match_community',
            'match_aspath',
            'match',
            'set',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'route_map',
            'sequence',
            'action',
        )
