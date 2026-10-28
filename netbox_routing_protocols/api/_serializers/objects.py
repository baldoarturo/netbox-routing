from rest_framework import serializers

from ipam.choices import IPAddressFamilyChoices
from ipam.api.serializers import PrefixSerializer
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer, PrimaryModelSerializer
from netbox_routing_protocols.helpers.prefix_list import any_le
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
    prefix = PrefixSerializer(nested=True, required=False, allow_null=True)
    eq = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=0,
        max_value=128,
        help_text='Exact prefix length: shorthand that sets ge and le to this value',
    )

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
            'any_prefix',
            'le',
            'ge',
            'eq',
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

    def to_internal_value(self, data):
        # `prefix` also accepts "any" or the all zeros prefix (0.0.0.0/0, ::/0), which
        # IPAM cannot hold: they set any_prefix, and the length of the entry is LE
        # (the longest length of the family) unless ge, le or eq are given.
        prefix = data.get('prefix') if hasattr(data, 'get') else None
        if isinstance(prefix, str) and not prefix.strip().isdigit():
            data = self._expand_any(data.copy(), prefix.strip().lower())
        return super().to_internal_value(data)

    def _expand_any(self, data, value):
        literal = {'0.0.0.0/0': 4, '::/0': 6}
        if value != 'any' and value not in literal:
            return data  # not a shorthand: the nested serializer reports it
        family = literal.get(value)
        if family is None:
            family = self._list_family(data.get('prefix_list'))
        if family is None and isinstance(self.instance, PrefixListEntry):
            family = self.instance.prefix_list.family
        if family is None:
            raise serializers.ValidationError(
                {
                    'prefix': "'any' needs a valid prefix_list to know the address family."
                }
            )
        data['prefix'] = None
        data['any_prefix'] = True
        if all(data.get(field) in (None, '') for field in ('ge', 'le', 'eq')):
            data['le'] = any_le(family)
        return data

    @staticmethod
    def _list_family(value):
        if isinstance(value, dict):
            value = value.get('id')
        if not str(value).isdigit():
            return None
        return (
            PrefixList.objects.filter(pk=int(value))
            .values_list('family', flat=True)
            .first()
        )

    def validate(self, data):
        eq = data.pop('eq', None)
        if eq is not None:
            if data.get('ge') is not None or data.get('le') is not None:
                raise serializers.ValidationError(
                    {'eq': 'Use either eq, or ge and le.'}
                )
            data['ge'] = data['le'] = eq
        return super().validate(data)


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
