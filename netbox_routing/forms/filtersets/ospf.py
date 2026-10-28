from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Interface, Device
from ipam.models import VRF, IPAddress
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing.choices import AuthenticationChoices
from netbox_routing.choices.ospf import (
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFGracefulRestartChoices,
    OSPFNetworkTypeChoices,
    OSPFRedistributionProtocolChoices,
)
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import TagFilterField, DynamicModelMultipleChoiceField

from netbox_routing.models import (
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
)

__all__ = (
    'OSPFAreaFilterForm',
    'OSPFInstanceFilterForm',
    'OSPFInterfaceFilterForm',
    'OSPFNetworkFilterForm',
    'OSPFRedistributionFilterForm',
)

from utilities.forms.rendering import FieldSet


class OSPFInstanceFilterForm(NetBoxModelFilterSetForm):
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
    router_id = forms.CharField(
        required=False,
        label=_('Router ID'),
    )
    process_id = forms.CharField(
        required=False,
        label=_('Process ID'),
    )
    default_originate = forms.NullBooleanField(
        required=False,
        label=_('Default Originate'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    default_originate_always = forms.NullBooleanField(
        required=False,
        label=_('Default Originate Always'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    default_originate_metric = forms.IntegerField(
        required=False, label=_('Default Originate Metric')
    )
    default_originate_metric_type = forms.MultipleChoiceField(
        choices=OSPFExternalMetricTypeChoices,
        required=False,
        label=_('Default Originate Metric Type'),
    )
    graceful_restart = forms.MultipleChoiceField(
        choices=OSPFGracefulRestartChoices,
        required=False,
        label=_('Graceful Restart'),
    )
    max_metric_router_lsa = forms.NullBooleanField(
        required=False,
        label=_('Max Metric (Stub Router)'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    rfc1583_compatibility = forms.NullBooleanField(
        required=False,
        label=_('RFC 1583 Compatibility'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    log_adjacency_changes = forms.NullBooleanField(
        required=False,
        label=_('Log Adjacency Changes'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    bfd_all_interfaces = forms.NullBooleanField(
        required=False,
        label=_('BFD on All Interfaces'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    passive_interface_default = forms.NullBooleanField(
        required=False,
        label=_('Passive Interfaces by Default'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )

    model = OSPFInstance
    fieldsets = (
        FieldSet(
            'q',
            'filter_id',
            'tag',
        ),
        FieldSet('device_id', 'vrf_id', 'router_id', 'process_id', name=_('Device')),
        FieldSet(
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            name=_('Default Information'),
        ),
        FieldSet(
            'graceful_restart',
            'max_metric_router_lsa',
            'rfc1583_compatibility',
            'log_adjacency_changes',
            'bfd_all_interfaces',
            'passive_interface_default',
            name=_('Advanced'),
        ),
    )
    tag = TagFilterField(model)


class OSPFAreaFilterForm(NetBoxModelFilterSetForm):
    model = OSPFArea
    fieldsets = (
        FieldSet('q', 'device_id', 'instance_id', 'filter_id', 'area_type', 'tag'),
        FieldSet(
            'default_cost',
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            name=_('Stub / NSSA'),
        ),
    )

    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        query_params={'device_id': '$device_id'},
        label=_('Instance'),
    )
    area_type = forms.ChoiceField(
        choices=add_blank_choice(OSPFAreaTypeChoices), label='Area Type', required=False
    )
    default_cost = forms.IntegerField(required=False, label=_('Default Cost'))
    nssa_translate_always = forms.NullBooleanField(
        required=False,
        label=_('Translate Type 7 Always'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    nssa_no_redistribution = forms.NullBooleanField(
        required=False,
        label=_('No Redistribution'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    nssa_default_originate = forms.NullBooleanField(
        required=False,
        label=_('Default Information Originate'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tag = TagFilterField(model)


class OSPFInterfaceFilterForm(NetBoxModelFilterSetForm):
    model = OSPFInterface
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'area_id', name=_('OSPF')),
        FieldSet('device_id', 'interface_id', 'vrf_id', name=_('Device')),
        FieldSet(
            'network_type',
            'priority',
            'cost',
            'bfd',
            'mtu_ignore',
            'authentication',
            name=_('Attributes'),
        ),
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            name=_('Timers'),
        ),
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
    instance_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    area_id = DynamicModelMultipleChoiceField(
        queryset=OSPFArea.objects.all(),
        required=False,
        selector=True,
        label=_('Area'),
    )
    interface_id = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        label=_('Interface'),
    )
    passive = forms.NullBooleanField(
        required=False,
        label='Passive Interface',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    bfd = forms.NullBooleanField(
        required=False,
        label='BFD Enabled',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    network_type = forms.MultipleChoiceField(
        choices=OSPFNetworkTypeChoices,
        required=False,
        label=_('Network Type'),
    )
    mtu_ignore = forms.NullBooleanField(
        required=False,
        label=_('MTU Ignore'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    priority = forms.IntegerField(required=False)
    cost = forms.IntegerField(required=False, label=_('Cost'))
    hello_interval = forms.IntegerField(required=False, label=_('Hello Interval'))
    dead_interval = forms.IntegerField(required=False, label=_('Dead Interval'))
    retransmit_interval = forms.IntegerField(
        required=False, label=_('Retransmit Interval')
    )
    transmit_delay = forms.IntegerField(required=False, label=_('Transmit Delay'))
    authentication = forms.ChoiceField(
        choices=add_blank_choice(AuthenticationChoices), required=False
    )
    tag = TagFilterField(model)


class OSPFNetworkFilterForm(NetBoxModelFilterSetForm):
    model = OSPFNetwork
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('instance_id', 'area_id', 'ospf_interface_id', name=_('OSPF')),
        FieldSet('device_id', 'interface_id', 'ip_address_id', name=_('Device')),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    area_id = DynamicModelMultipleChoiceField(
        queryset=OSPFArea.objects.all(),
        required=False,
        selector=True,
        label=_('Area'),
    )
    ospf_interface_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInterface.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Interface'),
    )
    interface_id = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        label=_('Interface'),
    )
    ip_address_id = DynamicModelMultipleChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        selector=True,
        label=_('IP Address'),
    )
    tag = TagFilterField(model)


class OSPFRedistributionFilterForm(NetBoxModelFilterSetForm):
    model = OSPFRedistribution
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('device_id', 'instance_id', name=_('OSPF')),
        FieldSet(
            'protocol',
            'metric_type',
            'subnets',
            'route_tag',
            name=_('Redistribution'),
        ),
    )
    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance_id = DynamicModelMultipleChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    protocol = forms.MultipleChoiceField(
        choices=OSPFRedistributionProtocolChoices,
        required=False,
        label=_('Protocol'),
    )
    metric_type = forms.MultipleChoiceField(
        choices=OSPFExternalMetricTypeChoices,
        required=False,
        label=_('Metric Type'),
    )
    subnets = forms.NullBooleanField(
        required=False,
        label=_('Subnets'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    route_tag = forms.IntegerField(required=False, label=_('Route Tag'))
    tag = TagFilterField(model)
