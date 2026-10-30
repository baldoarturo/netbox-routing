# SPDX-License-Identifier: Apache-2.0

from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import VRF
from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import BulkEditNullBooleanSelect

from netbox_routing_protocols.choices import (
    ISISAddressFamilyChoices,
    ISISAuthTypeChoices,
    ISISCircuitTypeChoices,
    ISISFastRerouteChoices,
    ISISFlexAlgoMetricTypeChoices,
    ISISFrrProtectionChoices,
    ISISLevelChoices,
    ISISLevelScopeChoices,
    ISISRedistributionMetricTypeChoices,
    ISISIsTypeChoices,
    ISISMetricStyleChoices,
    ISISNetworkTypeChoices,
)
from netbox_routing_protocols.models import (
    ISISFlexAlgo,
    ISISInstance,
    ISISInterface,
    ISISInterfaceLevel,
    ISISLevel,
    ISISPrefixSID,
    ISISSegmentRouting,
    ISISSetting,
    ISISSRv6Locator,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    'ISISInstanceBulkEditForm',
    'ISISInterfaceBulkEditForm',
    'ISISSettingBulkEditForm',
    'ISISLevelBulkEditForm',
    'ISISInterfaceLevelBulkEditForm',
    'ISISSegmentRoutingBulkEditForm',
    'ISISFlexAlgoBulkEditForm',
    'ISISPrefixSIDBulkEditForm',
    'ISISSRv6LocatorBulkEditForm',
    'ISISRedistributionBulkEditForm',
    'ISISSummaryAddressBulkEditForm',
    'ISISRouteLeakBulkEditForm',
)


def _boolean(label):
    return forms.NullBooleanField(
        label=label, required=False, widget=BulkEditNullBooleanSelect()
    )


def _integer(label, **kwargs):
    return forms.IntegerField(label=label, min_value=0, required=False, **kwargs)


class ISISSettingBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISSetting
    fieldsets = (FieldSet('description', 'comments'),)
    nullable_fields = ('description', 'comments')


class ISISInstanceBulkEditForm(NetBoxModelBulkEditForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(), label=_('Device'), required=False, selector=True
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(), label=_('VRF'), required=False, selector=True
    )
    import_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
    )
    process_tag = forms.CharField(label=_('Process Tag'), required=False)
    net = forms.CharField(label=_('NET'), required=False)
    is_type = forms.ChoiceField(
        label=_('IS Type'),
        choices=add_blank_choice(ISISIsTypeChoices),
        required=False,
    )
    metric_style = forms.ChoiceField(
        label=_('Metric Style'),
        choices=add_blank_choice(ISISMetricStyleChoices),
        required=False,
    )
    overload_bit = _boolean(_('Overload Bit'))
    overload_on_startup = _boolean(_('Overload on Startup'))
    overload_timeout = _integer(_('Overload Timeout'))
    suppress_attached_bit = _boolean(_('Suppress Attached Bit'))
    ignore_attached_bit = _boolean(_('Ignore Attached Bit'))
    te_enabled = _boolean(_('Traffic Engineering'))
    fast_reroute = forms.ChoiceField(
        label=_('Fast Reroute'),
        choices=add_blank_choice(ISISFastRerouteChoices),
        required=False,
    )
    microloop_avoidance = _boolean(_('Micro-loop Avoidance'))
    spf_initial_wait = _integer(_('SPF Initial Wait'))
    spf_max_wait = _integer(_('SPF Max Wait'))
    lsp_initial_wait = _integer(_('LSP-gen Initial Wait'))
    lsp_max_wait = _integer(_('LSP-gen Max Wait'))
    reference_bandwidth = _integer(_('Reference Bandwidth'))
    lsp_lifetime = forms.IntegerField(
        label=_('LSP Lifetime'), min_value=0, required=False
    )
    lsp_refresh_interval = forms.IntegerField(
        label=_('LSP Refresh Interval'), min_value=0, required=False
    )
    lsp_mtu = forms.IntegerField(label=_('LSP MTU'), min_value=0, required=False)
    distance = forms.IntegerField(label=_('Distance'), min_value=0, required=False)
    maximum_paths = forms.IntegerField(
        label=_('Maximum Paths'), min_value=0, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISInstance
    fieldsets = (
        FieldSet(
            'device',
            'vrf',
            'process_tag',
            'net',
            'is_type',
            'metric_style',
            name='IS-IS',
        ),
        FieldSet('import_policy', 'export_policy', name='Route Policy'),
        FieldSet(
            'lsp_lifetime',
            'lsp_refresh_interval',
            'lsp_mtu',
            'distance',
            'maximum_paths',
            'reference_bandwidth',
            'te_enabled',
            name='Attributes',
        ),
        FieldSet(
            'spf_initial_wait',
            'spf_max_wait',
            'lsp_initial_wait',
            'lsp_max_wait',
            name='Timers',
        ),
        FieldSet(
            'overload_bit',
            'overload_on_startup',
            'overload_timeout',
            'suppress_attached_bit',
            'ignore_attached_bit',
            name='Overload and Attached Bit',
        ),
        FieldSet('fast_reroute', 'microloop_avoidance', name='Fast Reroute'),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'vrf',
        'import_policy',
        'export_policy',
        'description',
        'comments',
        'is_type',
        'metric_style',
        'lsp_lifetime',
        'lsp_refresh_interval',
        'lsp_mtu',
        'distance',
        'maximum_paths',
        'reference_bandwidth',
        'te_enabled',
        'spf_initial_wait',
        'spf_max_wait',
        'lsp_initial_wait',
        'lsp_max_wait',
        'overload_bit',
        'overload_on_startup',
        'overload_timeout',
        'suppress_attached_bit',
        'ignore_attached_bit',
        'fast_reroute',
        'microloop_avoidance',
    )


class ISISInterfaceBulkEditForm(NetBoxModelBulkEditForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        label=_('IS-IS Instance'),
        required=False,
        selector=True,
    )
    address_family = forms.ChoiceField(
        label=_('Address Family'),
        choices=add_blank_choice(ISISAddressFamilyChoices),
        required=False,
    )
    circuit_type = forms.ChoiceField(
        label=_('Circuit Type'),
        choices=add_blank_choice(ISISCircuitTypeChoices),
        required=False,
    )
    network_type = forms.ChoiceField(
        label=_('Network Type'),
        choices=add_blank_choice(ISISNetworkTypeChoices),
        required=False,
    )
    metric = forms.IntegerField(label=_('Metric'), min_value=0, required=False)
    passive = forms.ChoiceField(
        label=_('Passive'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    hello_auth_type = forms.ChoiceField(
        label=_('Hello Auth Type'),
        choices=add_blank_choice(ISISAuthTypeChoices),
        required=False,
    )
    hello_auth_key = forms.CharField(label=_('Hello Auth Key'), required=False)
    bfd_enabled = _boolean(_('BFD Enabled'))
    frr_enabled = _boolean(_('FRR Enabled'))
    frr_protection = forms.ChoiceField(
        label=_('FRR Protection'),
        choices=add_blank_choice(ISISFrrProtectionChoices),
        required=False,
    )
    csnp_interval = forms.IntegerField(
        label=_('CSNP Interval'), min_value=0, required=False
    )
    retransmit_interval = forms.IntegerField(
        label=_('Retransmit Interval'), min_value=0, required=False
    )
    lsp_interval = forms.IntegerField(
        label=_('LSP Interval'), min_value=0, required=False
    )
    mesh_group = forms.CharField(label=_('Mesh Group'), required=False)
    hello_padding = _boolean(_('Hello Padding'))
    ldp_sync = _boolean(_('LDP-IGP Sync'))
    prefix_suppression = _boolean(_('Prefix Suppression'))
    three_way_handshake = _boolean(_('Three-way Handshake'))
    route_tag = forms.IntegerField(
        label=_('Route Tag'), min_value=1, max_value=4294967295, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISInterface
    fieldsets = (
        FieldSet('instance', name='IS-IS'),
        FieldSet(
            'address_family',
            'circuit_type',
            'network_type',
            'metric',
            'passive',
            'hello_auth_type',
            'hello_auth_key',
            'bfd_enabled',
            'frr_enabled',
            'frr_protection',
            name='Attributes',
        ),
        FieldSet(
            'csnp_interval',
            'retransmit_interval',
            'lsp_interval',
            'mesh_group',
            name='Timers',
        ),
        FieldSet(
            'hello_padding',
            'ldp_sync',
            'prefix_suppression',
            'three_way_handshake',
            'route_tag',
            name='Options',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'description',
        'comments',
        'circuit_type',
        'network_type',
        'metric',
        'passive',
        'hello_auth_type',
        'hello_auth_key',
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
        'three_way_handshake',
        'route_tag',
    )


class ISISLevelBulkEditForm(NetBoxModelBulkEditForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        label=_('IS-IS Instance'),
        required=False,
        selector=True,
    )
    default_metric = _integer(_('Default Metric'))
    wide_metrics_only = _boolean(_('Wide Metrics Only'))
    preference = _integer(_('Preference'))
    labeled_preference = _integer(_('Labeled Preference'))
    disabled = _boolean(_('Disabled'))
    auth_type = forms.ChoiceField(
        label=_('Auth Type'),
        choices=add_blank_choice(ISISAuthTypeChoices),
        required=False,
    )
    auth_key = forms.CharField(label=_('Auth Key'), required=False)
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISLevel
    fieldsets = (
        FieldSet('instance', name='IS-IS'),
        FieldSet(
            'default_metric',
            'wide_metrics_only',
            'preference',
            'labeled_preference',
            'disabled',
            'auth_type',
            'auth_key',
            name='Attributes',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'default_metric',
        'wide_metrics_only',
        'preference',
        'labeled_preference',
        'disabled',
        'auth_type',
        'auth_key',
        'description',
        'comments',
    )


class ISISInterfaceLevelBulkEditForm(NetBoxModelBulkEditForm):
    interface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        label=_('IS-IS Interface'),
        required=False,
        selector=True,
    )
    metric = _integer(_('Metric'))
    hello_interval = _integer(_('Hello Interval'))
    hello_multiplier = _integer(_('Hello Multiplier'))
    priority = _integer(_('Priority'))
    passive = _boolean(_('Passive'))
    hello_auth_type = forms.ChoiceField(
        label=_('Hello Auth Type'),
        choices=add_blank_choice(ISISAuthTypeChoices),
        required=False,
    )
    hello_auth_key = forms.CharField(label=_('Hello Auth Key'), required=False)
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISInterfaceLevel
    fieldsets = (
        FieldSet('interface', name='IS-IS'),
        FieldSet(
            'metric',
            'hello_interval',
            'hello_multiplier',
            'priority',
            'passive',
            'hello_auth_type',
            'hello_auth_key',
            name='Attributes',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'metric',
        'hello_interval',
        'hello_multiplier',
        'priority',
        'passive',
        'hello_auth_type',
        'hello_auth_key',
        'description',
        'comments',
    )


class ISISSegmentRoutingBulkEditForm(NetBoxModelBulkEditForm):
    enabled = _boolean(_('Enabled'))
    srv6_enabled = _boolean(_('SRv6 Enabled'))
    prefix_sid_range = forms.CharField(label=_('Prefix-SID Range'), required=False)
    srgb_start = _integer(_('SRGB Start Label'))
    srgb_range = _integer(_('SRGB Range Size'))
    srlb_start = _integer(_('SRLB Start Label'))
    srlb_range = _integer(_('SRLB Range Size'))
    maximum_sid_depth = _integer(_('Maximum SID Depth'))
    tunnel_table_pref = _integer(_('Tunnel-table Preference'))
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISSegmentRouting
    fieldsets = (
        FieldSet(
            'enabled',
            'srv6_enabled',
            'prefix_sid_range',
            'srgb_start',
            'srgb_range',
            'srlb_start',
            'srlb_range',
            'maximum_sid_depth',
            'tunnel_table_pref',
            name='Segment Routing',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
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
    )


class ISISFlexAlgoBulkEditForm(NetBoxModelBulkEditForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        label=_('IS-IS Instance'),
        required=False,
        selector=True,
    )
    metric_type = forms.ChoiceField(
        label=_('Metric Type'),
        choices=add_blank_choice(ISISFlexAlgoMetricTypeChoices),
        required=False,
    )
    priority = forms.IntegerField(
        label=_('Priority'), min_value=0, max_value=255, required=False
    )
    admin_group_exclude = forms.CharField(
        label=_('Admin-group Exclude'), required=False
    )
    admin_group_include_any = forms.CharField(
        label=_('Admin-group Include-any'), required=False
    )
    admin_group_include_all = forms.CharField(
        label=_('Admin-group Include-all'), required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISFlexAlgo
    fieldsets = (
        FieldSet('instance', name='IS-IS'),
        FieldSet(
            'metric_type',
            'priority',
            'admin_group_exclude',
            'admin_group_include_any',
            'admin_group_include_all',
            name='Flex-Algo',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'metric_type',
        'priority',
        'admin_group_exclude',
        'admin_group_include_any',
        'admin_group_include_all',
        'description',
        'comments',
    )


class ISISPrefixSIDBulkEditForm(NetBoxModelBulkEditForm):
    interface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        label=_('IS-IS Interface'),
        required=False,
        selector=True,
    )
    n_flag = _boolean(_('Node (N) Flag'))
    no_php = _boolean(_('No-PHP (P) Flag'))
    explicit_null = _boolean(_('Explicit-null (E) Flag'))
    readvertise = _boolean(_('Re-advertise (R) Flag'))
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISPrefixSID
    fieldsets = (
        FieldSet('interface', name='IS-IS'),
        FieldSet('n_flag', 'no_php', 'explicit_null', 'readvertise', name='Flags'),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'n_flag',
        'no_php',
        'explicit_null',
        'readvertise',
        'description',
        'comments',
    )


class ISISSRv6LocatorBulkEditForm(NetBoxModelBulkEditForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        label=_('IS-IS Instance'),
        required=False,
        selector=True,
    )
    algorithm = _integer(_('Algorithm'))
    is_anycast = _boolean(_('Anycast'))
    is_micro_segment = _boolean(_('Micro-segment (uSID)'))
    flavor = forms.CharField(label=_('Flavor'), required=False)
    isis_level = forms.ChoiceField(
        label=_('IS-IS Level'),
        choices=add_blank_choice(ISISLevelChoices),
        required=False,
    )
    enabled = _boolean(_('Enabled'))
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISSRv6Locator
    fieldsets = (
        FieldSet('instance', name='IS-IS'),
        FieldSet(
            'algorithm',
            'is_anycast',
            'is_micro_segment',
            'flavor',
            'isis_level',
            'enabled',
            name='Locator',
        ),
        FieldSet('description', 'comments'),
    )
    nullable_fields = (
        'algorithm',
        'is_anycast',
        'is_micro_segment',
        'flavor',
        'isis_level',
        'enabled',
        'description',
        'comments',
    )


class ISISRedistributionBulkEditForm(NetBoxModelBulkEditForm):
    address_family = forms.ChoiceField(
        label=_('Address Family'),
        choices=add_blank_choice(ISISAddressFamilyChoices),
        required=False,
    )
    level = forms.ChoiceField(
        label=_('Level'),
        choices=add_blank_choice(ISISLevelScopeChoices),
        required=False,
    )
    metric = forms.IntegerField(label=_('Metric'), min_value=1, required=False)
    metric_type = forms.ChoiceField(
        label=_('Metric Type'),
        choices=add_blank_choice(ISISRedistributionMetricTypeChoices),
        required=False,
    )
    route_tag = forms.IntegerField(
        label=_('Route Tag'), min_value=1, max_value=4294967295, required=False
    )
    route_policy = forms.CharField(
        label=_('Route Policy'), max_length=100, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISRedistribution
    fieldsets = (
        FieldSet(
            'address_family',
            'level',
            'metric',
            'metric_type',
            'route_tag',
            'route_policy',
        ),
        FieldSet('description'),
    )
    nullable_fields = ('metric', 'route_tag', 'route_policy', 'description')


class ISISSummaryAddressBulkEditForm(NetBoxModelBulkEditForm):
    level = forms.ChoiceField(
        label=_('Level'),
        choices=add_blank_choice(ISISLevelScopeChoices),
        required=False,
    )
    not_advertise = _boolean(_('Do Not Advertise'))
    metric = forms.IntegerField(label=_('Metric'), min_value=1, required=False)
    route_tag = forms.IntegerField(
        label=_('Route Tag'), min_value=1, max_value=4294967295, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISSummaryAddress
    fieldsets = (
        FieldSet('level', 'not_advertise', 'metric', 'route_tag'),
        FieldSet('description'),
    )
    nullable_fields = ('metric', 'route_tag', 'description')


class ISISRouteLeakBulkEditForm(NetBoxModelBulkEditForm):
    route_policy = forms.CharField(
        label=_('Route Policy'), max_length=100, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = ISISRouteLeak
    fieldsets = (FieldSet('route_policy'), FieldSet('description'))
    nullable_fields = ('route_policy', 'description')
