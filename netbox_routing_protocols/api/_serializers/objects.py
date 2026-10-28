from rest_framework import serializers

from ipam.choices import IPAddressFamilyChoices
from ipam.api.serializers import PrefixSerializer
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer, PrimaryModelSerializer
from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.api._serializers.community import *

__all__ = (
    'ASPathSerializer',
    'ASPathEntrySerializer',
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


class PrefixListSerializer(PrimaryModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:prefixlist-detail'
    )
    family = ChoiceField(choices=IPAddressFamilyChoices, required=False)

    class Meta:
        model = PrefixList
        fields = (
            'url',
            'id',
            'display',
            'name',
            'family',
            'description',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
            'family',
        )


class PrefixListEntrySerializer(PrimaryModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:prefixlistentry-detail'
    )
    prefix_list = PrefixListSerializer(nested=True)
    prefix = PrefixSerializer(nested=True)

    class Meta:
        model = PrefixListEntry
        fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'le',
            'ge',
            'description',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'le',
            'ge',
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
