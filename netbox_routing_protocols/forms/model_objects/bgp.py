from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import ASN, VRF, IPAddress
from netbox.forms import PrimaryModelForm
from tenancy.forms import TenancyForm
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet, TabbedGroups

from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceForm',
    'BGPAddressFamilyForm',
    'BGPPeerGroupForm',
    'BGPPeerForm',
    'BGPPeerAddressFamilyForm',
    'BFDProfileForm',
)

_CONFIG_FIELDS = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ttl',
    'keepalive',
    'hold_time',
    'password',
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

    fieldsets = (
        FieldSet('name', 'device', 'vrf', 'asn', 'description', name=_('Instance')),
        FieldSet('router_id', 'asdot', 'graceful_restart', name=_('Options')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPInstance
        fields = (
            'name',
            'device',
            'vrf',
            'asn',
            'router_id',
            'asdot',
            'graceful_restart',
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


class BGPPeerGroupForm(BGPPeerConfigFormMixin, TenancyForm, PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=BGPInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('instance', 'name', 'description', name=_('Peer group')),
        FieldSet(*_CONFIG_FIELDS, name=_('Session')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPPeerGroup
        fields = (
            'instance',
            'name',
            *_CONFIG_FIELDS,
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
        required=True,
        selector=True,
        label=_('Peer Address'),
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
            'source',
            'peer_group',
            'status',
            'description',
            name=_('Peer'),
        ),
        FieldSet(*_CONFIG_FIELDS, name=_('Session')),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = BGPPeer
        fields = (
            'instance',
            'name',
            'peer',
            'source',
            'peer_group',
            'status',
            *_CONFIG_FIELDS,
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
    routepolicy_in = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Inbound Route Policy'),
    )
    routepolicy_out = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Outbound Route Policy'),
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
            'routepolicy_in',
            'routepolicy_out',
            name=_('Filtering'),
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
            'routepolicy_in',
            'routepolicy_out',
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
