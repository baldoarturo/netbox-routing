from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.forms import PrimaryModelForm
from netbox_routing_plugin.models import StaticRoute
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import FieldSet


class StaticRouteForm(PrimaryModelForm):
    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_('Devices'),
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label=_('VRF'),
    )

    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        selector=True,
        query_params={'device_id': '$devices'},
        label=_('Interface Next Hop'),
    )
    next_hop_vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label=_('Next Hop VRF'),
    )

    fieldsets = (
        FieldSet(
            'devices',
            'vrf',
        ),
        FieldSet(
            'prefix',
            'next_hop_type',
            'next_hop',
            'interface',
            'distance',
            name=_('Route'),
        ),
        FieldSet(
            'next_hop_vrf',
            'next_hop_global',
            name=_('Route leaking'),
        ),
        FieldSet(
            'name',
            'description',
            'tag',
            'permanent',
            name=_('Metadata'),
        ),
        FieldSet(
            'tags',
            name=_('Tags'),
        ),
    )

    class Meta:
        model = StaticRoute
        fields = (
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'interface',
            'next_hop_type',
            'next_hop_vrf',
            'next_hop_global',
            'name',
            'distance',
            'permanent',
            'tag',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def _post_clean(self):
        super()._post_clean()
        devices = self.cleaned_data.get('devices')
        if devices and not self.errors:
            try:
                self.instance.validate_devices(devices)
            except ValidationError as e:
                self.add_error(None, e)

    def __init__(self, data=None, instance=None, *args, **kwargs):
        super().__init__(*args, data=data, instance=instance, **kwargs)

        if self.instance and self.instance.pk is not None:
            self.fields['devices'].initial = self.instance.devices.all().values_list(
                'id', flat=True
            )
