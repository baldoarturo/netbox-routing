from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import ChoiceField

from dcim.models import Interface, Device
from ipam.models import VRF, IPAddress
from netbox.forms import PrimaryModelForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing.choices import OSPFNetworkTypeChoices
from netbox_routing.choices.ospf import OSPFExternalMetricTypeChoices
from netbox_routing.constants.ospf import OSPF_INTERFACE_TIMERS
from netbox_routing.models import OSPFArea, OSPFInstance, OSPFInterface, OSPFNetwork

__all__ = (
    'OSPFAreaForm',
    'OSPFInstanceForm',
    'OSPFInterfaceForm',
    'OSPFNetworkForm',
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
    class Meta:
        model = OSPFArea
        fields = (
            'area_id',
            'area_type',
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
