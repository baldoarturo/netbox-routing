from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import ASN, VRF, IPAddress, Prefix
from netbox.forms import PrimaryModelForm
from tenancy.forms import TenancyForm
from dcim.models import Interface
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import FieldSet, TabbedGroups

from netbox_routing_protocols.choices.bgp import BGPCommunityTypeChoices
from netbox_routing_protocols.choices.ospf import OSPFRouteTypeChoices
from netbox_routing_protocols.models import (
    EIGRPAddressFamily,
    ISISInstance,
    OSPFInstance,
)
from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceForm',
    'BGPAddressFamilyForm',
    'BGPPeerGroupForm',
    'BGPListenRangeForm',
    'BGPRedistributionForm',
    'BGPPeerForm',
    'BGPPeerAddressFamilyForm',
    'BFDProfileForm',
)

_CONFIG_FIELDS = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ebgp_multihop',
    'ttl_security_hops',
    'passive',
    'as_override',
    'soft_reconfiguration_inbound',
    'graceful_shutdown',
    'route_reflector_client',
    'extended_nexthop',
    'keepalive',
    'hold_time',
    'passphrase',
    'show_md5',
)
_COMMON_FIELDS = ('description', 'comments', 'tags', 'owner')


class BGPInstanceForm(TenancyForm, PrimaryModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(), required=True, selector=True, label=_('Device')
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
        help_text=_('Leave empty for the global routing table'),
    )
    asn = DynamicModelChoiceField(
        queryset=ASN.objects.all(), required=True, selector=True, label=_('ASN')
    )
    confederation_identifier = DynamicModelChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        selector=True,
        label=_('Confederation Identifier'),
    )
    confederation_peers = DynamicModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        selector=True,
        label=_('Confederation Peers'),
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

    fieldsets = (
        FieldSet('name', 'device', 'vrf', 'asn', 'description', name=_('Instance')),
        FieldSet('router_id', 'asdot', name=_('Options')),
        FieldSet(
            'cluster_id',
            'confederation_identifier',
            'confederation_peers',
            name=_('Route reflector and confederation'),
        ),
        FieldSet(
            'graceful_restart',
            'graceful_restart_time',
            'graceful_restart_stale_time',
            'graceful_restart_helper_only',
            name=_('Graceful restart'),
        ),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    def clean(self):
        super().clean()
        errors = BGPInstance.confederation_errors(
            self.cleaned_data.get('asn'),
            self.cleaned_data.get('confederation_identifier'),
            self.cleaned_data.get('confederation_peers'),
        )
        if errors:
            raise forms.ValidationError(errors)

    class Meta:
        model = BGPInstance
        fields = (
            'name',
            'device',
            'vrf',
            'asn',
            'router_id',
            'asdot',
            'cluster_id',
            'confederation_identifier',
            'confederation_peers',
            'graceful_restart',
            'graceful_restart_time',
            'graceful_restart_stale_time',
            'graceful_restart_helper_only',
            'import_policy',
            'export_policy',
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BGPAddressFamilyForm(TenancyForm, PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=BGPInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('instance', 'address_family', 'description', name=_('Address family')),
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
            name=_('Additional paths'),
        ),
        FieldSet('long_lived_stale_time', name=_('Graceful restart')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPAddressFamily
        fields = (
            'instance',
            'address_family',
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
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BGPPeerConfigFormMixin(forms.Form):
    remote_as = DynamicModelChoiceField(
        queryset=ASN.objects.all(), required=False, selector=True, label=_('Remote AS')
    )
    local_as = DynamicModelChoiceField(
        queryset=ASN.objects.all(), required=False, selector=True, label=_('Local AS')
    )
    bfd = DynamicModelChoiceField(
        queryset=BFDProfile.objects.all(),
        required=False,
        selector=True,
        label=_('BFD Profile'),
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


class BGPPeerGroupForm(BGPPeerConfigFormMixin, TenancyForm, PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=BGPInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('instance', 'name', 'description', name=_('Peer group')),
        FieldSet('listen_limit', name=_('Dynamic neighbors')),
        FieldSet(*_CONFIG_FIELDS, name=_('Session')),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPPeerGroup
        fields = (
            'instance',
            'name',
            'listen_limit',
            *_CONFIG_FIELDS,
            'import_policy',
            'export_policy',
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BGPListenRangeForm(PrimaryModelForm):
    peer_group = DynamicModelChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=True,
        selector=True,
        label=_('Peer Group'),
    )
    prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=True,
        selector=True,
        label=_('Prefix'),
        help_text=_('The addresses the peer group accepts neighbors from'),
    )

    fieldsets = (
        FieldSet('peer_group', 'prefix', 'description', name=_('Listen range')),
    )

    class Meta:
        model = BGPListenRange
        fields = ('peer_group', 'prefix', *_COMMON_FIELDS)


class BGPRedistributionForm(TenancyForm, PrimaryModelForm):
    address_family = DynamicModelChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=True,
        selector=True,
        label=_('Address Family'),
    )
    ospf_source = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Source'),
        help_text=_('An OSPF instance on the device of the BGP instance'),
    )
    isis_source = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Source'),
    )
    eigrp_source = DynamicModelChoiceField(
        queryset=EIGRPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('EIGRP Source'),
        help_text=_('An EIGRP address family: its VRF and IP version'),
    )
    ospf_match = forms.MultipleChoiceField(
        choices=OSPFRouteTypeChoices,
        required=False,
        label=_('OSPF Route Types'),
        help_text=_('Empty takes all of them'),
    )
    route_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Route Policy'),
    )

    fieldsets = (
        FieldSet(
            'address_family',
            'protocol',
            'metric',
            'route_policy',
            'description',
            name=_('Redistribution'),
        ),
        FieldSet(
            'ospf_source',
            'ospf_match',
            'isis_source',
            'eigrp_source',
            name=_('Source'),
        ),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPRedistribution
        fields = (
            'address_family',
            'protocol',
            'ospf_source',
            'isis_source',
            'eigrp_source',
            'metric',
            'route_policy',
            'ospf_match',
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BGPPeerForm(BGPPeerConfigFormMixin, TenancyForm, PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=BGPInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )
    peer = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Address'),
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        label=_('Interface'),
        help_text=_('Unnumbered peer (RFC 5549): instead of the address'),
    )
    source = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        selector=True,
        label=_('Source Address'),
    )
    peer_group = DynamicModelChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        query_params={'instance_id': '$instance'},
        label=_('Peer Group'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'name',
            'peer',
            'interface',
            'source',
            'peer_group',
            'status',
            'description',
            name=_('Peer'),
        ),
        FieldSet(*_CONFIG_FIELDS, name=_('Session')),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPPeer
        fields = (
            'instance',
            'name',
            'peer',
            'interface',
            'source',
            'peer_group',
            'status',
            *_CONFIG_FIELDS,
            'import_policy',
            'export_policy',
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BGPPeerAddressFamilyForm(TenancyForm, PrimaryModelForm):
    peer = DynamicModelChoiceField(
        queryset=BGPPeer.objects.all(),
        required=False,
        selector=True,
        label=_('Peer'),
    )
    peer_group = DynamicModelChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Group'),
    )
    address_family = DynamicModelChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=True,
        selector=True,
        label=_('Address Family'),
    )
    prefixlist_in = DynamicModelChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
        label=_('Inbound Prefix List'),
    )
    prefixlist_out = DynamicModelChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
        label=_('Outbound Prefix List'),
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

    send_community = forms.MultipleChoiceField(
        choices=BGPCommunityTypeChoices,
        required=False,
        label=_('Send Community'),
        help_text=_('Empty uses the one of the peer group, else the platform default'),
    )

    fieldsets = (
        FieldSet(
            TabbedGroups(
                FieldSet('peer', name=_('Peer')),
                FieldSet('peer_group', name=_('Peer Group')),
            ),
            'address_family',
            'enabled',
            'description',
            name=_('Peer address family'),
        ),
        FieldSet(
            'prefixlist_in',
            'prefixlist_out',
            'import_policy',
            'export_policy',
            name=_('Filtering'),
        ),
        FieldSet(
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            name=_('Advertisement'),
        ),
        FieldSet(
            'maximum_prefix',
            'maximum_prefix_warning',
            'maximum_prefix_action',
            'maximum_prefix_restart',
            name=_('Maximum prefixes'),
        ),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPPeerAddressFamily
        fields = (
            'peer',
            'peer_group',
            'address_family',
            'enabled',
            'prefixlist_in',
            'prefixlist_out',
            'import_policy',
            'export_policy',
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            'maximum_prefix',
            'maximum_prefix_warning',
            'maximum_prefix_action',
            'maximum_prefix_restart',
            'tenant_group',
            'tenant',
            *_COMMON_FIELDS,
        )


class BFDProfileForm(TenancyForm, PrimaryModelForm):
    fieldsets = (
        FieldSet(
            'name',
            'description',
        ),
        FieldSet(
            'min_rx_int',
            'min_tx_int',
            'multiplier',
            'hold',
            name=_('BFD Parameters'),
        ),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BFDProfile
        fields = [
            'name',
            'min_tx_int',
            'min_rx_int',
            'multiplier',
            'hold',
            'description',
            'comments',
            'tenant_group',
            'tenant',
            'tags',
            'owner',
        ]
