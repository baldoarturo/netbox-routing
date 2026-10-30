# SPDX-License-Identifier: Apache-2.0

from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.forms import NetBoxModelImportForm
from utilities.forms.fields import CSVModelChoiceField

from netbox_routing_protocols.models import (
    BGPRouter,
    EIGRPRouter,
    OSPFInstance,
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
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    'ISISInstanceImportForm',
    'ISISInterfaceImportForm',
    'ISISSettingImportForm',
    'ISISLevelImportForm',
    'ISISInterfaceLevelImportForm',
    'ISISSegmentRoutingImportForm',
    'ISISFlexAlgoImportForm',
    'ISISPrefixSIDImportForm',
    'ISISSRv6LocatorImportForm',
    'ISISAddressFamilyImportForm',
    'ISISSRMappingEntryImportForm',
    'ISISAdjacencySIDImportForm',
    'ISISAreaAddressImportForm',
    'ISISRedistributionImportForm',
    'ISISSummaryAddressImportForm',
    'ISISRouteLeakImportForm',
)


class ISISPrefixSIDImportForm(NetBoxModelImportForm):
    interface = CSVModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Interface'),
    )

    class Meta:
        model = ISISPrefixSID
        fields = (
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
        )


class ISISSRv6LocatorImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISSRv6Locator
        # vendor_ext (a null=False JSONField) is intentionally omitted: an empty CSV cell
        # would clean to None and fail model validation on every row that omits it. It
        # defaults to {} and is populated via the API / reconcilers, not bulk import.
        fields = (
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
            'description',
            'comments',
            'tags',
        )


class ISISFlexAlgoImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISFlexAlgo
        fields = (
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
        )


class ISISLevelImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISLevel
        fields = (
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
        )


class ISISInterfaceLevelImportForm(NetBoxModelImportForm):
    interface = CSVModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Interface'),
    )

    class Meta:
        model = ISISInterfaceLevel
        fields = (
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
        )


class ISISSegmentRoutingImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISSegmentRouting
        fields = (
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
        )


class ISISInstanceImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Name of device'),
    )
    vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of VRF'),
    )

    import_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the import route policy'),
    )
    export_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the export route policy'),
    )

    class Meta:
        model = ISISInstance
        fields = (
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
            'distance',
            'maximum_paths',
            'reference_bandwidth',
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
            'description',
            'comments',
            'tags',
        )


class ISISInterfaceImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of device'),
    )
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )
    interface = CSVModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Name of interface'),
    )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        # An interface name (e.g. 'Ethernet1') is only unique within a device, so the
        # by-name lookup must be scoped to the row's device — otherwise a name shared
        # across devices resolves ambiguously and the row is rejected. (The interactive
        # form scopes this via query_params={'device_id': '$device'}.)
        if data and (device := data.get('device')):
            self.fields['interface'].queryset = Interface.objects.filter(
                device__name=device
            )

    class Meta:
        model = ISISInterface
        fields = (
            'device',
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
        )


class ISISSettingImportForm(NetBoxModelImportForm):
    class Meta:
        model = ISISSetting
        fields = (
            'assigned_object_type',
            'assigned_object_id',
            'key',
            'value',
            'description',
            'comments',
            'tags',
        )


class ISISRedistributionImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )
    ospf_source = CSVModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        help_text=_('Primary key of OSPF Instance'),
    )
    eigrp_source = CSVModelChoiceField(
        queryset=EIGRPRouter.objects.all(),
        required=False,
        help_text=_('Primary key of EIGRP Router'),
    )
    bgp_source = CSVModelChoiceField(
        queryset=BGPRouter.objects.all(),
        required=False,
        help_text=_('Primary key of BGP Router'),
    )
    isis_source = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISRedistribution
        fields = (
            'instance',
            'address_family',
            'protocol',
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            'level',
            'metric',
            'metric_type',
            'route_tag',
            'route_policy',
            'description',
            'comments',
            'tags',
        )


class ISISSummaryAddressImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISSummaryAddress
        fields = (
            'instance',
            'prefix',
            'level',
            'not_advertise',
            'metric',
            'route_tag',
            'description',
            'comments',
            'tags',
        )


class ISISRouteLeakImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISRouteLeak
        fields = (
            'instance',
            'address_family',
            'route_policy',
            'description',
            'comments',
            'tags',
        )


class ISISAreaAddressImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISAreaAddress
        fields = ('instance', 'net', 'description', 'comments', 'tags')


class ISISSRMappingEntryImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISSRMappingEntry
        fields = (
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
        )


class ISISAdjacencySIDImportForm(NetBoxModelImportForm):
    interface = CSVModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Interface'),
    )

    class Meta:
        model = ISISAdjacencySID
        fields = (
            'interface',
            'sid_label',
            'protected',
            'description',
            'comments',
            'tags',
        )


class ISISAddressFamilyImportForm(NetBoxModelImportForm):
    instance = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        help_text=_('Primary key of IS-IS Instance'),
    )

    class Meta:
        model = ISISAddressFamily
        fields = (
            'instance',
            'address_family',
            'metric_style',
            'distance',
            'maximum_paths',
            'default_originate',
            'description',
            'comments',
            'tags',
        )
