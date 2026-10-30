from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'OSPFInstancePanel',
    'OSPFInstanceAdvancedPanel',
    'OSPFAuthenticationPanel',
    'OSPFAreaPanel',
    'OSPFInterfacePanel',
    'OSPFInterfaceSettingsPanel',
    'OSPFNetworkPanel',
    'OSPFRedistributionPanel',
    'OSPFVirtualLinkPanel',
    'OSPFSummaryAddressPanel',
    'OSPFNeighborPanel',
    'OSPFAreaRangePanel',
    'OSPFPrefixSIDPanel',
)


class OSPFInstancePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    router_id = attrs.TextAttr('router_id', label=_('Router ID'))
    device = attrs.RelatedObjectAttr('device', label=_('Device'))
    vrf = attrs.RelatedObjectAttr('vrf', linkify=True)
    address_family = attrs.ChoiceAttr('address_family', label=_('Address Family'))
    default_originate = attrs.BooleanAttr(
        'default_originate', label=_('Default Originate')
    )
    default_originate_always = attrs.BooleanAttr(
        'default_originate_always', label=_('Default Originate Always')
    )
    default_originate_metric = attrs.NumericAttr(
        'default_originate_metric', label=_('Default Originate Metric')
    )
    default_originate_metric_type = attrs.ChoiceAttr(
        'default_originate_metric_type', label=_('Default Originate Metric Type')
    )
    import_policy = attrs.RelatedObjectAttr(
        'import_policy', linkify=True, label=_('Import Policy')
    )
    export_policy = attrs.RelatedObjectAttr(
        'export_policy', linkify=True, label=_('Export Policy')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFInstanceAdvancedPanel(panels.ObjectAttributesPanel):
    spf_initial_delay = attrs.NumericAttr(
        'spf_initial_delay', label=_('SPF Initial Delay')
    )
    spf_short_delay = attrs.NumericAttr('spf_short_delay', label=_('SPF Short Delay'))
    spf_long_delay = attrs.NumericAttr('spf_long_delay', label=_('SPF Long Delay'))
    spf_time_to_learn = attrs.NumericAttr(
        'spf_time_to_learn', label=_('SPF Time to Learn')
    )
    spf_holddown = attrs.NumericAttr('spf_holddown', label=_('SPF Holddown'))
    lsa_min_interval = attrs.NumericAttr(
        'lsa_min_interval', label=_('LSA Minimum Interval')
    )
    lsa_min_arrival = attrs.NumericAttr(
        'lsa_min_arrival', label=_('LSA Minimum Arrival')
    )
    max_metric_router_lsa = attrs.BooleanAttr(
        'max_metric_router_lsa', label=_('Max Metric (Stub Router)')
    )
    max_metric_on_startup = attrs.NumericAttr(
        'max_metric_on_startup', label=_('Max Metric On Startup')
    )
    graceful_restart = attrs.ChoiceAttr('graceful_restart', label=_('Graceful Restart'))
    graceful_restart_period = attrs.NumericAttr(
        'graceful_restart_period', label=_('Graceful Restart Period')
    )
    graceful_restart_helper = attrs.BooleanAttr(
        'graceful_restart_helper', label=_('Graceful Restart Helper')
    )
    graceful_restart_helper_strict_lsa_checking = attrs.BooleanAttr(
        'graceful_restart_helper_strict_lsa_checking', label=_('Strict LSA Checking')
    )
    rfc1583_compatibility = attrs.BooleanAttr(
        'rfc1583_compatibility', label=_('RFC 1583 Compatibility')
    )
    log_adjacency_changes = attrs.BooleanAttr(
        'log_adjacency_changes', label=_('Log Adjacency Changes')
    )
    log_adjacency_changes_detail = attrs.BooleanAttr(
        'log_adjacency_changes_detail', label=_('Log Adjacency Changes in Detail')
    )
    bfd_all_interfaces = attrs.BooleanAttr(
        'bfd_all_interfaces', label=_('BFD on All Interfaces')
    )
    passive_interface_default = attrs.BooleanAttr(
        'passive_interface_default', label=_('Passive Interfaces by Default')
    )
    max_lsa = attrs.NumericAttr('max_lsa', label=_('Max LSAs'))
    max_lsa_threshold = attrs.NumericAttr(
        'max_lsa_threshold', label=_('Max LSAs Warning Threshold')
    )
    max_lsa_warning_only = attrs.BooleanAttr(
        'max_lsa_warning_only', label=_('Max LSAs Warning Only')
    )
    external_lsdb_limit = attrs.NumericAttr(
        'external_lsdb_limit', label=_('External LSDB Limit')
    )
    exit_overflow_interval = attrs.NumericAttr(
        'exit_overflow_interval', label=_('Exit Overflow Interval')
    )
    reference_bandwidth = attrs.NumericAttr(
        'reference_bandwidth', label=_('Reference Bandwidth')
    )
    maximum_paths = attrs.NumericAttr('maximum_paths', label=_('Maximum Paths'))
    distance_intra_area = attrs.NumericAttr(
        'distance_intra_area', label=_('Distance (Intra-Area)')
    )
    distance_inter_area = attrs.NumericAttr(
        'distance_inter_area', label=_('Distance (Inter-Area)')
    )
    distance_external = attrs.NumericAttr(
        'distance_external', label=_('Distance (External)')
    )
    default_metric = attrs.NumericAttr('default_metric', label=_('Default Metric'))
    ospf_instance_id = attrs.NumericAttr('ospf_instance_id', label=_('Instance ID'))
    ldp_sync = attrs.BooleanAttr('ldp_sync', label=_('LDP-IGP Synchronization'))
    ldp_sync_holddown = attrs.NumericAttr(
        'ldp_sync_holddown', label=_('LDP Sync Hold-down')
    )
    segment_routing = attrs.BooleanAttr('segment_routing', label=_('Segment Routing'))
    srgb_start = attrs.NumericAttr('srgb_start', label=_('SRGB Start'))
    srgb_size = attrs.NumericAttr('srgb_size', label=_('SRGB Size'))
    opaque_capability = attrs.BooleanAttr('opaque_capability', label=_('Opaque LSAs'))
    te_router_address = attrs.TextAttr(
        'te_router_address', label=_('TE Router Address')
    )


class OSPFAuthenticationPanel(panels.ObjectAttributesPanel):
    authentication = attrs.ChoiceAttr('authentication', label=_('Authentication'))
    authentication_key_id = attrs.NumericAttr(
        'authentication_key_id', label=_('Key ID')
    )
    message_digest_algorithm = attrs.ChoiceAttr(
        'message_digest_algorithm', label=_('Message Digest Algorithm')
    )
    key_chain = attrs.TextAttr('key_chain', label=_('Key Chain'))
    passphrase = attrs.TextAttr('passphrase', label=_('Passphrase'))
    md5_digest = attrs.TextAttr('md5_digest', label=_('MD5 Digest'))


class OSPFAreaPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    area_id = attrs.NumericAttr('area_id', label=_('Area ID'))
    area_type = attrs.ChoiceAttr('area_type', label=_('Area Type'))
    default_cost = attrs.NumericAttr('default_cost', label=_('Default Cost'))
    nssa_translate_always = attrs.BooleanAttr(
        'nssa_translate_always', label=_('Translate Type 7 Always')
    )
    nssa_no_redistribution = attrs.BooleanAttr(
        'nssa_no_redistribution', label=_('No Redistribution')
    )
    traffic_engineering = attrs.BooleanAttr(
        'traffic_engineering', label=_('Traffic Engineering')
    )
    fast_reroute = attrs.BooleanAttr('fast_reroute', label=_('Fast Reroute'))
    nssa_default_originate = attrs.BooleanAttr(
        'nssa_default_originate', label=_('Default Information Originate')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFInterfacePanel(panels.ObjectAttributesPanel):
    area = attrs.RelatedObjectAttr('area', label=_('Area'))
    device = attrs.RelatedObjectAttr('instance.device', label=_('Device'))
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'))
    interface = attrs.RelatedObjectAttr('interface', label=_('Interface'))


class OSPFInterfaceSettingsPanel(panels.ObjectAttributesPanel):
    priority = attrs.NumericAttr('priority', label=_('Priority'))
    cost = attrs.NumericAttr('cost', label=_('Cost'))
    hello_interval = attrs.NumericAttr('hello_interval', label=_('Hello Interval'))
    dead_interval = attrs.NumericAttr('dead_interval', label=_('Dead Interval'))
    retransmit_interval = attrs.NumericAttr(
        'retransmit_interval', label=_('Retransmit Interval')
    )
    transmit_delay = attrs.NumericAttr('transmit_delay', label=_('Transmit Delay'))
    ttl_security = attrs.BooleanAttr('ttl_security', label=_('TTL Security'))
    ttl_security_hops = attrs.NumericAttr(
        'ttl_security_hops', label=_('TTL Security Hops')
    )
    mtu = attrs.NumericAttr('interface.mtu', label=_('MTU'))
    unnumbered = attrs.BooleanAttr('unnumbered', label=_('Unnumbered'))
    mtu_ignore = attrs.BooleanAttr('mtu_ignore', label=_('MTU Ignore'))
    adjacency_sid = attrs.NumericAttr('adjacency_sid', label=_('Adjacency SID'))
    fast_reroute = attrs.ChoiceAttr('fast_reroute', label=_('Fast Reroute'))
    ldp_sync = attrs.BooleanAttr('ldp_sync', label=_('LDP-IGP Synchronization'))
    te_metric = attrs.NumericAttr('te_metric', label=_('TE Metric'))
    te_max_reservable_bandwidth = attrs.NumericAttr(
        'te_max_reservable_bandwidth', label=_('TE Maximum Reservable Bandwidth')
    )
    te_admin_group = attrs.NumericAttr(
        'te_admin_group', label=_('TE Administrative Group')
    )
    prefix_suppression = attrs.BooleanAttr(
        'prefix_suppression', label=_('Prefix Suppression')
    )
    database_filter_all_out = attrs.BooleanAttr(
        'database_filter_all_out', label=_('Database Filter All Out')
    )
    flood_reduction = attrs.BooleanAttr('flood_reduction', label=_('Flood Reduction'))
    demand_circuit = attrs.BooleanAttr('demand_circuit', label=_('Demand Circuit'))
    network_type = attrs.ChoiceAttr('network_type', label=_('Network Type'))
    passive = attrs.BooleanAttr('passive', label=_('Passive'))
    bfd = attrs.BooleanAttr('bfd', label=_('BFD'))
    authentication = attrs.ChoiceAttr('authentication', label=_('Authentication'))
    authentication_key_id = attrs.NumericAttr(
        'authentication_key_id', label=_('Key ID')
    )
    message_digest_algorithm = attrs.ChoiceAttr(
        'message_digest_algorithm', label=_('Message Digest Algorithm')
    )
    key_chain = attrs.TextAttr('key_chain', label=_('Key Chain'))
    passphrase = attrs.TextAttr('passphrase', label=_('Passphrase'))
    md5_digest = attrs.TextAttr('md5_digest', label=_('MD5 Digest'))
    effective_authentication = attrs.TextAttr(
        'effective_authentication', label=_('Authentication in Use')
    )
    authentication_source = attrs.TextAttr(
        'authentication_source', label=_('Authentication Set At')
    )


class OSPFNetworkPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr(
        'ospf_interface.instance', label=_('Instance'), linkify=True
    )
    area = attrs.RelatedObjectAttr('ospf_interface.area', label=_('Area'), linkify=True)
    ospf_interface = attrs.RelatedObjectAttr(
        'ospf_interface', label=_('OSPF Interface'), linkify=True
    )
    ip_address = attrs.RelatedObjectAttr(
        'ip_address', label=_('IP Address'), linkify=True
    )
    subnet = attrs.TextAttr('subnet', label=_('Subnet'))
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFRedistributionPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    protocol = attrs.ChoiceAttr('protocol', label=_('Protocol'))
    source = attrs.TextAttr('source', label=_('Source'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    metric_type = attrs.ChoiceAttr('metric_type', label=_('Metric Type'))
    subnets = attrs.BooleanAttr('subnets', label=_('Subnets'))
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    ospf_match = attrs.TextAttr('ospf_match_display', label=_('OSPF Route Types'))
    route_policy = attrs.RelatedObjectAttr(
        'route_policy', linkify=True, label=_('Route Policy')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFVirtualLinkPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    transit_area = attrs.RelatedObjectAttr(
        'transit_area', label=_('Transit Area'), linkify=True
    )
    remote_router_id = attrs.TextAttr('remote_router_id', label=_('Remote Router ID'))
    hello_interval = attrs.NumericAttr('hello_interval', label=_('Hello Interval'))
    dead_interval = attrs.NumericAttr('dead_interval', label=_('Dead Interval'))
    retransmit_interval = attrs.NumericAttr(
        'retransmit_interval', label=_('Retransmit Interval')
    )
    transmit_delay = attrs.NumericAttr('transmit_delay', label=_('Transmit Delay'))
    ttl_security = attrs.BooleanAttr('ttl_security', label=_('TTL Security'))
    ttl_security_hops = attrs.NumericAttr(
        'ttl_security_hops', label=_('TTL Security Hops')
    )
    effective_authentication = attrs.TextAttr(
        'effective_authentication', label=_('Authentication in Use')
    )
    authentication_source = attrs.TextAttr(
        'authentication_source', label=_('Authentication Set At')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFSummaryAddressPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    not_advertise = attrs.BooleanAttr('not_advertise', label=_('Do Not Advertise'))
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFNeighborPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr(
        'ospf_interface.instance', label=_('Instance'), linkify=True
    )
    ospf_interface = attrs.RelatedObjectAttr(
        'ospf_interface', label=_('OSPF Interface'), linkify=True
    )
    ip_address = attrs.TextAttr('ip_address', label=_('IP Address'))
    priority = attrs.NumericAttr('priority', label=_('Priority'))
    poll_interval = attrs.NumericAttr('poll_interval', label=_('Poll Interval'))
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFAreaRangePanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr(
        'area.instance', label=_('Instance'), linkify=True
    )
    area = attrs.RelatedObjectAttr('area', label=_('Area'), linkify=True)
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    range_type = attrs.ChoiceAttr('range_type', label=_('Range Type'))
    advertise = attrs.BooleanAttr('advertise', label=_('Advertise'))
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFPrefixSIDPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    sid_type = attrs.ChoiceAttr('sid_type', label=_('SID Type'))
    sid = attrs.NumericAttr('sid', label=_('SID'))
    algorithm = attrs.ChoiceAttr('algorithm', label=_('Algorithm'))
    node_sid = attrs.BooleanAttr('node_sid', label=_('Node SID'))
    no_php = attrs.BooleanAttr('no_php', label=_('No PHP'))
    explicit_null = attrs.BooleanAttr('explicit_null', label=_('Explicit Null'))
    description = attrs.TextAttr('description', label=_('Description'))
