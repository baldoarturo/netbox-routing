from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'BGPPolicyFilteringPanel',
    'BGPRoutePolicyPanel',
    'BGPGracefulRestartPanel',
    'BGPPeerAddressFamilyOptionsPanel',
    'BGPNoPolicyPanel',
    'BGPEffectivePolicyPanel',
    'BGPInstancePanel',
    'BGPInstanceRoutingPanel',
    'BGPInstanceVRFPanel',
    'BGPListenRangePanel',
    'BGPRedistributionPanel',
    'BGPOriginatedNetworkPanel',
    'BGPAggregatePanel',
    'BGPAddressFamilyPanel',
    'BGPAddressFamilyOptionsPanel',
    'BGPPeerGroupPanel',
    'BGPPeerPanel',
    'BGPPeerSessionPanel',
    'BGPPeerAddressFamilyPanel',
    'BFDProfilePanel',
    'BFDProfileSessionPanel',
)


class BGPInstancePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    device = attrs.RelatedObjectAttr('device', linkify=True)
    vrf = attrs.RelatedObjectAttr('vrf', linkify=True)
    asn = attrs.RelatedObjectAttr('asn', label=_('ASN'), linkify=True)
    router_id = attrs.TextAttr('router_id', label=_('Router ID'))
    asdot = attrs.BooleanAttr('asdot', label=_('AS Dot Notation'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPInstanceRoutingPanel(panels.ObjectAttributesPanel):
    """Route reflector (RFC 4456) and confederation (RFC 5065)"""

    cluster_id = attrs.TextAttr('cluster_id', label=_('Cluster ID'))
    confederation_identifier = attrs.RelatedObjectAttr(
        'confederation_identifier', label=_('Confederation Identifier'), linkify=True
    )
    confederation_peers = attrs.RelatedObjectListAttr(
        'confederation_peers', label=_('Confederation Peers'), linkify=True
    )


class BGPInstanceVRFPanel(panels.ObjectAttributesPanel):
    """The RD and the route targets come from the VRF (NetBox IPAM, RFC 4364)"""

    rd = attrs.TextAttr('vrf_route_distinguisher', label=_('Route Distinguisher'))
    import_targets = attrs.TextAttr(
        'vrf_import_targets_display', label=_('Import Targets')
    )
    export_targets = attrs.TextAttr(
        'vrf_export_targets_display', label=_('Export Targets')
    )


class BGPRedistributionPanel(panels.ObjectAttributesPanel):
    address_family = attrs.RelatedObjectAttr('address_family', linkify=True)
    protocol = attrs.ChoiceAttr('protocol', label=_('Protocol'))
    source = attrs.RelatedObjectAttr('source', linkify=True, label=_('Source'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    route_policy = attrs.RelatedObjectAttr(
        'route_policy', linkify=True, label=_('Route Policy')
    )
    ospf_match = attrs.TextAttr('ospf_match_display', label=_('OSPF Route Types'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPOriginatedNetworkPanel(panels.ObjectAttributesPanel):
    address_family = attrs.RelatedObjectAttr('address_family', linkify=True)
    prefix = attrs.RelatedObjectAttr('prefix', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPAggregatePanel(panels.ObjectAttributesPanel):
    address_family = attrs.RelatedObjectAttr('address_family', linkify=True)
    prefix = attrs.RelatedObjectAttr('prefix', linkify=True)
    summary_only = attrs.BooleanAttr('summary_only', label=_('Summary Only'))
    as_set = attrs.BooleanAttr('as_set', label=_('AS Set'))
    description = attrs.TextAttr('description', label=_('Description'))


class BGPListenRangePanel(panels.ObjectAttributesPanel):
    peer_group = attrs.RelatedObjectAttr('peer_group', linkify=True)
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    prefix = attrs.RelatedObjectAttr('prefix', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPAddressFamilyPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    address_family = attrs.ChoiceAttr('address_family', label=_('Address Family'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPAddressFamilyOptionsPanel(panels.ObjectAttributesPanel):
    maximum_paths = attrs.NumericAttr('maximum_paths', label=_('Maximum Paths'))
    default_metric = attrs.NumericAttr('default_metric', label=_('Default Metric'))
    default_originate = attrs.BooleanAttr(
        'default_originate', label=_('Default Originate')
    )
    auto_summary = attrs.BooleanAttr('auto_summary', label=_('Auto Summary'))
    distance_ebgp = attrs.NumericAttr('distance_ebgp', label=_('eBGP Distance'))
    distance_ibgp = attrs.NumericAttr('distance_ibgp', label=_('iBGP Distance'))
    additional_paths_send = attrs.BooleanAttr(
        'additional_paths_send', label=_('Additional Paths (send)')
    )
    additional_paths_receive = attrs.BooleanAttr(
        'additional_paths_receive', label=_('Additional Paths (receive)')
    )
    additional_paths_install = attrs.BooleanAttr(
        'additional_paths_install', label=_('Additional Paths (install)')
    )
    long_lived_stale_time = attrs.NumericAttr(
        'long_lived_stale_time', label=_('Long-Lived Graceful Restart Stale Time')
    )


class BGPPeerGroupPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    listen_limit = attrs.NumericAttr('listen_limit', label=_('Listen Limit'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPPeerPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    peer = attrs.RelatedObjectAttr('peer', linkify=True)
    interface = attrs.RelatedObjectAttr('interface', linkify=True)
    source = attrs.RelatedObjectAttr('source', linkify=True)
    peer_group = attrs.RelatedObjectAttr('peer_group', linkify=True)
    status = attrs.ChoiceAttr('status', label=_('Status'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPPeerSessionPanel(panels.ObjectAttributesPanel):
    """Session options of a peer or a peer group (a peer left empty inherits the group)"""

    remote_as = attrs.RelatedObjectAttr('remote_as', label=_('Remote AS'), linkify=True)
    local_as = attrs.RelatedObjectAttr('local_as', label=_('Local AS'), linkify=True)
    enabled = attrs.BooleanAttr('enabled', label=_('Enabled'))
    bfd = attrs.RelatedObjectAttr('bfd', label=_('BFD Profile'), linkify=True)
    ebgp_multihop = attrs.NumericAttr('ebgp_multihop', label=_('eBGP Multihop'))
    ttl_security_hops = attrs.NumericAttr(
        'ttl_security_hops', label=_('TTL Security Hops')
    )
    passive = attrs.BooleanAttr('passive', label=_('Passive'))
    as_override = attrs.BooleanAttr('as_override', label=_('AS Override'))
    soft_reconfiguration_inbound = attrs.BooleanAttr(
        'soft_reconfiguration_inbound', label=_('Soft Reconfiguration Inbound')
    )
    graceful_shutdown = attrs.BooleanAttr(
        'graceful_shutdown', label=_('Graceful Shutdown')
    )
    route_reflector_client = attrs.BooleanAttr(
        'route_reflector_client', label=_('Route Reflector Client')
    )
    extended_nexthop = attrs.BooleanAttr(
        'extended_nexthop', label=_('Extended Next Hop')
    )
    passphrase = attrs.TextAttr('passphrase', label=_('Passphrase'))
    md5_digest = attrs.TextAttr('md5_digest', label=_('MD5 Digest'))
    keepalive = attrs.NumericAttr('keepalive', label=_('Keepalive Time'))
    hold_time = attrs.NumericAttr('hold_time', label=_('Hold Time'))


class BGPRoutePolicyPanel(panels.ObjectAttributesPanel):
    """The import and export policy set on the object itself"""

    import_policy = attrs.RelatedObjectAttr(
        'import_policy', linkify=True, label=_('Import Policy')
    )
    export_policy = attrs.RelatedObjectAttr(
        'export_policy', linkify=True, label=_('Export Policy')
    )


class BGPGracefulRestartPanel(panels.ObjectAttributesPanel):
    graceful_restart = attrs.BooleanAttr(
        'graceful_restart', label=_('Graceful Restart')
    )
    graceful_restart_time = attrs.NumericAttr(
        'graceful_restart_time', label=_('Restart Time')
    )
    graceful_restart_stale_time = attrs.NumericAttr(
        'graceful_restart_stale_time', label=_('Stale Paths Time')
    )
    graceful_restart_helper_only = attrs.BooleanAttr(
        'graceful_restart_helper_only', label=_('Helper Only')
    )


class BGPPeerAddressFamilyOptionsPanel(panels.ObjectAttributesPanel):
    send_community = attrs.TextAttr('send_community_display', label=_('Send Community'))
    next_hop_self = attrs.BooleanAttr('next_hop_self', label=_('Next Hop Self'))
    remove_private_as = attrs.BooleanAttr(
        'remove_private_as', label=_('Remove Private AS')
    )
    allowas_in = attrs.NumericAttr('allowas_in', label=_('Allow AS In'))
    maximum_prefix = attrs.NumericAttr('maximum_prefix', label=_('Maximum Prefixes'))
    maximum_prefix_warning = attrs.NumericAttr(
        'maximum_prefix_warning', label=_('Warning at (%)')
    )
    maximum_prefix_action = attrs.ChoiceAttr('maximum_prefix_action', label=_('Action'))
    maximum_prefix_restart = attrs.NumericAttr(
        'maximum_prefix_restart', label=_('Restart after (minutes)')
    )


class BGPNoPolicyPanel(panels.TemplatePanel):
    """The address families of an eBGP session that has no import or export policy at
    any level (RFC 8212)"""

    def __init__(self, **kwargs):
        super().__init__('netbox_routing_protocols/panels/bgp_no_policy.html', **kwargs)

    def should_render(self, context):
        return bool(context.get('sessions_without_policy'))


class BGPPeerAddressFamilyPanel(panels.ObjectAttributesPanel):
    peer = attrs.RelatedObjectAttr('peer', linkify=True)
    peer_group = attrs.RelatedObjectAttr('peer_group', linkify=True)
    address_family = attrs.RelatedObjectAttr(
        'address_family', linkify=True, label=_('Address Family')
    )
    enabled = attrs.BooleanAttr('enabled', label=_('Enabled'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPEffectivePolicyPanel(panels.ObjectAttributesPanel):
    """The policy that applies: the most specific of the address family, the peer
    group, the peer and the instance"""

    import_policy = attrs.TextAttr(
        'effective_import_policy_display', label=_('Import Policy')
    )
    export_policy = attrs.TextAttr(
        'effective_export_policy_display', label=_('Export Policy')
    )


class BGPPolicyFilteringPanel(panels.ObjectAttributesPanel):
    prefixlist_out = attrs.RelatedObjectAttr('prefixlist_out', linkify=True)
    prefixlist_in = attrs.RelatedObjectAttr('prefixlist_in', linkify=True)
    export_policy = attrs.RelatedObjectAttr('export_policy', linkify=True)
    import_policy = attrs.RelatedObjectAttr('import_policy', linkify=True)


class BFDProfilePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    description = attrs.TextAttr('description', label=_('Description'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)


class BFDProfileSessionPanel(panels.ObjectAttributesPanel):
    min_rx_int = attrs.NumericAttr('min_rx_int', label=_('Min Receive (ms)'))
    min_tx_int = attrs.NumericAttr('min_tx_int', label=_('Min Transmit (ms)'))
    multiplier = attrs.NumericAttr('multiplier', label=_('Multiplier'))
    hold = attrs.NumericAttr('hold', label=_('Hold Time'))
