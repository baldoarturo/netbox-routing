import django_filters
import netaddr
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF, IPAddress
from utilities.filters import MultiValueCharFilter
from utilities.filtersets import register_filterset

from netbox.filtersets import NetBoxModelFilterSet
from netbox_routing_protocols.choices.ospf import OSPFAuthenticationChoices
from netbox_routing_protocols.choices.ospf import (
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFGracefulRestartChoices,
    OSPFMessageDigestAlgorithmChoices,
    OSPFNetworkTypeChoices,
    OSPFRangeTypeChoices,
    OSPFRedistributionProtocolChoices,
    OSPFRouteTypeChoices,
)
from netbox_routing_protocols.models import (
    OSPFAuthenticationMixin,
    BGPRouter,
    EIGRPRouter,
    ISISInstance,
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
    OSPFAreaRange,
)

__all__ = (
    'OSPFAreaFilterSet',
    'OSPFInstanceFilterSet',
    'OSPFInterfaceFilterSet',
    'OSPFNetworkFilterSet',
    'OSPFRedistributionFilterSet',
    'OSPFVirtualLinkFilterSet',
    'OSPFSummaryAddressFilterSet',
    'OSPFNeighborFilterSet',
    'OSPFAreaRangeFilterSet',
)


@register_filterset
class OSPFInstanceFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device',
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf',
        queryset=VRF.objects.all(),
        label='VRF (ID)',
    )
    vrf = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf__name',
        queryset=VRF.objects.all(),
        to_field_name='name',
        label='VRF',
    )

    default_originate_metric_type = django_filters.MultipleChoiceFilter(
        choices=OSPFExternalMetricTypeChoices,
        label=_('Default Originate Metric Type'),
    )
    graceful_restart = django_filters.MultipleChoiceFilter(
        choices=OSPFGracefulRestartChoices,
        label=_('Graceful Restart'),
    )
    router_id = MultiValueCharFilter(
        method='filter_rid',
        label=_('Router ID'),
    )

    class Meta:
        model = OSPFInstance
        fields = (
            'device_id',
            'device',
            'name',
            'vrf_id',
            'vrf',
            'router_id',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            *OSPFInstance.ADVANCED_FIELDS,
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(device__name__icontains=value)
            | Q(router_id__icontains=value)
        )
        return queryset.filter(qs_filter)

    def filter_rid(self, queryset, name, value):
        try:
            return queryset.filter(**{f'{name}__in': value})
        except ValidationError:
            return queryset.none()


@register_filterset
class OSPFAreaFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        to_field_name='id',
        label=_('Device (ID)'),
    )
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    instance = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__name',
        queryset=OSPFInstance.objects.all(),
        to_field_name='name',
        label=_('Instance'),
    )

    area_id = MultiValueCharFilter(
        method='filter_aid',
        label=_('Area ID'),
    )

    area_type = django_filters.MultipleChoiceFilter(
        choices=OSPFAreaTypeChoices,
        label=_('Area Type'),
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
            'traffic_engineering',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(area_id__icontains=value)
        return queryset.filter(qs_filter)

    def filter_aid(self, queryset, name, value):
        try:
            return queryset.filter(**{f'{name}__in': value})
        except ValidationError:
            return queryset.none()


@register_filterset
class OSPFInterfaceFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=OSPFInstance.objects.all(),
        label='Instance (ID)',
    )
    instance = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__name',
        queryset=OSPFInstance.objects.all(),
        to_field_name='name',
        label='Instance',
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__vrf',
        queryset=VRF.objects.all(),
        label='VRF (ID)',
    )
    vrf = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__vrf__name',
        queryset=VRF.objects.all(),
        to_field_name='name',
        label='VRF',
    )
    area_id = django_filters.ModelMultipleChoiceFilter(
        field_name='area',
        queryset=OSPFArea.objects.all(),
        label='Area (ID)',
    )
    area = django_filters.ModelMultipleChoiceFilter(
        field_name='area__area_id',
        queryset=OSPFArea.objects.all(),
        to_field_name='area_id',
        label='Area',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='interface__device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='interface__device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device',
    )
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='interface',
        queryset=Interface.objects.all(),
        label='Interface (ID)',
    )
    interface = django_filters.ModelMultipleChoiceFilter(
        field_name='interface__name',
        queryset=Interface.objects.all(),
        to_field_name='name',
        label='Interface',
    )

    network_type = django_filters.MultipleChoiceFilter(
        choices=OSPFNetworkTypeChoices,
        label=_('Network Type'),
    )
    message_digest_algorithm = django_filters.MultipleChoiceFilter(
        choices=OSPFMessageDigestAlgorithmChoices,
        label=_('Message Digest Algorithm'),
    )

    class Meta:
        model = OSPFInterface
        fields = (
            'instance',
            'area',
            'interface',
            'network_type',
            'passive',
            'bfd',
            'priority',
            'cost',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'mtu_ignore',
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
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(instance__name__icontains=value)
            | Q(area__area_id__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(interface__label__icontains=value)
            | Q(interface__device__name__icontains=value)
        )
        return queryset.filter(qs_filter)


@register_filterset
class OSPFNetworkFilterSet(NetBoxModelFilterSet):
    ospf_interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface',
        queryset=OSPFInterface.objects.all(),
        label=_('OSPF Interface (ID)'),
    )
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    area_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__area',
        queryset=OSPFArea.objects.all(),
        label=_('Area (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__interface__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__interface',
        queryset=Interface.objects.all(),
        label=_('Interface (ID)'),
    )
    ip_address_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ip_address',
        queryset=IPAddress.objects.all(),
        label=_('IP Address (ID)'),
    )

    class Meta:
        model = OSPFNetwork
        fields = ('ospf_interface', 'ip_address')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(ospf_interface__instance__name__icontains=value)
            | Q(ospf_interface__area__area_id__icontains=value)
            | Q(ospf_interface__interface__name__icontains=value)
            | Q(ospf_interface__interface__device__name__icontains=value)
        )
        return queryset.filter(qs_filter)


@register_filterset
class OSPFRedistributionFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    instance = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__name',
        queryset=OSPFInstance.objects.all(),
        to_field_name='name',
        label=_('Instance'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    protocol = django_filters.MultipleChoiceFilter(
        choices=OSPFRedistributionProtocolChoices,
        label=_('Protocol'),
    )
    ospf_source_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_source',
        queryset=OSPFInstance.objects.all(),
        label=_('OSPF Source (ID)'),
    )
    eigrp_source_id = django_filters.ModelMultipleChoiceFilter(
        field_name='eigrp_source',
        queryset=EIGRPRouter.objects.all(),
        label=_('EIGRP Source (ID)'),
    )
    bgp_source_id = django_filters.ModelMultipleChoiceFilter(
        field_name='bgp_source',
        queryset=BGPRouter.objects.all(),
        label=_('BGP Source (ID)'),
    )
    isis_source_id = django_filters.ModelMultipleChoiceFilter(
        field_name='isis_source',
        queryset=ISISInstance.objects.all(),
        label=_('IS-IS Source (ID)'),
    )
    metric_type = django_filters.MultipleChoiceFilter(
        choices=OSPFExternalMetricTypeChoices,
        label=_('Metric Type'),
    )
    ospf_match = django_filters.MultipleChoiceFilter(
        choices=OSPFRouteTypeChoices,
        method='filter_ospf_match',
        label=_('OSPF Route Types'),
    )

    class Meta:
        model = OSPFRedistribution
        fields = (
            'instance',
            'protocol',
            'metric',
            'metric_type',
            'subnets',
            'route_tag',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(instance__name__icontains=value) | Q(
            route_policy__icontains=value
        )
        return queryset.filter(qs_filter)

    def filter_ospf_match(self, queryset, name, value):
        return queryset.filter(ospf_match__overlap=value)


@register_filterset
class OSPFVirtualLinkFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    instance = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__name',
        queryset=OSPFInstance.objects.all(),
        to_field_name='name',
        label=_('Instance'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    transit_area_id = django_filters.ModelMultipleChoiceFilter(
        field_name='transit_area',
        queryset=OSPFArea.objects.all(),
        label=_('Transit Area (ID)'),
    )
    remote_router_id = MultiValueCharFilter(
        method='filter_rid',
        label=_('Remote Router ID'),
    )
    authentication = django_filters.MultipleChoiceFilter(
        choices=OSPFAuthenticationChoices,
        label=_('Authentication'),
    )
    message_digest_algorithm = django_filters.MultipleChoiceFilter(
        choices=OSPFMessageDigestAlgorithmChoices,
        label=_('Message Digest Algorithm'),
    )

    class Meta:
        model = OSPFVirtualLink
        fields = (
            'instance',
            'transit_area',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(instance__name__icontains=value)
            | Q(transit_area__area_id__icontains=value)
            | Q(remote_router_id__icontains=value)
        )
        return queryset.filter(qs_filter)

    def filter_rid(self, queryset, name, value):
        try:
            return queryset.filter(**{f'{name}__in': value})
        except ValidationError:
            return queryset.none()


@register_filterset
class OSPFSummaryAddressFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    instance = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__name',
        queryset=OSPFInstance.objects.all(),
        to_field_name='name',
        label=_('Instance'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    prefix = django_filters.CharFilter(method='filter_prefix', label=_('Prefix'))

    class Meta:
        model = OSPFSummaryAddress
        fields = ('instance', 'prefix', 'not_advertise', 'route_tag')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(instance__name__icontains=value) | Q(prefix__icontains=value)
        return queryset.filter(qs_filter)

    def filter_prefix(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            return queryset.filter(prefix=str(netaddr.IPNetwork(value).cidr))
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()


@register_filterset
class OSPFNeighborFilterSet(NetBoxModelFilterSet):
    ospf_interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface',
        queryset=OSPFInterface.objects.all(),
        label=_('OSPF Interface (ID)'),
    )
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='ospf_interface__interface__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    ip_address = MultiValueCharFilter(method='filter_ip_address', label=_('IP Address'))

    class Meta:
        model = OSPFNeighbor
        fields = ('ospf_interface', 'priority', 'poll_interval')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(ospf_interface__instance__name__icontains=value)
            | Q(ospf_interface__interface__name__icontains=value)
            | Q(ospf_interface__interface__device__name__icontains=value)
            | Q(ip_address__icontains=value)
        )
        return queryset.filter(qs_filter)

    def filter_ip_address(self, queryset, name, value):
        try:
            return queryset.filter(**{f'{name}__in': value})
        except ValidationError:
            return queryset.none()


@register_filterset
class OSPFAreaRangeFilterSet(NetBoxModelFilterSet):
    area_id = django_filters.ModelMultipleChoiceFilter(
        field_name='area',
        queryset=OSPFArea.objects.all(),
        label=_('Area (ID)'),
    )
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='area__instance',
        queryset=OSPFInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='area__instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    prefix = django_filters.CharFilter(method='filter_prefix', label=_('Prefix'))
    range_type = django_filters.MultipleChoiceFilter(
        choices=OSPFRangeTypeChoices,
        label=_('Range Type'),
    )

    class Meta:
        model = OSPFAreaRange
        fields = ('area', 'prefix', 'range_type', 'advertise')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(area__area_id__icontains=value)
            | Q(area__instance__name__icontains=value)
            | Q(prefix__icontains=value)
        )
        return queryset.filter(qs_filter)

    def filter_prefix(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            return queryset.filter(prefix=str(netaddr.IPNetwork(value).cidr))
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()
