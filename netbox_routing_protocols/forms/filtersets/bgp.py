from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import ASN, VRF, Prefix
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.models import (
    EIGRPAddressFamily,
    ISISInstance,
    OSPFInstance,
    PrefixList,
    RoutePolicy,
)
from tenancy.forms import TenancyFilterForm
from utilities.forms.fields import TagFilterField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.choices.bgp import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPOriginatedNetworkFilterForm',
    'BGPAggregateFilterForm',
    'BGPRedistributionFilterForm',
    'BGPInstanceFilterForm',
    'BGPAddressFamilyFilterForm',
    'BGPPeerGroupFilterForm',
    'BGPListenRangeFilterForm',
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
    import_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
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
    import_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
    )


class BGPInstanceFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = BGPInstance
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('device_id', 'vrf_id', 'asn_id', name=_('BGP')),
        FieldSet('import_policy_id', 'export_policy_id', name=_('Route Policy')),
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
    import_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
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
        FieldSet('import_policy_id', 'export_policy_id', name=_('Route Policy')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    tag = TagFilterField(model)


class BGPListenRangeFilterForm(NetBoxModelFilterSetForm):
    model = BGPListenRange
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'peer_group_id', 'prefix_id', name=_('BGP')),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    peer_group_id = DynamicModelMultipleChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Group'),
    )
    prefix_id = DynamicModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        selector=True,
        label=_('Prefix'),
    )
    tag = TagFilterField(model)


class BGPRedistributionFilterForm(NetBoxModelFilterSetForm):
    model = BGPRedistribution
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'instance_id',
            'address_family_id',
            'protocol',
            'ospf_source_id',
            'isis_source_id',
            'eigrp_source_id',
            name=_('Redistribution'),
        ),
        FieldSet('device_id', name=_('Device')),
        FieldSet('route_policy_id', name=_('Filtering')),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, selector=True, label=_('Device')
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    address_family_id = DynamicModelMultipleChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('Address Family'),
    )
    ospf_source_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Source'),
    )
    isis_source_id = DynamicModelMultipleChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Source'),
    )
    eigrp_source_id = DynamicModelMultipleChoiceField(
        queryset=EIGRPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('EIGRP Source'),
    )
    route_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Route Policy'),
    )
    protocol = forms.MultipleChoiceField(
        choices=BGPRedistributionProtocolChoices,
        required=False,
        label=_('Protocol'),
    )
    tag = TagFilterField(model)


class _PrefixFilterFormMixin(forms.Form):
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(), required=False, selector=True, label=_('Device')
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    address_family_id = DynamicModelMultipleChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('Address Family'),
    )
    prefix_id = DynamicModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        selector=True,
        label=_('Prefix'),
    )


class BGPOriginatedNetworkFilterForm(_PrefixFilterFormMixin, NetBoxModelFilterSetForm):
    model = BGPOriginatedNetwork
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'device_id', 'instance_id', 'address_family_id', 'prefix_id', name=_('BGP')
        ),
    )
    tag = TagFilterField(model)


class BGPAggregateFilterForm(_PrefixFilterFormMixin, NetBoxModelFilterSetForm):
    model = BGPAggregate
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'device_id', 'instance_id', 'address_family_id', 'prefix_id', name=_('BGP')
        ),
        FieldSet('summary_only', 'as_set', name=_('Aggregate')),
    )
    summary_only = forms.NullBooleanField(
        required=False,
        label=_('Summary Only'),
        widget=forms.Select(
            choices=((None, '---------'), (True, _('Yes')), (False, _('No')))
        ),
    )
    as_set = forms.NullBooleanField(
        required=False,
        label=_('AS Set'),
        widget=forms.Select(
            choices=((None, '---------'), (True, _('Yes')), (False, _('No')))
        ),
    )
    tag = TagFilterField(model)


class BGPPeerFilterForm(
    BGPPeerConfigFilterFormMixin, TenancyFilterForm, NetBoxModelFilterSetForm
):
    model = BGPPeer
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'instance_id',
            'device_id',
            'peer_group_id',
            'interface_id',
            'status',
            name=_('BGP'),
        ),
        FieldSet('enabled', 'remote_as_id', 'local_as_id', 'bfd_id', name=_('Session')),
        FieldSet('import_policy_id', 'export_policy_id', name=_('Route Policy')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    peer_group_id = DynamicModelMultipleChoiceField(
        queryset=BGPPeerGroup.objects.all(),
        required=False,
        selector=True,
        label=_('Peer Group'),
    )
    interface_id = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        label=_('Interface'),
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
            'import_policy_id',
            'export_policy_id',
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
        FieldSet(
            'min_tx_int',
            'min_rx_int',
            'multiplier',
            'hold',
            name=_('BFD Parameters'),
        ),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    min_tx_int = forms.IntegerField(required=False, label=_('Min TX Interval (ms)'))
    min_rx_int = forms.IntegerField(required=False, label=_('Min RX Interval (ms)'))
    multiplier = forms.IntegerField(required=False, label=_('Multiplier'))
    hold = forms.IntegerField(required=False, label=_('Hold Time'))
    tag = TagFilterField(model)
