# SPDX-License-Identifier: Apache-2.0

from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels
from netbox_routing_protocols.ui.attributes import ContentTypeAttribute

__all__ = (
    'ISISInstancePanel',
    'ISISInstanceSettingsPanel',
    'ISISInterfacePanel',
    'ISISInterfaceSettingsPanel',
    'ISISSettingPanel',
    'ISISLevelPanel',
    'ISISInterfaceLevelPanel',
    'ISISSegmentRoutingPanel',
    'ISISFlexAlgoPanel',
    'ISISPrefixSIDPanel',
    'ISISSRv6LocatorPanel',
    'ISISSRMappingEntryPanel',
    'ISISAdjacencySIDPanel',
    'ISISAreaAddressPanel',
    'ISISRedistributionPanel',
    'ISISSummaryAddressPanel',
    'ISISRouteLeakPanel',
)


class ISISFlexAlgoPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', linkify=True, label=_('Instance'))
    algo_id = attrs.NumericAttr('algo_id', label=_('Algorithm ID'))
    metric_type = attrs.TextAttr('metric_type', label=_('Metric Type'))
    priority = attrs.NumericAttr('priority', label=_('Priority'))
    admin_group_exclude = attrs.TextAttr(
        'admin_group_exclude', label=_('Admin-group Exclude')
    )
    admin_group_include_any = attrs.TextAttr(
        'admin_group_include_any', label=_('Admin-group Include-Any')
    )
    admin_group_include_all = attrs.TextAttr(
        'admin_group_include_all', label=_('Admin-group Include-All')
    )


class ISISPrefixSIDPanel(panels.ObjectAttributesPanel):
    interface = attrs.RelatedObjectAttr('interface', linkify=True, label=_('Interface'))
    algorithm = attrs.NumericAttr('algorithm', label=_('Algorithm'))
    sid_index = attrs.NumericAttr('sid_index', label=_('SID Index'))
    sid_label = attrs.NumericAttr('sid_label', label=_('SID Label'))
    n_flag = attrs.BooleanAttr('n_flag', label=_('Node (N) Flag'))
    no_php = attrs.BooleanAttr('no_php', label=_('No-PHP (P) Flag'))
    explicit_null = attrs.BooleanAttr(
        'explicit_null', label=_('Explicit-null (E) Flag')
    )
    readvertise = attrs.BooleanAttr('readvertise', label=_('Re-advertise (R) Flag'))


class ISISSRv6LocatorPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', linkify=True, label=_('Instance'))
    name = attrs.TextAttr('name', label=_('Name'))
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    algorithm = attrs.NumericAttr('algorithm', label=_('Algorithm'))
    is_anycast = attrs.BooleanAttr('is_anycast', label=_('Anycast'))
    is_micro_segment = attrs.BooleanAttr(
        'is_micro_segment', label=_('Micro-segment (uSID)')
    )
    flavor = attrs.TextAttr('flavor', label=_('Flavor'))
    isis_level = attrs.ChoiceAttr('isis_level', label=_('IS-IS Level'))
    block_length = attrs.NumericAttr('block_length', label=_('Block Length'))
    node_length = attrs.NumericAttr('node_length', label=_('Node Length'))
    function_length = attrs.NumericAttr('function_length', label=_('Function Length'))
    argument_length = attrs.NumericAttr('argument_length', label=_('Argument Length'))
    enabled = attrs.BooleanAttr('enabled', label=_('Enabled'))


class ISISLevelPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', linkify=True, label=_('Instance'))
    level = attrs.NumericAttr('level', label=_('Level'))
    default_metric = attrs.NumericAttr('default_metric', label=_('Default Metric'))
    wide_metrics_only = attrs.BooleanAttr(
        'wide_metrics_only', label=_('Wide Metrics Only')
    )
    preference = attrs.NumericAttr('preference', label=_('Preference'))
    labeled_preference = attrs.NumericAttr(
        'labeled_preference', label=_('Labeled Preference')
    )
    disabled = attrs.BooleanAttr('disabled', label=_('Disabled'))
    auth_type = attrs.ChoiceAttr('auth_type', label=_('Auth Type'))
    auth_key = attrs.TextAttr('auth_key', label=_('Auth Key'))
    auth_key_id = attrs.NumericAttr('auth_key_id', label=_('Auth Key ID'))
    auth_key_chain = attrs.TextAttr('auth_key_chain', label=_('Auth Key Chain'))
    auth_send_only = attrs.BooleanAttr('auth_send_only', label=_('Auth Send Only'))


class ISISInterfaceLevelPanel(panels.ObjectAttributesPanel):
    interface = attrs.RelatedObjectAttr('interface', linkify=True, label=_('Interface'))
    level = attrs.NumericAttr('level', label=_('Level'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    hello_interval = attrs.NumericAttr('hello_interval', label=_('Hello Interval'))
    hello_multiplier = attrs.NumericAttr(
        'hello_multiplier', label=_('Hello Multiplier')
    )
    priority = attrs.NumericAttr('priority', label=_('Priority'))
    passive = attrs.BooleanAttr('passive', label=_('Passive'))
    hello_auth_type = attrs.ChoiceAttr('hello_auth_type', label=_('Hello Auth Type'))
    hello_auth_key_id = attrs.NumericAttr(
        'hello_auth_key_id', label=_('Hello Auth Key ID')
    )
    hello_auth_key_chain = attrs.TextAttr(
        'hello_auth_key_chain', label=_('Hello Auth Key Chain')
    )
    hello_auth_send_only = attrs.BooleanAttr(
        'hello_auth_send_only', label=_('Hello Auth Send Only')
    )


class ISISSegmentRoutingPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', linkify=True, label=_('Instance'))
    enabled = attrs.BooleanAttr('enabled', label=_('Enabled'))
    srv6_enabled = attrs.BooleanAttr('srv6_enabled', label=_('SRv6 Enabled'))
    prefix_sid_range = attrs.TextAttr('prefix_sid_range', label=_('Prefix-SID Range'))
    srgb_start = attrs.NumericAttr('srgb_start', label=_('SRGB Start'))
    srgb_range = attrs.NumericAttr('srgb_range', label=_('SRGB Range'))
    srlb_start = attrs.NumericAttr('srlb_start', label=_('SRLB Start'))
    srlb_range = attrs.NumericAttr('srlb_range', label=_('SRLB Range'))
    maximum_sid_depth = attrs.NumericAttr(
        'maximum_sid_depth', label=_('Maximum SID Depth')
    )
    tunnel_table_pref = attrs.NumericAttr(
        'tunnel_table_pref', label=_('Tunnel-Table Pref')
    )


class ISISInstancePanel(panels.ObjectAttributesPanel):
    device = attrs.RelatedObjectAttr('device', linkify=True, label=_('Device'))
    vrf = attrs.RelatedObjectAttr('vrf', linkify=True)
    process_tag = attrs.TextAttr('process_tag', label=_('Process Tag'))
    net = attrs.TextAttr('net', label=_('NET'))
    duplicate_system_ids = attrs.TextAttr(
        'duplicate_system_ids_display', label=_('Same System ID In')
    )
    is_type = attrs.ChoiceAttr('is_type', label=_('IS Type'))
    import_policy = attrs.RelatedObjectAttr(
        'import_policy', linkify=True, label=_('Import Policy')
    )
    export_policy = attrs.RelatedObjectAttr(
        'export_policy', linkify=True, label=_('Export Policy')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class ISISInstanceSettingsPanel(panels.ObjectAttributesPanel):
    metric_style = attrs.ChoiceAttr('metric_style', label=_('Metric Style'))
    area_auth_type = attrs.ChoiceAttr('area_auth_type', label=_('Area Auth Type'))
    area_auth_key = attrs.TextAttr('area_auth_key', label=_('Area Auth Key'))
    area_auth_key_id = attrs.NumericAttr(
        'area_auth_key_id', label=_('Area Auth Key ID')
    )
    area_auth_key_chain = attrs.TextAttr(
        'area_auth_key_chain', label=_('Area Auth Key Chain')
    )
    area_auth_send_only = attrs.BooleanAttr(
        'area_auth_send_only', label=_('Area Auth Send Only')
    )
    domain_auth_type = attrs.ChoiceAttr('domain_auth_type', label=_('Domain Auth Type'))
    domain_auth_key = attrs.TextAttr('domain_auth_key', label=_('Domain Auth Key'))
    domain_auth_key_id = attrs.NumericAttr(
        'domain_auth_key_id', label=_('Domain Auth Key ID')
    )
    domain_auth_key_chain = attrs.TextAttr(
        'domain_auth_key_chain', label=_('Domain Auth Key Chain')
    )
    domain_auth_send_only = attrs.BooleanAttr(
        'domain_auth_send_only', label=_('Domain Auth Send Only')
    )
    overload_bit = attrs.BooleanAttr('overload_bit', label=_('Overload Bit'))
    overload_on_startup = attrs.BooleanAttr(
        'overload_on_startup', label=_('Overload on Startup')
    )
    overload_timeout = attrs.NumericAttr(
        'overload_timeout', label=_('Overload Timeout')
    )
    suppress_attached_bit = attrs.BooleanAttr(
        'suppress_attached_bit', label=_('Suppress Attached Bit')
    )
    ignore_attached_bit = attrs.BooleanAttr(
        'ignore_attached_bit', label=_('Ignore Attached Bit')
    )
    spf_initial_wait = attrs.NumericAttr(
        'spf_initial_wait', label=_('SPF Initial Wait')
    )
    spf_max_wait = attrs.NumericAttr('spf_max_wait', label=_('SPF Max Wait'))
    lsp_initial_wait = attrs.NumericAttr(
        'lsp_initial_wait', label=_('LSP-gen Initial Wait')
    )
    lsp_max_wait = attrs.NumericAttr('lsp_max_wait', label=_('LSP-gen Max Wait'))
    lsp_lifetime = attrs.NumericAttr('lsp_lifetime', label=_('LSP Lifetime'))
    lsp_refresh_interval = attrs.NumericAttr(
        'lsp_refresh_interval', label=_('LSP Refresh Interval')
    )
    lsp_mtu = attrs.NumericAttr('lsp_mtu', label=_('LSP MTU'))
    te_enabled = attrs.BooleanAttr('te_enabled', label=_('Traffic Engineering'))
    fast_reroute = attrs.ChoiceAttr('fast_reroute', label=_('Fast Reroute'))
    microloop_avoidance = attrs.BooleanAttr(
        'microloop_avoidance', label=_('Micro-loop Avoidance')
    )
    distance = attrs.NumericAttr('distance', label=_('Distance'))
    maximum_paths = attrs.NumericAttr('maximum_paths', label=_('Maximum Paths'))
    reference_bandwidth = attrs.NumericAttr(
        'reference_bandwidth', label=_('Reference Bandwidth')
    )


class ISISInterfacePanel(panels.ObjectAttributesPanel):
    device = attrs.RelatedObjectAttr('instance.device', linkify=True, label=_('Device'))
    instance = attrs.RelatedObjectAttr('instance', linkify=True, label=_('Instance'))
    interface = attrs.RelatedObjectAttr('interface', linkify=True, label=_('Interface'))
    address_family = attrs.ChoiceAttr('address_family', label=_('Address Family'))


class ISISInterfaceSettingsPanel(panels.ObjectAttributesPanel):
    circuit_type = attrs.ChoiceAttr('circuit_type', label=_('Circuit Type'))
    network_type = attrs.ChoiceAttr('network_type', label=_('Network Type'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    passive = attrs.BooleanAttr('passive', label=_('Passive'))
    bfd_enabled = attrs.BooleanAttr('bfd_enabled', label=_('BFD Enabled'))
    frr_enabled = attrs.BooleanAttr('frr_enabled', label=_('FRR Enabled'))
    frr_protection = attrs.ChoiceAttr('frr_protection', label=_('FRR Protection'))
    csnp_interval = attrs.NumericAttr('csnp_interval', label=_('CSNP Interval'))
    retransmit_interval = attrs.NumericAttr(
        'retransmit_interval', label=_('Retransmit Interval')
    )
    lsp_interval = attrs.NumericAttr('lsp_interval', label=_('LSP Interval'))
    mesh_group = attrs.TextAttr('mesh_group', label=_('Mesh Group'))
    hello_padding = attrs.BooleanAttr('hello_padding', label=_('Hello Padding'))
    ldp_sync = attrs.BooleanAttr('ldp_sync', label=_('LDP-IGP Sync'))
    prefix_suppression = attrs.BooleanAttr(
        'prefix_suppression', label=_('Prefix Suppression')
    )
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    three_way_handshake = attrs.BooleanAttr(
        'three_way_handshake', label=_('Three-way Handshake')
    )
    admin_group = attrs.TextAttr('admin_group', label=_('Admin Group'))
    te_metric = attrs.NumericAttr('te_metric', label=_('TE Metric'))
    delay_metric = attrs.NumericAttr('delay_metric', label=_('Delay Metric'))
    hello_auth_type = attrs.ChoiceAttr('hello_auth_type', label=_('Hello Auth Type'))
    hello_auth_key = attrs.TextAttr('hello_auth_key', label=_('Hello Auth Key'))
    hello_auth_key_id = attrs.NumericAttr(
        'hello_auth_key_id', label=_('Hello Auth Key ID')
    )
    hello_auth_key_chain = attrs.TextAttr(
        'hello_auth_key_chain', label=_('Hello Auth Key Chain')
    )
    hello_auth_send_only = attrs.BooleanAttr(
        'hello_auth_send_only', label=_('Hello Auth Send Only')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class ISISSettingPanel(panels.ObjectAttributesPanel):
    assigned_object_type = ContentTypeAttribute('assigned_object_type', label=_('Type'))
    assigned_object = attrs.RelatedObjectAttr('assigned_object', linkify=True)
    name = attrs.TextAttr('key', label=_('Name'))
    value = attrs.TextAttr('value', label=_('Value'))


class ISISRedistributionPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    address_family = attrs.ChoiceAttr('address_family', label=_('Address Family'))
    protocol = attrs.ChoiceAttr('protocol', label=_('Protocol'))
    source = attrs.TextAttr('source', label=_('Source'))
    level = attrs.ChoiceAttr('level', label=_('Level'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    metric_type = attrs.ChoiceAttr('metric_type', label=_('Metric Type'))
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    route_policy = attrs.TextAttr('route_policy', label=_('Route Policy'))
    description = attrs.TextAttr('description', label=_('Description'))


class ISISSummaryAddressPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    level = attrs.ChoiceAttr('level', label=_('Level'))
    not_advertise = attrs.BooleanAttr('not_advertise', label=_('Do Not Advertise'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    description = attrs.TextAttr('description', label=_('Description'))


class ISISRouteLeakPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    address_family = attrs.ChoiceAttr('address_family', label=_('Address Family'))
    route_policy = attrs.TextAttr('route_policy', label=_('Route Policy'))
    description = attrs.TextAttr('description', label=_('Description'))


class ISISAreaAddressPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    net = attrs.TextAttr('net', label=_('NET'))
    area = attrs.TextAttr('area', label=_('Area'))
    system_id = attrs.TextAttr('system_id', label=_('System ID'))
    description = attrs.TextAttr('description', label=_('Description'))


class ISISSRMappingEntryPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    range_size = attrs.NumericAttr('range_size', label=_('Range Size'))
    sid_index = attrs.NumericAttr('sid_index', label=_('SID Index'))
    sid_label = attrs.NumericAttr('sid_label', label=_('SID Label'))
    algorithm = attrs.NumericAttr('algorithm', label=_('Algorithm'))
    level = attrs.ChoiceAttr('level', label=_('Level'))
    description = attrs.TextAttr('description', label=_('Description'))


class ISISAdjacencySIDPanel(panels.ObjectAttributesPanel):
    interface = attrs.RelatedObjectAttr('interface', label=_('Interface'), linkify=True)
    sid_label = attrs.NumericAttr('sid_label', label=_('SID Label'))
    protected = attrs.BooleanAttr('protected', label=_('Protected'))
    description = attrs.TextAttr('description', label=_('Description'))
