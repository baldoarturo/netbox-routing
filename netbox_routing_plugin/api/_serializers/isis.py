# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from dcim.api.serializers_.device_components import InterfaceSerializer
from dcim.api.serializers_.devices import DeviceSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from netbox.api.fields import ContentTypeField
from netbox.api.gfk_fields import GFKSerializerField
from netbox.api.serializers import NetBoxModelSerializer

from netbox_routing_plugin.constants.isis import ISISSETTING_ASSIGNMENT_MODELS
from netbox_routing_plugin.models import (
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISAddressFamily,
    ISISSRMappingEntry,
    ISISAdjacencySID,
    ISISAreaAddress,
)
from netbox_routing_plugin.api._serializers.objects import RoutePolicySerializer

__all__ = (
    'ISISInstanceSerializer',
    'ISISInterfaceSerializer',
    'ISISSettingSerializer',
    'ISISLevelSerializer',
    'ISISInterfaceLevelSerializer',
    'ISISSegmentRoutingSerializer',
    'ISISFlexAlgoSerializer',
    'ISISPrefixSIDSerializer',
    'ISISSRv6LocatorSerializer',
    'ISISAddressFamilySerializer',
    'ISISSRMappingEntrySerializer',
    'ISISAdjacencySIDSerializer',
    'ISISAreaAddressSerializer',
)


class ISISFlexAlgoSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisflexalgo-detail'
    )

    class Meta:
        model = ISISFlexAlgo
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'algo_id',
            'metric_type',
            'priority',
            'admin_group_exclude',
            'admin_group_include_any',
            'admin_group_include_all',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'algo_id', 'metric_type')


class ISISPrefixSIDSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisprefixsid-detail'
    )

    class Meta:
        model = ISISPrefixSID
        fields = (
            'url',
            'id',
            'display',
            'interface',
            'algorithm',
            'sid_index',
            'sid_label',
            'n_flag',
            'no_php',
            'explicit_null',
            'readvertise',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'algorithm', 'sid_index')


class ISISSRv6LocatorSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isissrv6locator-detail'
    )

    class Meta:
        model = ISISSRv6Locator
        # prefix (IPNetworkField) and vendor_ext (JSONField) round-trip via
        # NetBoxModelSerializer's default field mapping — no explicit declaration
        # needed (mirrors StaticRouteSerializer.prefix / RoutePolicyEntrySerializer.vendor_ext).
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'name',
            'prefix',
            'algorithm',
            'is_anycast',
            'is_micro_segment',
            'flavor',
            'block_length',
            'node_length',
            'function_length',
            'argument_length',
            'isis_level',
            'enabled',
            'vendor_ext',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'name', 'prefix')


class ISISLevelSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isislevel-detail'
    )

    class Meta:
        model = ISISLevel
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'level',
            'default_metric',
            'wide_metrics_only',
            'preference',
            'labeled_preference',
            'disabled',
            'auth_type',
            'auth_key',
            'auth_key_id',
            'auth_key_chain',
            'auth_send_only',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'level', 'default_metric')


class ISISInterfaceLevelSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisinterfacelevel-detail'
    )

    class Meta:
        model = ISISInterfaceLevel
        fields = (
            'url',
            'id',
            'display',
            'interface',
            'level',
            'metric',
            'hello_interval',
            'hello_multiplier',
            'priority',
            'passive',
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'level', 'metric')


class ISISSegmentRoutingSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isissegmentrouting-detail'
    )

    class Meta:
        model = ISISSegmentRouting
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'enabled',
            'srv6_enabled',
            'prefix_sid_range',
            'srgb_start',
            'srgb_range',
            'srlb_start',
            'srlb_range',
            'maximum_sid_depth',
            'tunnel_table_pref',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'enabled', 'prefix_sid_range')


class ISISSettingSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isissetting-detail'
    )

    assigned_object_type = ContentTypeField(
        queryset=ContentType.objects.filter(ISISSETTING_ASSIGNMENT_MODELS),
        required=False,
        allow_null=True,
    )
    assigned_object = GFKSerializerField(read_only=True)

    class Meta:
        model = ISISSetting
        fields = (
            'url',
            'id',
            'display',
            'assigned_object_type',
            'assigned_object_id',
            'assigned_object',
            'key',
            'value',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'assigned_object',
            'key',
        )


class ISISInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisinstance-detail'
    )
    device = DeviceSerializer(nested=True)
    vrf = VRFSerializer(nested=True, required=False, allow_null=True)
    import_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    export_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = ISISInstance
        fields = (
            'url',
            'id',
            'display',
            'device',
            'vrf',
            'process_tag',
            'net',
            'is_type',
            'metric_style',
            'import_policy',
            'export_policy',
            'overload_bit',
            'overload_on_startup',
            'overload_timeout',
            'suppress_attached_bit',
            'ignore_attached_bit',
            'area_auth_type',
            'area_auth_key',
            'area_auth_key_id',
            'area_auth_key_chain',
            'area_auth_send_only',
            'domain_auth_type',
            'domain_auth_key',
            'domain_auth_key_id',
            'domain_auth_key_chain',
            'domain_auth_send_only',
            'spf_initial_wait',
            'spf_max_wait',
            'lsp_initial_wait',
            'lsp_max_wait',
            'lsp_lifetime',
            'lsp_refresh_interval',
            'lsp_mtu',
            'te_enabled',
            'fast_reroute',
            'microloop_avoidance',
            'distance',
            'maximum_paths',
            'reference_bandwidth',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'device',
            'vrf',
            'process_tag',
            'net',
            'is_type',
        )


class ISISInterfaceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisinterface-detail'
    )
    instance = ISISInstanceSerializer(nested=True)
    interface = InterfaceSerializer(nested=True)

    class Meta:
        model = ISISInterface
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'interface',
            'address_family',
            'circuit_type',
            'network_type',
            'metric',
            'passive',
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            'bfd_enabled',
            'frr_enabled',
            'frr_protection',
            'csnp_interval',
            'retransmit_interval',
            'lsp_interval',
            'mesh_group',
            'hello_padding',
            'ldp_sync',
            'prefix_suppression',
            'route_tag',
            'three_way_handshake',
            'admin_group',
            'te_metric',
            'delay_metric',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'instance',
            'interface',
            'address_family',
        )


class ISISAreaAddressSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisareaaddress-detail'
    )
    instance = ISISInstanceSerializer(nested=True)

    class Meta:
        model = ISISAreaAddress
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'net',
            'area',
            'system_id',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'net')


class ISISSRMappingEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isissrmappingentry-detail'
    )
    instance = ISISInstanceSerializer(nested=True)

    class Meta:
        model = ISISSRMappingEntry
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'prefix',
            'range_size',
            'sid_index',
            'sid_label',
            'algorithm',
            'level',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'prefix')


class ISISAdjacencySIDSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisadjacencysid-detail'
    )
    interface = ISISInterfaceSerializer(nested=True)

    class Meta:
        model = ISISAdjacencySID
        fields = (
            'url',
            'id',
            'display',
            'interface',
            'sid_label',
            'protected',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'interface', 'sid_label')


class ISISAddressFamilySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisaddressfamily-detail'
    )
    instance = ISISInstanceSerializer(nested=True)

    class Meta:
        model = ISISAddressFamily
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'address_family',
            'metric_style',
            'distance',
            'maximum_paths',
            'default_originate',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'address_family')
