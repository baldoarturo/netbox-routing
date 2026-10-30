from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from dcim.models import Interface, Device
from ipam.models import VRF
from netbox.forms import NetBoxModelImportForm
from ipam.models import IPAddress
from utilities.forms.fields import (
    CSVModelChoiceField,
    CSVChoiceField,
    CSVMultipleChoiceField,
)
from netbox_routing_protocols.choices.ospf import (
    OSPFAddressFamilyChoices,
    OSPFRangeTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFNetworkTypeChoices,
    OSPFRedistributionProtocolChoices,
    OSPFRouteTypeChoices,
    OSPFSegmentIdentifierChoices,
    OSPFSRAlgorithmChoices,
)

from netbox_routing_protocols.models import (
    BGPRouter,
    EIGRPRouter,
    ISISInstance,
    OSPFAreaRange,
    OSPFAuthenticationMixin,
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
    OSPFNeighbor,
    OSPFNetwork,
    OSPFPrefixSID,
    OSPFRedistribution,
    OSPFSummaryAddress,
    OSPFVirtualLink,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    "OSPFInstanceImportForm",
    "OSPFAreaImportForm",
    "OSPFInterfaceImportForm",
    "OSPFNetworkImportForm",
    "OSPFRedistributionImportForm",
    "OSPFVirtualLinkImportForm",
    "OSPFSummaryAddressImportForm",
    "OSPFNeighborImportForm",
    "OSPFAreaRangeImportForm",
    "OSPFPrefixSIDImportForm",
)


class _DefaultsMixin:
    """A column with a default in the model can be left out of the CSV."""

    def _defaulted_fields(self):
        for name in self._meta.fields:
            try:
                model_field = self._meta.model._meta.get_field(name)
            except FieldDoesNotExist:
                continue  # a column that is not a field, like the device
            if model_field.has_default() and not model_field.null:
                yield name, model_field

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        for name, _field in self._defaulted_fields():
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        for name, model_field in self._defaulted_fields():
            if cleaned.get(name) in (None, '', []) and name not in self.errors:
                cleaned[name] = model_field.get_default()
        return cleaned


class OSPFInstanceImportForm(_DefaultsMixin, NetBoxModelImportForm):
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

    address_family = CSVChoiceField(
        choices=OSPFAddressFamilyChoices,
        required=False,
        help_text=_("IPv4 (OSPFv2, the default) or IPv6 (OSPFv3)"),
    )
    import_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the import route policy'),
    )
    export_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the export route policy'),
    )

    class Meta:
        model = OSPFInstance
        fields = (
            "name",
            "router_id",
            "device",
            "vrf",
            "address_family",
            "default_originate",
            "default_originate_always",
            "default_originate_metric",
            "default_originate_metric_type",
            "import_policy",
            "export_policy",
            *OSPFInstance.ADVANCED_FIELDS,
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            "description",
            "comments",
            "tags",
        )


class OSPFAreaImportForm(_DefaultsMixin, NetBoxModelImportForm):
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
            "fast_reroute",
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


def _narrow(form, data, **querysets):
    """
    Limit the choices of the foreign keys to what belongs to the device (and the
    instance) of the row: names and area IDs are only unique inside them.
    """
    if not data:
        return
    device = data.get('device')
    instance = data.get('instance')
    for name, builder in querysets.items():
        form.fields[name].queryset = builder(device, instance)


def _of_device(model, path='device'):
    return lambda device, instance: model.objects.filter(**{f'{path}__name': device})


def _areas(device, instance):
    return OSPFArea.objects.filter(
        instance__device__name=device, instance__name=instance
    )


class OSPFInterfaceImportForm(_DefaultsMixin, NetBoxModelImportForm):
    device = CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
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
        to_field_name="area_id",
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
            "ttl_security",
            "ttl_security_hops",
            "mtu_ignore",
            "unnumbered",
            "adjacency_sid",
            "ldp_sync",
            "fast_reroute",
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

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(
            self,
            data,
            instance=_of_device(OSPFInstance, 'device'),
            area=_areas,
            interface=_of_device(Interface),
        )


def _instance_field():
    return CSVModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of the OSPF instance"),
    )


def _device_field():
    return CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name="name",
        help_text=_("Name of the device of the instance"),
    )


def _ospf_interface_field():
    return CSVModelChoiceField(
        queryset=OSPFInterface.objects.all(),
        required=True,
        to_field_name="interface__name",
        help_text=_("Name of the interface that runs OSPF"),
    )


def _narrow_ospf_interface(form, data):
    _narrow(
        form,
        data,
        ospf_interface=_of_device(OSPFInterface, 'instance__device'),
    )


class OSPFNetworkImportForm(NetBoxModelImportForm):
    device = _device_field()
    ospf_interface = _ospf_interface_field()
    ip_address = CSVModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=True,
        to_field_name="address",
        help_text=_("IPv4 address with its mask, assigned to the interface"),
    )

    class Meta:
        model = OSPFNetwork
        fields = (
            "device",
            "ospf_interface",
            "ip_address",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow_ospf_interface(self, data)
        if data:
            self.fields['ip_address'].queryset = IPAddress.objects.filter(
                interface__device__name=data.get('device'),
                interface__name=data.get('ospf_interface'),
            )


class OSPFNeighborImportForm(NetBoxModelImportForm):
    device = _device_field()
    ospf_interface = _ospf_interface_field()

    class Meta:
        model = OSPFNeighbor
        fields = (
            "device",
            "ospf_interface",
            "ip_address",
            "priority",
            "poll_interval",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow_ospf_interface(self, data)


class OSPFRedistributionImportForm(_DefaultsMixin, NetBoxModelImportForm):
    device = _device_field()
    instance = _instance_field()
    protocol = CSVChoiceField(
        choices=OSPFRedistributionProtocolChoices,
        required=True,
        help_text=_("Where the routes come from"),
    )
    ospf_source = CSVModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the OSPF instance, for protocol ospf"),
    )
    eigrp_source = CSVModelChoiceField(
        queryset=EIGRPRouter.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the EIGRP router, for protocol eigrp"),
    )
    bgp_source = CSVModelChoiceField(
        queryset=BGPRouter.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the BGP router, for protocol bgp"),
    )
    isis_source = CSVModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the IS-IS instance, for protocol isis"),
    )
    metric_type = CSVChoiceField(
        choices=OSPFExternalMetricTypeChoices,
        required=False,
        help_text=_("1 or 2; empty is type 2"),
    )
    ospf_match = CSVMultipleChoiceField(
        choices=OSPFRouteTypeChoices,
        required=False,
        help_text=_("Route types, separated by commas, for protocol ospf"),
    )
    route_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name="name",
        help_text=_("Name of the route policy"),
    )

    class Meta:
        model = OSPFRedistribution
        fields = (
            "device",
            "instance",
            "protocol",
            "ospf_source",
            "eigrp_source",
            "bgp_source",
            "isis_source",
            "ospf_match",
            "metric",
            "metric_type",
            "subnets",
            "route_tag",
            "route_policy",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(
            self,
            data,
            instance=_of_device(OSPFInstance),
            ospf_source=_of_device(OSPFInstance),
            isis_source=_of_device(ISISInstance),
        )


class OSPFVirtualLinkImportForm(_DefaultsMixin, NetBoxModelImportForm):
    device = _device_field()
    instance = _instance_field()
    transit_area = CSVModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        to_field_name="area_id",
        help_text=_("Area ID of the transit area"),
    )

    class Meta:
        model = OSPFVirtualLink
        fields = (
            "device",
            "instance",
            "transit_area",
            "remote_router_id",
            "hello_interval",
            "dead_interval",
            "retransmit_interval",
            "transmit_delay",
            "ttl_security",
            "ttl_security_hops",
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(
            self,
            data,
            instance=_of_device(OSPFInstance),
            transit_area=_areas,
        )


class OSPFSummaryAddressImportForm(NetBoxModelImportForm):
    device = _device_field()
    instance = _instance_field()

    class Meta:
        model = OSPFSummaryAddress
        fields = (
            "device",
            "instance",
            "prefix",
            "not_advertise",
            "route_tag",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(self, data, instance=_of_device(OSPFInstance))


class OSPFAreaRangeImportForm(_DefaultsMixin, NetBoxModelImportForm):
    device = _device_field()
    instance = _instance_field()
    area = CSVModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        to_field_name="area_id",
        help_text=_("Area ID"),
    )
    range_type = CSVChoiceField(
        choices=OSPFRangeTypeChoices,
        required=False,
        help_text=_("Type of the range"),
    )

    class Meta:
        model = OSPFAreaRange
        fields = (
            "device",
            "instance",
            "area",
            "prefix",
            "range_type",
            "advertise",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(
            self,
            data,
            instance=_of_device(OSPFInstance),
            area=_areas,
        )


class OSPFPrefixSIDImportForm(_DefaultsMixin, NetBoxModelImportForm):
    device = _device_field()
    instance = _instance_field()
    sid_type = CSVChoiceField(
        choices=OSPFSegmentIdentifierChoices,
        required=False,
        help_text=_("index or absolute"),
    )
    algorithm = CSVChoiceField(
        choices=OSPFSRAlgorithmChoices,
        required=False,
        help_text=_("SR algorithm"),
    )

    class Meta:
        model = OSPFPrefixSID
        fields = (
            "device",
            "instance",
            "prefix",
            "sid_type",
            "sid",
            "algorithm",
            "node_sid",
            "no_php",
            "explicit_null",
            "description",
            "comments",
            "tags",
        )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        _narrow(self, data, instance=_of_device(OSPFInstance))
