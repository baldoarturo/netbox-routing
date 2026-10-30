from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'BGPPolicyFilteringPanel',
    'BGPInstancePanel',
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
    graceful_restart = attrs.BooleanAttr(
        'graceful_restart', label=_('Graceful Restart')
    )
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
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


class BGPPeerGroupPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPPeerPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    instance = attrs.RelatedObjectAttr('instance', linkify=True)
    peer = attrs.RelatedObjectAttr('peer', linkify=True)
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
    ttl = attrs.NumericAttr('ttl', label=_('TTL'))
    password = attrs.TextAttr('password', label=_('Password'))
    keepalive = attrs.NumericAttr('keepalive', label=_('Keepalive Time'))
    hold_time = attrs.NumericAttr('hold_time', label=_('Hold Time'))


class BGPPeerAddressFamilyPanel(panels.ObjectAttributesPanel):
    peer = attrs.RelatedObjectAttr('peer', linkify=True)
    peer_group = attrs.RelatedObjectAttr('peer_group', linkify=True)
    address_family = attrs.RelatedObjectAttr(
        'address_family', linkify=True, label=_('Address Family')
    )
    enabled = attrs.BooleanAttr('enabled', label=_('Enabled'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))


class BGPPolicyFilteringPanel(panels.ObjectAttributesPanel):
    prefixlist_out = attrs.RelatedObjectAttr('prefixlist_out', linkify=True)
    prefixlist_in = attrs.RelatedObjectAttr('prefixlist_in', linkify=True)
    routepolicy_out = attrs.RelatedObjectAttr('routepolicy_out', linkify=True)
    routepolicy_in = attrs.RelatedObjectAttr('routepolicy_in', linkify=True)


class BFDProfilePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    description = attrs.TextAttr('description', label=_('Description'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True)


class BFDProfileSessionPanel(panels.ObjectAttributesPanel):
    min_rx_int = attrs.NumericAttr('min_rx_int', label=_('Min Receive'))
    min_tx_int = attrs.NumericAttr('min_tx_int', label=_('Min Transmit'))
    multiplier = attrs.NumericAttr('multiplier', label=_('Multiplier'))
    hold = attrs.NumericAttr('hold', label=_('Hold Time'))
