from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import ASN, VRF
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.models import PrefixList, RoutePolicy
from tenancy.forms import TenancyFilterForm
from utilities.forms.fields import TagFilterField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.choices.bgp import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceFilterForm',
    'BGPAddressFamilyFilterForm',
    'BGPPeerGroupFilterForm',
    'BGPPeerFilterForm',
    'BGPPeerAddressFamilyFilterForm',
    'BFDProfileFilterForm',
)


class BGPPolicyFilterFormMixin(forms.Form):
    prefixlist_in_id = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
        label=_('Incoming Prefix List'),
    )
    prefixlist_out_id = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
        label=_('Outgoing Prefix List'),
    )
    routepolicy_in_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Incoming Route Policy'),
    )
    routepolicy_out_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Outgoing Route Policy'),
    )


class BGPPeerConfigFilterFormMixin(forms.Form):
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    remote_as_id = DynamicModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        selector=True,
        label=_('Remote AS'),
    )
    local_as_id = DynamicModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        selector=True,
        label=_('Local AS'),
    )
    bfd_id = DynamicModelMultipleChoiceField(
        queryset=BFDProfile.objects.all(),
        required=False,
        selector=True,
        label=_('BFD Profile'),
    )
    enabled = forms.NullBooleanField(
        required=False,
        label=_('Enabled'),
        widget=forms.Select(
            choices=((None, '---------'), (True, _('Yes')), (False, _('No')))
        ),
    )


class BGPInstanceFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = BGPInstance
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('device_id', 'vrf_id', 'asn_id', name=_('BGP')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    vrf_id = DynamicModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
    )
    asn_id = DynamicModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        selector=True,
        label=_('ASN'),
    )
    tag = TagFilterField(model)


class BGPAddressFamilyFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = BGPAddressFamily
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'device_id', 'vrf_id', 'address_family', name=_('BGP')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    vrf_id = DynamicModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
    )
    address_family = forms.MultipleChoiceField(
        choices=BGPAddressFamilyChoices, required=False, label=_('Address Family')
    )
    tag = TagFilterField(model)


class BGPPeerGroupFilterForm(
    BGPPeerConfigFilterFormMixin, TenancyFilterForm, NetBoxModelFilterSetForm
):
    model = BGPPeerGroup
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'device_id', name=_('BGP')),
        FieldSet('enabled', 'remote_as_id', 'local_as_id', 'bfd_id', name=_('Session')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    tag = TagFilterField(model)


class BGPPeerFilterForm(
    BGPPeerConfigFilterFormMixin, TenancyFilterForm, NetBoxModelFilterSetForm
):
    model = BGPPeer
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'device_id', 'peer_group_id', 'status', name=_('BGP')),
        FieldSet('enabled', 'remote_as_id', 'local_as_id', 'bfd_id', name=_('Session')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    peer_group_id = DynamicModelMultipleChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Group'),
    )
    status = forms.MultipleChoiceField(
        choices=BGPStatusChoices, required=False, label=_('Status')
    )
    tag = TagFilterField(model)


class BGPPeerAddressFamilyFilterForm(
    BGPPolicyFilterFormMixin, TenancyFilterForm, NetBoxModelFilterSetForm
):
    model = BGPPeerAddressFamily
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'instance_id',
            'peer_id',
            'peer_group_id',
            'address_family_id',
            'enabled',
            name=_('BGP'),
        ),
        FieldSet(
            'prefixlist_in_id',
            'prefixlist_out_id',
            'routepolicy_in_id',
            'routepolicy_out_id',
            name=_('Filtering'),
        ),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    peer_id = DynamicModelMultipleChoiceField(
        queryset=BGPPeer.objects.all(),
        required=False,
        selector=True,
        label=_('Peer'),
    )
    peer_group_id = DynamicModelMultipleChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Group'),
    )
    address_family_id = DynamicModelMultipleChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('Address Family'),
    )
    enabled = forms.NullBooleanField(
        required=False,
        label=_('Enabled'),
        widget=forms.Select(
            choices=((None, '---------'), (True, _('Yes')), (False, _('No')))
        ),
    )
    tag = TagFilterField(model)


class BFDProfileFilterForm(
    TenancyFilterForm,
    # ContactModelFilterForm,
    NetBoxModelFilterSetForm,
):
    model = BFDProfile
    fieldsets = (
        FieldSet(
            'q',
            'filter_id',
            'tag',
        ),
    )
    tag = TagFilterField(model)
