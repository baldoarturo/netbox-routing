from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.models import ASN, IPAddress, VRF
from netbox.forms import PrimaryModelBulkEditForm
from netbox_routing_protocols.forms.bulk_edit.base import TenantBulkEditMixin
from netbox_routing_protocols.models import RoutePolicy, PrefixList
from utilities.forms import add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import BulkEditNullBooleanSelect

from netbox_routing_protocols.choices.bgp import *
from netbox_routing_protocols.choices.ospf import OSPFRouteTypeChoices
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceBulkEditForm',
    'BGPAddressFamilyBulkEditForm',
    'BGPPeerGroupBulkEditForm',
    'BGPListenRangeBulkEditForm',
    'BGPRedistributionBulkEditForm',
    'BGPPeerBulkEditForm',
    'BGPPeerAddressFamilyBulkEditForm',
    'BFDProfileBulkEditForm',
)


def _tristate(label):
    return forms.NullBooleanField(
        label=label, required=False, widget=BulkEditNullBooleanSelect()
    )


class BGPPeerConfigBulkEditMixin(forms.Form):
    remote_as = DynamicModelChoiceField(
        label=_('Remote AS'), queryset=ASN.objects.all(), required=False, selector=True
    )
    local_as = DynamicModelChoiceField(
        label=_('Local AS'), queryset=ASN.objects.all(), required=False, selector=True
    )
    enabled = _tristate(_('Enabled'))
    bfd = DynamicModelChoiceField(
        label=_('BFD Profile'),
        queryset=BFDProfile.objects.all(),
        required=False,
        selector=True,
    )
    ebgp_multihop = forms.IntegerField(
        label=_('eBGP Multihop'), required=False, min_value=1, max_value=255
    )
    ttl_security_hops = forms.IntegerField(
        label=_('TTL Security Hops'), required=False, min_value=1, max_value=254
    )
    passive = _tristate(_('Passive'))
    route_reflector_client = _tristate(_('Route Reflector Client'))
    extended_nexthop = _tristate(_('Extended Next Hop'))
    show_md5 = _tristate(_('MD5 Digest'))
    import_policy = DynamicModelChoiceField(
        label=_('Import Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    export_policy = DynamicModelChoiceField(
        label=_('Export Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    keepalive = forms.IntegerField(
        label=_('Keepalive Time'), required=False, min_value=0, max_value=21845
    )
    hold_time = forms.IntegerField(
        label=_('Hold Time'), required=False, min_value=0, max_value=65535
    )


_CONFIG_NULLABLE = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ebgp_multihop',
    'ttl_security_hops',
    'passive',
    'route_reflector_client',
    'extended_nexthop',
    'import_policy',
    'export_policy',
    'keepalive',
    'hold_time',
    'description',
    'tenant',
)


class BGPInstanceBulkEditForm(TenantBulkEditMixin, PrimaryModelBulkEditForm):
    model = BGPInstance
    vrf = DynamicModelChoiceField(
        label=_('VRF'), queryset=VRF.objects.all(), required=False, selector=True
    )
    asn = DynamicModelChoiceField(
        label=_('ASN'), queryset=ASN.objects.all(), required=False, selector=True
    )
    asdot = _tristate(_('AS Dot Notation'))
    cluster_id = forms.CharField(label=_('Cluster ID'), required=False, max_length=15)
    graceful_restart = _tristate(_('Graceful Restart'))
    import_policy = DynamicModelChoiceField(
        label=_('Import Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    export_policy = DynamicModelChoiceField(
        label=_('Export Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet(
            'vrf', 'asn', 'asdot', 'cluster_id', 'graceful_restart', name=_('BGP')
        ),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = (
        'vrf',
        'asdot',
        'cluster_id',
        'graceful_restart',
        'import_policy',
        'export_policy',
        'description',
        'tenant',
    )


class BGPAddressFamilyBulkEditForm(TenantBulkEditMixin, PrimaryModelBulkEditForm):
    model = BGPAddressFamily
    maximum_paths = forms.IntegerField(
        label=_('Maximum Paths'), required=False, min_value=1
    )
    default_metric = forms.IntegerField(
        label=_('Default Metric'), required=False, min_value=0, max_value=4294967295
    )
    default_originate = _tristate(_('Default Originate'))
    auto_summary = _tristate(_('Auto Summary'))
    distance_ebgp = forms.IntegerField(
        label=_('eBGP Distance'), required=False, min_value=1, max_value=255
    )
    distance_ibgp = forms.IntegerField(
        label=_('iBGP Distance'), required=False, min_value=1, max_value=255
    )
    additional_paths_send = _tristate(_('Additional Paths (send)'))
    additional_paths_receive = _tristate(_('Additional Paths (receive)'))
    additional_paths_install = _tristate(_('Additional Paths (install)'))
    long_lived_stale_time = forms.IntegerField(
        label=_('Long-Lived Graceful Restart Stale Time'),
        required=False,
        min_value=0,
        max_value=16777215,
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet(
            'maximum_paths',
            'default_metric',
            'default_originate',
            'auto_summary',
            'distance_ebgp',
            'distance_ibgp',
            name=_('Options'),
        ),
        FieldSet(
            'additional_paths_send',
            'additional_paths_receive',
            'additional_paths_install',
            'long_lived_stale_time',
            name=_('Additional paths'),
        ),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = (
        'maximum_paths',
        'default_metric',
        'default_originate',
        'auto_summary',
        'distance_ebgp',
        'distance_ibgp',
        'additional_paths_send',
        'additional_paths_receive',
        'additional_paths_install',
        'long_lived_stale_time',
        'description',
        'tenant',
    )


class BGPPeerGroupBulkEditForm(
    BGPPeerConfigBulkEditMixin, TenantBulkEditMixin, PrimaryModelBulkEditForm
):
    model = BGPPeerGroup
    listen_limit = forms.IntegerField(
        label=_('Listen Limit'), required=False, min_value=1
    )
    fieldsets = (
        FieldSet('description'),
        FieldSet(
            'remote_as',
            'local_as',
            'enabled',
            'bfd',
            'ebgp_multihop',
            'ttl_security_hops',
            'passive',
            'route_reflector_client',
            'extended_nexthop',
            'keepalive',
            'hold_time',
            'show_md5',
            name=_('Session'),
        ),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('listen_limit', name=_('Dynamic neighbors')),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = _CONFIG_NULLABLE + ('listen_limit',)


class BGPRedistributionBulkEditForm(TenantBulkEditMixin, PrimaryModelBulkEditForm):
    model = BGPRedistribution
    metric = forms.IntegerField(
        label=_('Metric'), required=False, min_value=0, max_value=4294967295
    )
    route_policy = DynamicModelChoiceField(
        label=_('Route Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    ospf_match = forms.MultipleChoiceField(
        label=_('OSPF Route Types'), choices=OSPFRouteTypeChoices, required=False
    )
    fieldsets = (
        FieldSet('description'),
        FieldSet('metric', 'route_policy', 'ospf_match', name=_('Redistribution')),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = ('metric', 'route_policy', 'ospf_match', 'description', 'tenant')


class BGPListenRangeBulkEditForm(PrimaryModelBulkEditForm):
    model = BGPListenRange
    fieldsets = (FieldSet('description'),)
    nullable_fields = ('description',)


class BGPPeerBulkEditForm(
    BGPPeerConfigBulkEditMixin, TenantBulkEditMixin, PrimaryModelBulkEditForm
):
    model = BGPPeer
    peer_group = DynamicModelChoiceField(
        label=_('Peer Group'),
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
    )
    source = DynamicModelChoiceField(
        label=_('Source'),
        queryset=IPAddress.objects.all(),
        required=False,
        selector=True,
    )
    status = forms.ChoiceField(
        label=_('Status'), choices=add_blank_choice(BGPStatusChoices), required=False
    )
    fieldsets = (
        FieldSet('description'),
        FieldSet('peer_group', 'source', 'status', name=_('Peer')),
        FieldSet(
            'remote_as',
            'local_as',
            'enabled',
            'bfd',
            'ebgp_multihop',
            'ttl_security_hops',
            'passive',
            'route_reflector_client',
            'extended_nexthop',
            'keepalive',
            'hold_time',
            'show_md5',
            name=_('Session'),
        ),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = _CONFIG_NULLABLE + ('peer_group', 'source', 'status')


class BGPPeerAddressFamilyBulkEditForm(TenantBulkEditMixin, PrimaryModelBulkEditForm):
    model = BGPPeerAddressFamily
    enabled = _tristate(_('Enabled'))
    prefixlist_in = DynamicModelChoiceField(
        label=_('Prefix List (in)'),
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
    )
    prefixlist_out = DynamicModelChoiceField(
        label=_('Prefix List (out)'),
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
    )
    import_policy = DynamicModelChoiceField(
        label=_('Import Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    export_policy = DynamicModelChoiceField(
        label=_('Export Policy'),
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
    )
    send_community = forms.MultipleChoiceField(
        label=_('Send Community'),
        choices=BGPCommunityTypeChoices,
        required=False,
    )
    next_hop_self = _tristate(_('Next Hop Self'))
    remove_private_as = _tristate(_('Remove Private AS'))
    allowas_in = forms.IntegerField(
        label=_('Allow AS In'), required=False, min_value=1, max_value=10
    )
    maximum_prefix = forms.IntegerField(
        label=_('Maximum Prefixes'), required=False, min_value=1
    )
    fieldsets = (
        FieldSet('description', 'enabled'),
        FieldSet(
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            'maximum_prefix',
            name=_('Options'),
        ),
        FieldSet(
            'prefixlist_in',
            'prefixlist_out',
            'import_policy',
            'export_policy',
            name=_('Filtering'),
        ),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = (
        'enabled',
        'next_hop_self',
        'remove_private_as',
        'allowas_in',
        'maximum_prefix',
        'prefixlist_in',
        'prefixlist_out',
        'import_policy',
        'export_policy',
        'description',
        'tenant',
    )


class BFDProfileBulkEditForm(TenantBulkEditMixin, PrimaryModelBulkEditForm):
    model = BFDProfile
    fieldsets = (
        FieldSet(
            'description',
        ),
        FieldSet(
            'min_tx_int',
            'min_rx_int',
            'multiplier',
            'hold',
        ),
        FieldSet('tenant', name=_('Tenancy')),
    )
    nullable_fields = (
        'hold',
        'description',
        'tenant',
    )
