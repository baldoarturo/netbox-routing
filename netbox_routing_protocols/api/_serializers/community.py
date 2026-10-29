from rest_framework import serializers

from netbox.api.fields import ChoiceField
from ipam.api.serializers_.roles import RoleSerializer
from netbox_routing_protocols.choices import ActionChoices, CommunityStatusChoices
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer

from netbox_routing_protocols.models.community import *

__all__ = (
    'CommunityListSerializer',
    'CommunitySerializer',
    'CommunityListEntrySerializer',
)


class CommunitySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:community-detail'
    )
    status = ChoiceField(choices=CommunityStatusChoices, required=False)
    role = RoleSerializer(nested=True, required=False)
    tenant = TenantSerializer(nested=True, required=False)

    class Meta:
        model = Community
        fields = (
            'url',
            'id',
            'display',
            'name',
            'community',
            'role',
            'status',
            'tenant',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name', 'community', 'description')


class CommunityListSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:communitylist-detail'
    )
    tenant = TenantSerializer(nested=True, required=False)

    class Meta:
        model = CommunityList
        fields = (
            'url',
            'id',
            'display',
            'name',
            'tenant',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name', 'description')


class CommunityListEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:communitylistentry-detail'
    )
    community_list = CommunityListSerializer(nested=True)
    community = CommunitySerializer(nested=True)
    action = ChoiceField(choices=ActionChoices)

    class Meta:
        model = CommunityListEntry
        fields = (
            'url',
            'id',
            'display',
            'community_list',
            'action',
            'community',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'community_list',
            'action',
            'community',
            'description',
        )
