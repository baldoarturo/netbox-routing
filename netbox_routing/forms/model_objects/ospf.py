from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import ChoiceField

from dcim.models import Interface, Device
from ipam.models import VRF, IPAddress
from netbox.forms import PrimaryModelForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, get_field_value
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet
from utilities.forms.widgets import HTMXSelect

from netbox_routing.choices import OSPFNetworkTypeChoices
from netbox_routing.choices.ospf import OSPFExternalMetricTypeChoices
from netbox_routing.constants.ospf import OSPF_INTERFACE_TIMERS
from netbox_routing.models import (
    BGPRouter,
    EIGRPRouter,
    ISISInstance,
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
)

__all__ = (
    'OSPFAreaForm',
    'OSPFInstanceForm',
    'OSPFInterfaceForm',
    'OSPFNetworkForm',
    'OSPFRedistributionForm',
)


class OSPFInstanceForm(PrimaryModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        selector=True,
        label=_('Device'),
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
    )

    fieldsets = (
        FieldSet(
            'name',
            'description',
        ),
        FieldSet(
            'device',
            name=_('Device'),
        ),
        FieldSet(
            'process_id',
            'router_id',
            'vrf',
            name=_('Instance'),
        ),
        FieldSet(
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            name=_('Default Information'),
        ),
    )

    class Meta:
        model = OSPFInstance
        fields = (
            'name',
            'router_id',
            'process_id',
            'device',
            'vrf',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # An empty metric type falls back to its default (see clean()).
        self.fields['default_originate_metric_type'].required = False

    def clean(self):
        if not self.cleaned_data.get('default_originate_metric_type'):
            self.cleaned_data['default_originate_metric_type'] = (
                OSPFExternalMetricTypeChoices.TYPE_2
            )
        return super().clean()


class OSPFAreaForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('instance', 'area_id', 'area_type', 'description', name=_('Area')),
        FieldSet('default_cost', name=_('Stub / NSSA')),
        FieldSet(
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            name=_('NSSA'),
        ),
    )

    class Meta:
        model = OSPFArea
        fields = (
            'instance',
            'area_id',
            'area_type',
            'default_cost',
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFInterfaceForm(PrimaryModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
        query_params={
            'device_id': '$device',
        },
    )
    area = DynamicModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        selector=True,
        label=_('Area'),
        query_params={
            'instance_id': '$instance',
        },
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        selector=True,
        label=_('Interface'),
        query_params={
            'device_id': '$device',
        },
    )
    network_type = ChoiceField(
        choices=OSPFNetworkTypeChoices,
        required=True,
        label=_('Network Type'),
    )

    fieldsets = (
        FieldSet(
            'area',
            'description',
            name=_('Session'),
        ),
        FieldSet(
            'device',
            'instance',
            name=_('Instance'),
        ),
        FieldSet(
            'interface',
            'network_type',
            'priority',
            'cost',
            'passive',
            'bfd',
            'mtu_ignore',
            name=_('Interface'),
        ),
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            name=_('Timers'),
        ),
        FieldSet(
            'authentication',
            'passphrase',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = OSPFInterface
        fields = (
            'device',
            'instance',
            'area',
            'interface',
            'network_type',
            'passive',
            'priority',
            'cost',
            'bfd',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'mtu_ignore',
            'authentication',
            'passphrase',
            'description',
            'comments',
            'tags',
            'owner',
        )

        widgets = {
            'bfd': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'passive': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['device'] = self.instance.interface.device.pk
        # An empty timer falls back to its RFC 2328 default (see clean()).
        for name in OSPF_INTERFACE_TIMERS:
            self.fields[name].required = False

    def clean(self):
        for name, (_min, _max, default) in OSPF_INTERFACE_TIMERS.items():
            if self.cleaned_data.get(name) is None:
                self.cleaned_data[name] = default
        super().clean()
        if self.cleaned_data.get('instance') and self.cleaned_data.get('interface'):
            if (
                self.cleaned_data.get('instance').device
                != self.cleaned_data.get('interface').device
            ):
                raise ValidationError(
                    {
                        'instance': _(
                            'OSPF Instance Device and Interface Device must match'
                        ),
                        'interface': _(
                            'OSPF Instance Device and Interface Device must match'
                        ),
                    }
                )


class OSPFNetworkForm(PrimaryModelForm):
    ospf_interface = DynamicModelChoiceField(
        queryset=OSPFInterface.objects.all(),
        required=True,
        selector=True,
        label=_('OSPF Interface'),
    )
    ip_address = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=True,
        selector=True,
        label=_('IP Address'),
        help_text=_('Must be an IPv4 address assigned to the OSPF interface'),
    )

    fieldsets = (
        FieldSet(
            'ospf_interface',
            'ip_address',
            'description',
            name=_('Network'),
        ),
    )

    class Meta:
        model = OSPFNetwork
        fields = (
            'ospf_interface',
            'ip_address',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFRedistributionForm(PrimaryModelForm):
    # Only used to narrow the instance and the sources to one device; the model
    # validates that the source really is on the instance's device.
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
        query_params={'device_id': '$device'},
    )
    ospf_source = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Source'),
        query_params={'device_id': '$device'},
    )
    eigrp_source = DynamicModelChoiceField(
        queryset=EIGRPRouter.objects.all(),
        required=False,
        selector=True,
        label=_('EIGRP Source'),
        query_params={'device_id': '$device'},
    )
    bgp_source = DynamicModelChoiceField(
        queryset=BGPRouter.objects.all(),
        required=False,
        selector=True,
        label=_('BGP Source'),
        help_text=_('A BGP router assigned to the device'),
    )
    isis_source = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Source'),
        query_params={'device_id': '$device'},
    )

    fieldsets = (
        FieldSet(
            'device',
            'instance',
            'protocol',
            'description',
            name=_('Redistribution'),
        ),
        FieldSet(
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            name=_('Source (not for static)'),
        ),
        FieldSet(
            'metric',
            'metric_type',
            'subnets',
            'route_tag',
            'route_policy',
            name=_('Attributes'),
        ),
    )

    class Meta:
        model = OSPFRedistribution
        widgets = {
            'protocol': HTMXSelect(),
        }
        fields = (
            'device',
            'instance',
            'protocol',
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            'metric',
            'metric_type',
            'subnets',
            'route_tag',
            'route_policy',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['device'] = self.instance.instance.device_id
        # An empty metric type falls back to its default (see clean()).
        self.fields['metric_type'].required = False

        # Only the source of the selected protocol is shown (none for connected,
        # static or while no protocol is selected)
        protocol = get_field_value(self, 'protocol')
        for source_protocol, field in OSPFRedistribution.SOURCE_FIELDS.items():
            if source_protocol != protocol:
                del self.fields[field]

    def clean(self):
        if not self.cleaned_data.get('metric_type'):
            self.cleaned_data['metric_type'] = OSPFExternalMetricTypeChoices.TYPE_2
        # A source left over from a previous protocol is not on the form anymore
        for source_protocol, field in OSPFRedistribution.SOURCE_FIELDS.items():
            if field not in self.fields:
                setattr(self.instance, field, None)
        return super().clean()
