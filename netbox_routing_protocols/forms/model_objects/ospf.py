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
from utilities.forms.widgets import DateTimePicker, HTMXSelect

from netbox_routing_protocols.choices import OSPFNetworkTypeChoices
from netbox_routing_protocols.choices.ospf import (
    OSPFAddressFamilyChoices,
    OSPFAuthenticationChoices,
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFMessageDigestAlgorithmChoices,
    OSPFRedistributionProtocolChoices,
    OSPFRouteTypeChoices,
)
from netbox_routing_protocols.constants.ospf import (
    OSPF_INTERFACE_TIMERS,
    OSPF_PRIORITY_DEFAULT,
)
from netbox_routing_protocols.models import (
    OSPFAuthenticationMixin,
    BGPInstance,
    EIGRPRouter,
    ISISInstance,
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFAuthenticationKey,
    OSPFNeighbor,
    OSPFAreaRange,
    OSPFPrefixSID,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    'OSPFAreaForm',
    'OSPFInstanceForm',
    'OSPFInterfaceForm',
    'OSPFNetworkForm',
    'OSPFRedistributionForm',
    'OSPFVirtualLinkForm',
    'OSPFSummaryAddressForm',
    'OSPFAuthenticationKeyForm',
    'OSPFNeighborForm',
    'OSPFAreaRangeForm',
    'OSPFPrefixSIDForm',
)


def _default_algorithm(authentication):
    """HMAC-SHA-256 for the authentication trailer (RFC 7166), else MD5."""
    if authentication == OSPFAuthenticationChoices.TRAILER:
        return OSPFMessageDigestAlgorithmChoices.HMAC_SHA_256
    return OSPFMessageDigestAlgorithmChoices.MD5


def _limit_authentication(form, version):
    """Offer only the authentication types of the address family (None: all)."""
    if version is None:
        return
    allowed = (
        OSPFAuthenticationChoices.IPV6
        if version == 6
        else OSPFAuthenticationChoices.IPV4
    )
    field = form.fields['authentication']
    field.choices = [
        choice for choice in field.choices if not choice[0] or choice[0] in allowed
    ]


def _instance_version(form):
    """The IP version of the instance chosen in the form, or None if none yet."""
    value = get_field_value(form, 'instance')
    if not value:
        return None
    instance = OSPFInstance.objects.filter(pk=value).first()
    return instance.ip_version if instance else None


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

    address_family = forms.ChoiceField(
        choices=OSPFAddressFamilyChoices,
        initial=OSPFAddressFamilyChoices.IPV4,
        label=_('Address Family'),
        help_text=_(
            'IPv4 is OSPFv2 (RFC 2328), IPv6 is OSPFv3 (RFC 5340). It cannot be '
            'changed once the instance exists'
        ),
        required=False,
        widget=HTMXSelect(),
    )
    import_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
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
            'address_family',
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
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet(*OSPFInstance.ADVANCED_FIELDS, name=_('Advanced')),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = OSPFInstance
        fields = (
            'name',
            'router_id',
            'device',
            'vrf',
            'address_family',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            'import_policy',
            'export_policy',
            *OSPFInstance.ADVANCED_FIELDS,
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # The family is fixed: another family needs another instance
            self.fields['address_family'].disabled = True
        family = get_field_value(self, 'address_family')
        _limit_authentication(self, 6 if family == OSPFAddressFamilyChoices.IPV6 else 4)
        # Options left empty fall back to their default (see clean()).
        self.fields['default_originate_metric_type'].required = False
        self.fields['message_digest_algorithm'].required = False
        for name in OSPFInstance.ADVANCED_FIELDS:
            if not OSPFInstance._meta.get_field(name).null:
                self.fields[name].required = False

    def clean(self):
        if not self.cleaned_data.get('address_family'):
            self.cleaned_data['address_family'] = OSPFAddressFamilyChoices.IPV4
        if not self.cleaned_data.get('default_originate_metric_type'):
            self.cleaned_data['default_originate_metric_type'] = (
                OSPFExternalMetricTypeChoices.TYPE_2
            )
        for name in OSPFInstance.ADVANCED_FIELDS:
            field = OSPFInstance._meta.get_field(name)
            if not field.null and self.cleaned_data.get(name) in (None, ''):
                self.cleaned_data[name] = field.get_default()
        if not self.cleaned_data.get('message_digest_algorithm'):
            self.cleaned_data['message_digest_algorithm'] = _default_algorithm(
                self.cleaned_data.get('authentication')
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
        FieldSet('traffic_engineering', 'fast_reroute', name=_('Advanced')),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name=_('Authentication'),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # An empty algorithm falls back to its default (see clean())
        self.fields['message_digest_algorithm'].required = False
        _limit_authentication(self, _instance_version(self))

    def clean(self):
        if not self.cleaned_data.get('message_digest_algorithm'):
            self.cleaned_data['message_digest_algorithm'] = _default_algorithm(
                self.cleaned_data.get('authentication')
            )
        # Area 0 is the backbone: the untouched default type becomes Backbone
        area = OSPFArea(area_id=self.cleaned_data.get('area_id'))
        if (
            area.area_number == 0
            and self.cleaned_data.get('area_type') == OSPFAreaTypeChoices.STANDARD
        ):
            self.cleaned_data['area_type'] = OSPFAreaTypeChoices.BACKBONE
        return super().clean()

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
            'traffic_engineering',
            'fast_reroute',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
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
            'unnumbered',
            'adjacency_sid',
            'ldp_sync',
            'fast_reroute',
            name=_('Interface'),
        ),
        FieldSet(
            'te_metric',
            'te_max_reservable_bandwidth',
            'te_admin_group',
            name=_('Traffic Engineering'),
        ),
        FieldSet(
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
            name=_('Options'),
        ),
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'ttl_security',
            'ttl_security_hops',
            name=_('Timers'),
        ),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
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
            'ttl_security',
            'ttl_security_hops',
            'mtu_ignore',
            'unnumbered',
            'adjacency_sid',
            'ldp_sync',
            'fast_reroute',
            'te_metric',
            'te_max_reservable_bandwidth',
            'te_admin_group',
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
            'authentication',
            'passphrase',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
            'show_md5',
            'description',
            'comments',
            'tags',
            'owner',
        )

        widgets = {
            'bfd': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'passive': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'prefix_suppression': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'database_filter_all_out': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'flood_reduction': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'demand_circuit': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['device'] = self.instance.interface.device.pk
        # An empty timer or priority falls back to its default (see clean()).
        for name in (*OSPF_INTERFACE_TIMERS, 'priority', 'message_digest_algorithm'):
            self.fields[name].required = False
        _limit_authentication(self, _instance_version(self))

    def clean(self):
        for name, (_min, _max, default) in OSPF_INTERFACE_TIMERS.items():
            if self.cleaned_data.get(name) is None:
                self.cleaned_data[name] = default
        if self.cleaned_data.get('priority') is None:
            self.cleaned_data['priority'] = OSPF_PRIORITY_DEFAULT
        if not self.cleaned_data.get('message_digest_algorithm'):
            self.cleaned_data['message_digest_algorithm'] = _default_algorithm(
                self.cleaned_data.get('authentication')
            )
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
        query_params={'unnumbered': False, 'address_family': 'ipv4'},
        label=_('OSPF Interface'),
    )
    ip_address = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=True,
        selector=True,
        label=_('IP Address'),
        help_text=_(
            'Must be an IPv4 address assigned to the OSPF interface. Networks are '
            'for IPv4 instances: OSPFv3 is enabled on the interface'
        ),
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
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('BGP Source'),
        help_text=_('A BGP instance on the device'),
    )
    isis_source = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Source'),
        query_params={'device_id': '$device'},
    )
    ospf_match = forms.MultipleChoiceField(
        choices=OSPFRouteTypeChoices,
        required=False,
        label=_('OSPF Route Types'),
        help_text=_('Empty uses the platform default'),
    )
    route_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Route Policy'),
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
            'ospf_match',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            name=_('Source'),
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
            'ospf_match',
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
        # The route types only make sense when the source is OSPF
        if protocol != OSPFRedistributionProtocolChoices.OSPF:
            del self.fields['ospf_match']

    def clean(self):
        if not self.cleaned_data.get('metric_type'):
            self.cleaned_data['metric_type'] = OSPFExternalMetricTypeChoices.TYPE_2
        # A source left over from a previous protocol is not on the form anymore
        for field in OSPFRedistribution.SOURCE_FIELDS.values():
            if field not in self.fields:
                setattr(self.instance, field, None)
        if 'ospf_match' not in self.fields:
            self.instance.ospf_match = []
        return super().clean()


class OSPFVirtualLinkForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )
    transit_area = DynamicModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        selector=True,
        label=_('Transit Area'),
        query_params={'instance_id': '$instance'},
    )

    fieldsets = (
        FieldSet(
            'instance',
            'transit_area',
            'remote_router_id',
            'description',
            name=_('Virtual Link'),
        ),
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'ttl_security',
            'ttl_security_hops',
            name=_('Timers'),
        ),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = OSPFVirtualLink
        fields = (
            'instance',
            'transit_area',
            'remote_router_id',
            *OSPF_INTERFACE_TIMERS,
            'ttl_security',
            'ttl_security_hops',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Empty timers and algorithm fall back to their default (see clean())
        for name in (*OSPF_INTERFACE_TIMERS, 'message_digest_algorithm'):
            self.fields[name].required = False
        _limit_authentication(self, _instance_version(self))

    def clean(self):
        for name, (_min, _max, default) in OSPF_INTERFACE_TIMERS.items():
            if self.cleaned_data.get(name) is None:
                self.cleaned_data[name] = default
        if not self.cleaned_data.get('message_digest_algorithm'):
            self.cleaned_data['message_digest_algorithm'] = _default_algorithm(
                self.cleaned_data.get('authentication')
            )
        return super().clean()


class OSPFSummaryAddressForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'prefix',
            'not_advertise',
            'route_tag',
            'description',
            name=_('Summary Address'),
        ),
    )

    class Meta:
        model = OSPFSummaryAddress
        fields = (
            'instance',
            'prefix',
            'not_advertise',
            'route_tag',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFNeighborForm(PrimaryModelForm):
    ospf_interface = DynamicModelChoiceField(
        queryset=OSPFInterface.objects.all(),
        required=True,
        selector=True,
        label=_('OSPF Interface'),
        help_text=_('A non-broadcast or point-to-multipoint interface'),
    )

    fieldsets = (
        FieldSet(
            'ospf_interface',
            'ip_address',
            'priority',
            'poll_interval',
            'description',
            name=_('Neighbor'),
        ),
    )

    class Meta:
        model = OSPFNeighbor
        fields = (
            'ospf_interface',
            'ip_address',
            'priority',
            'poll_interval',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFAreaRangeForm(PrimaryModelForm):
    area = DynamicModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=True,
        selector=True,
        label=_('Area'),
    )

    fieldsets = (
        FieldSet(
            'area',
            'prefix',
            'range_type',
            'advertise',
            'description',
            name=_('Address Range'),
        ),
    )

    class Meta:
        model = OSPFAreaRange
        fields = (
            'area',
            'prefix',
            'range_type',
            'advertise',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFPrefixSIDForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'prefix',
            'sid_type',
            'sid',
            'algorithm',
            'description',
            name=_('Prefix SID'),
        ),
        FieldSet('node_sid', 'no_php', 'explicit_null', name=_('Flags')),
    )

    class Meta:
        model = OSPFPrefixSID
        fields = (
            'instance',
            'prefix',
            'sid_type',
            'sid',
            'algorithm',
            'node_sid',
            'no_php',
            'explicit_null',
            'description',
            'comments',
            'tags',
            'owner',
        )


class OSPFAuthenticationKeyForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    area = DynamicModelChoiceField(
        queryset=OSPFArea.objects.all(),
        required=False,
        selector=True,
        label=_('Area'),
    )
    ospf_interface = DynamicModelChoiceField(
        queryset=OSPFInterface.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Interface'),
    )
    virtual_link = DynamicModelChoiceField(
        queryset=OSPFVirtualLink.objects.all(),
        required=False,
        selector=True,
        label=_('Virtual Link'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'area',
            'ospf_interface',
            'virtual_link',
            name=_('Belongs to (choose one)'),
        ),
        FieldSet(
            'key_id',
            'passphrase',
            'message_digest_algorithm',
            'description',
            name=_('Key'),
        ),
        FieldSet(
            'accept_from',
            'send_from',
            'send_until',
            'accept_until',
            name=_('Lifetimes (RFC 7474)'),
        ),
    )

    class Meta:
        model = OSPFAuthenticationKey
        fields = (
            'instance',
            'area',
            'ospf_interface',
            'virtual_link',
            'key_id',
            'passphrase',
            'message_digest_algorithm',
            'accept_from',
            'send_from',
            'send_until',
            'accept_until',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'accept_from': DateTimePicker(),
            'send_from': DateTimePicker(),
            'send_until': DateTimePicker(),
            'accept_until': DateTimePicker(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['message_digest_algorithm'].required = False

    def clean(self):
        if not self.cleaned_data.get('message_digest_algorithm'):
            self.cleaned_data['message_digest_algorithm'] = _default_algorithm(
                self._parent_authentication()
            )
        return super().clean()

    def _parent_authentication(self):
        for name in OSPFAuthenticationKey.PARENTS:
            parent = self.cleaned_data.get(name)
            if parent is not None:
                return parent.authentication
        return None
