from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ipam.api.serializers_.roles import RoleSerializer
from netbox.api.fields import ChoiceField
from netbox.api.serializers import PrimaryModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer

from netbox_routing_plugin.choices import (
    ActionChoices,
    CommunityStatusChoices,
    CommunityTypeChoices,
)
from netbox_routing_plugin.helpers import community as community_helpers
from netbox_routing_plugin.models.community import *

__all__ = (
    'CommunityListSerializer',
    'CommunitySerializer',
    'CommunityListEntrySerializer',
)


class CommunitySerializer(PrimaryModelSerializer):
    """`type` and `well_known` are derived from `community`, which is stored normalised"""

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:community-detail'
    )
    status = ChoiceField(choices=CommunityStatusChoices, required=False)
    type = ChoiceField(choices=CommunityTypeChoices, read_only=True)
    well_known = serializers.CharField(read_only=True)
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
            'type',
            'well_known',
            'role',
            'status',
            'tenant',
            'description',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('url', 'id', 'display', 'name', 'community', 'description')


class CommunityListSerializer(PrimaryModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:communitylist-detail'
    )
    type = ChoiceField(choices=CommunityTypeChoices, required=False)
    tenant = TenantSerializer(nested=True, required=False)

    class Meta:
        model = CommunityList
        fields = (
            'url',
            'id',
            'display',
            'name',
            'type',
            'tenant',
            'description',
            'owner',
            'comments',
            'tags',
            'custom_fields',
            'created',
            'last_updated',
        )
        brief_fields = ('url', 'id', 'display', 'name', 'description')


class CommunityListEntrySerializer(PrimaryModelSerializer):
    """An empty `sequence` takes the next free one of the list"""

    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:communitylistentry-detail'
    )
    community_list = CommunityListSerializer(nested=True)
    community = CommunitySerializer(nested=True)
    action = ChoiceField(choices=ActionChoices)

    class Meta:
        model = CommunityListEntry
        extra_kwargs = {'sequence': {'required': False, 'allow_null': True}}
        fields = (
            'url',
            'id',
            'display',
            'community_list',
            'sequence',
            'action',
            'community',
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
            'community_list',
            'sequence',
            'action',
            'community',
            'description',
        )

    def validate(self, data):
        # A new entry without sequence gets the next one of its list. The serializer of a
        # bulk request is shared by the entries, so they get consecutive numbers.
        if self.instance is None and data.get('sequence') is None:
            community_list = data.get('community_list')
            if community_list is not None:
                assigned = self.context.setdefault('community_list_sequences', {})
                try:
                    sequence = community_helpers.next_sequence(
                        community_list, assigned.get(community_list.pk, 0)
                    )
                except DjangoValidationError as e:
                    raise serializers.ValidationError({'sequence': e.messages})
                assigned[community_list.pk] = data['sequence'] = sequence
        return super().validate(data)
