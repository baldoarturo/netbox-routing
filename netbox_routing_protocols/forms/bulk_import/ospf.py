from django.utils.translation import gettext_lazy as _

from dcim.models import Interface, Device
from ipam.models import VRF
from netbox.forms import NetBoxModelImportForm
from utilities.forms.fields import CSVModelChoiceField, CSVChoiceField
from netbox_routing_protocols.choices.ospf import OSPFNetworkTypeChoices

from netbox_routing_protocols.models import (
    OSPFAuthenticationMixin,
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
)

__all__ = (
    "OSPFInstanceImportForm",
    "OSPFAreaImportForm",
    "OSPFInterfaceImportForm",
)


class OSPFInstanceImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of device"),
    )
    vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of VRF"),
    )

    class Meta:
        model = OSPFInstance
        fields = (
            "name",
            "router_id",
            "device",
            "vrf",
            "default_originate",
            "default_originate_always",
            "default_originate_metric",
            "default_originate_metric_type",
            *OSPFInstance.ADVANCED_FIELDS,
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            "description",
            "comments",
            "tags",
        )


class OSPFAreaImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of the instance's device"),
    )
    instance = CSVModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of OSPF Instance"),
    )

    class Meta:
        model = OSPFArea
        fields = (
            "device",
            "instance",
            "area_id",
            "area_type",
            "default_cost",
            "nssa_translate_always",
            "nssa_no_redistribution",
            "nssa_default_originate",
            "traffic_engineering",
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        if data:
            # Instance names are only unique per device
            self.fields['instance'].queryset = OSPFInstance.objects.filter(
                device__name=data.get('device')
            )


class OSPFInterfaceImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of device"),
    )
    instance = CSVModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of OSPF Instance"),
    )
    area = CSVModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Area ID"),
    )
    interface = CSVModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of interface"),
    )
    network_type = CSVChoiceField(
        choices=OSPFNetworkTypeChoices.CHOICES,
        required=True,
        help_text=_("OSPF network type"),
    )

    class Meta:
        model = OSPFInterface
        fields = (
            "device",
            "instance",
            "area",
            "interface",
            "network_type",
            "passive",
            "priority",
            "bfd",
            "cost",
            "hello_interval",
            "dead_interval",
            "retransmit_interval",
            "transmit_delay",
            "mtu_ignore",
            "te_metric",
            "te_max_reservable_bandwidth",
            "te_admin_group",
            "prefix_suppression",
            "database_filter_all_out",
            "flood_reduction",
            "demand_circuit",
            "authentication",
            "passphrase",
            "authentication_key_id",
            "message_digest_algorithm",
            "key_chain",
            "show_md5",
            "description",
            "comments",
            "tags",
        )
