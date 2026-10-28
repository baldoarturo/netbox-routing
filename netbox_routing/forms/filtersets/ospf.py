from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Interface, Device
from ipam.models import VRF
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing.choices import AuthenticationChoices
from netbox_routing.choices.ospf import OSPFAreaTypeChoices, OSPFNetworkTypeChoices
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import TagFilterField, DynamicModelMultipleChoiceField

from netbox_routing.models import OSPFInstance, OSPFArea, OSPFInterface

__all__ = (
    'OSPFAreaFilterForm',
    'OSPFInstanceFilterForm',
    'OSPFInterfaceFilterForm',
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

    model = OSPFInstance
    fieldsets = (
        FieldSet(
            'q',
            'filter_id',
            'tag',
        ),
        FieldSet('device_id', 'vrf_id', 'router_id', 'process_id', name=_('Device')),
    )
    tag = TagFilterField(model)


class OSPFAreaFilterForm(NetBoxModelFilterSetForm):
    model = OSPFArea
    fieldsets = (
        FieldSet('q', 'device_id', 'instance_id', 'filter_id', 'area_type', 'tag'),
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
