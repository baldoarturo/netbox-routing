from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import VRF
from netbox.forms import NetBoxModelImportForm
from utilities.forms.fields import CSVModelChoiceField, CSVModelMultipleChoiceField

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

    class Meta:
        model = StaticRoute
        fields = (
            "name",
            "devices",
            "vrf",
            "prefix",
            "next_hop",
            "interface_next_hop",
            "metric",
            "tag",
            "permanent",
            "description",
            "comments",
            "tags",
        )
