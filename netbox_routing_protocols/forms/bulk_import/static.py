from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.forms import NetBoxModelImportForm
from netbox_routing_protocols.choices import StaticRouteNextHopTypeChoices
from utilities.forms.fields import (
    CSVChoiceField,
    CSVModelChoiceField,
    CSVModelMultipleChoiceField,
)

from netbox_routing_protocols.models import StaticRoute

__all__ = ("StaticRouteImportForm",)


class StaticRouteImportForm(NetBoxModelImportForm):
    devices = CSVModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Names of the devices, separated by commas"),
    )
    vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of VRF"),
    )

    interface = CSVModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the interface (of the one device of the route)"),
    )
    next_hop_type = CSVChoiceField(
        choices=StaticRouteNextHopTypeChoices,
        required=False,
        help_text=_("forward (default), blackhole, unreachable, prohibit or receive"),
    )
    next_hop_vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the VRF where the next hop is resolved"),
    )

    class Meta:
        model = StaticRoute
        fields = (
            "name",
            "devices",
            "vrf",
            "prefix",
            "next_hop",
            "interface",
            "next_hop_type",
            "next_hop_vrf",
            "next_hop_global",
            "distance",
            "tag",
            "permanent",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        # An interface name only means something on one device
        if data:
            names = [
                n.strip()
                for n in str(data.get('devices') or '').split(',')
                if n.strip()
            ]
            self.fields['interface'].queryset = Interface.objects.filter(
                device__name__in=names
            )

    def clean_next_hop_type(self):
        return (
            self.cleaned_data.get('next_hop_type')
            or StaticRouteNextHopTypeChoices.FORWARD
        )

    def _post_clean(self):
        super()._post_clean()
        devices = self.cleaned_data.get('devices')
        if devices and not self.errors:
            try:
                self.instance.validate_devices(devices)
            except ValidationError as e:
                self.add_error(None, e)
