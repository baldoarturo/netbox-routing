# SPDX-License-Identifier: Apache-2.0

import django_filters
import netaddr
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import MultiValueCharFilter
from utilities.filtersets import register_filterset

from netbox_routing_protocols.choices import (
    ISISAddressFamilyChoices,
    ISISAuthTypeChoices,
    ISISCircuitTypeChoices,
    ISISFastRerouteChoices,
    ISISFrrProtectionChoices,
    ISISMetricStyleChoices,
    ISISIsTypeChoices,
    ISISLevelScopeChoices,
    ISISNetworkTypeChoices,
    ISISRedistributionMetricTypeChoices,
    ISISRedistributionProtocolChoices,
    ISISSettingChoices,
)
from netbox_routing_protocols.constants.isis import ISISSETTING_ASSIGNMENT_MODELS
from netbox_routing_protocols.models import (
    BGPRouter,
    EIGRPRouter,
    OSPFInstance,
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISAreaAddress,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    'ISISInstanceFilterSet',
    'ISISInterfaceFilterSet',
    'ISISSettingFilterSet',
    'ISISLevelFilterSet',
    'ISISInterfaceLevelFilterSet',
    'ISISSegmentRoutingFilterSet',
    'ISISFlexAlgoFilterSet',
    'ISISPrefixSIDFilterSet',
    'ISISSRv6LocatorFilterSet',
    'ISISAreaAddressFilterSet',
    'ISISRedistributionFilterSet',
    'ISISSummaryAddressFilterSet',
    'ISISRouteLeakFilterSet',
)


@register_filterset
class ISISFlexAlgoFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label='Instance (ID)',
    )

    class Meta:
        model = ISISFlexAlgo
        fields = ('instance_id', 'algo_id', 'metric_type', 'priority')

    def search(self, queryset, name, value):
        return queryset


@register_filterset
class ISISPrefixSIDFilterSet(NetBoxModelFilterSet):
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='interface',
        queryset=ISISInterface.objects.all(),
        label='Interface (ID)',
    )

    class Meta:
        model = ISISPrefixSID
        fields = (
            'interface_id',
            'algorithm',
            'sid_index',
            'sid_label',
            'n_flag',
            'no_php',
            'explicit_null',
            'readvertise',
        )

    def search(self, queryset, name, value):
        return queryset


@register_filterset
class ISISSRv6LocatorFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label='Instance (ID)',
    )
    # prefix is an IPNetworkField; auto-generating a filter for it fails, so mirror
    # StaticRouteFilterSet's explicit CharFilter + CIDR-normalising method.
    prefix = django_filters.CharFilter(method='filter_prefix', label='Prefix')

    class Meta:
        model = ISISSRv6Locator
        fields = (
            'instance_id',
            'name',
            'prefix',
            'algorithm',
            'enabled',
            'is_anycast',
            'is_micro_segment',
            'isis_level',
        )

    def search(self, queryset, name, value):
        value = (value or '').strip()
        if not value:
            return queryset
        return queryset.filter(name__icontains=value)

    def filter_prefix(self, queryset, name, value):
        value = (value or '').strip()
        if not value:
            return queryset
        try:
            query = str(netaddr.IPNetwork(value).cidr)
            return queryset.filter(**{f'{name}': query})
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()


@register_filterset
class ISISSettingFilterSet(NetBoxModelFilterSet):
    key = django_filters.MultipleChoiceFilter(
        choices=ISISSettingChoices, null_value=None, label=_('Setting Name')
    )
    assigned_object_type = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.filter(ISISSETTING_ASSIGNMENT_MODELS),
        field_name='assigned_object_type',
        label=_('Assigned Object Type'),
    )
    assigned_object_id = MultiValueCharFilter(
        field_name='assigned_object_id',
        label=_('Assigned Object (ID)'),
    )

    class Meta:
        model = ISISSetting
        fields = ('key', 'assigned_object_type', 'assigned_object_id')

    def search(self, queryset, name, value):
        value = (value or '').strip()
        if not value:
            return queryset
        qs_filter = Q(key__icontains=value) | Q(value__icontains=value)
        return queryset.filter(qs_filter)


@register_filterset
class ISISLevelFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label='Instance (ID)',
    )

    class Meta:
        model = ISISLevel
        fields = (
            'instance_id',
            'level',
            'default_metric',
            'wide_metrics_only',
            'preference',
            'labeled_preference',
            'disabled',
            'auth_type',
        )

    def search(self, queryset, name, value):
        return queryset


@register_filterset
class ISISInterfaceLevelFilterSet(NetBoxModelFilterSet):
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='interface',
        queryset=ISISInterface.objects.all(),
        label='Interface (ID)',
    )

    class Meta:
        model = ISISInterfaceLevel
        fields = (
            'interface_id',
            'level',
            'metric',
            'hello_interval',
            'hello_multiplier',
            'priority',
            'passive',
        )

    def search(self, queryset, name, value):
        return queryset


@register_filterset
class ISISSegmentRoutingFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label='Instance (ID)',
    )

    class Meta:
        model = ISISSegmentRouting
        fields = (
            'instance_id',
            'enabled',
            'srv6_enabled',
            'prefix_sid_range',
            'srgb_start',
            'srgb_range',
            'srlb_start',
            'srlb_range',
            'maximum_sid_depth',
            'tunnel_table_pref',
        )

    def search(self, queryset, name, value):
        return queryset


@register_filterset
class ISISInstanceFilterSet(NetBoxModelFilterSet):
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
    import_policy_id = django_filters.ModelMultipleChoiceFilter(
        field_name='import_policy',
        queryset=RoutePolicy.objects.all(),
        label=_('Import Policy (ID)'),
    )
    import_policy = django_filters.ModelMultipleChoiceFilter(
        field_name='import_policy__name',
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        label=_('Import Policy (Name)'),
    )
    export_policy_id = django_filters.ModelMultipleChoiceFilter(
        field_name='export_policy',
        queryset=RoutePolicy.objects.all(),
        label=_('Export Policy (ID)'),
    )
    export_policy = django_filters.ModelMultipleChoiceFilter(
        field_name='export_policy__name',
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        label=_('Export Policy (Name)'),
    )

    process_tag = MultiValueCharFilter(label=_('Process Tag'))
    net = MultiValueCharFilter(label=_('NET'))
    is_type = django_filters.MultipleChoiceFilter(
        choices=ISISIsTypeChoices,
        label=_('IS Type'),
    )

    metric_style = django_filters.MultipleChoiceFilter(
        choices=ISISMetricStyleChoices,
        label=_('Metric Style'),
    )
    fast_reroute = django_filters.MultipleChoiceFilter(
        choices=ISISFastRerouteChoices,
        label=_('Fast Reroute'),
    )
    area_auth_type = django_filters.MultipleChoiceFilter(
        choices=ISISAuthTypeChoices,
        label=_('Area Auth Type'),
    )
    domain_auth_type = django_filters.MultipleChoiceFilter(
        choices=ISISAuthTypeChoices,
        label=_('Domain Auth Type'),
    )

    class Meta:
        model = ISISInstance
        fields = (
            'metric_style',
            'fast_reroute',
            'area_auth_type',
            'domain_auth_type',
            'overload_bit',
            'overload_on_startup',
            'suppress_attached_bit',
            'ignore_attached_bit',
            'te_enabled',
            'microloop_avoidance',
            'distance',
            'maximum_paths',
            'reference_bandwidth',
            'lsp_lifetime',
            'lsp_refresh_interval',
            'lsp_mtu',
            'device_id',
            'device',
            'vrf_id',
            'vrf',
            'process_tag',
            'net',
            'is_type',
            'import_policy_id',
            'import_policy',
            'export_policy_id',
            'export_policy',
        )

    def search(self, queryset, name, value):
        value = (value or '').strip()
        if not value:
            return queryset
        qs_filter = (
            Q(process_tag__icontains=value)
            | Q(device__name__icontains=value)
            | Q(net__icontains=value)
        )
        return queryset.filter(qs_filter)


@register_filterset
class ISISInterfaceFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label='Instance (ID)',
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
    address_family = django_filters.MultipleChoiceFilter(
        choices=ISISAddressFamilyChoices,
        label=_('Address Family'),
    )
    circuit_type = django_filters.MultipleChoiceFilter(
        choices=ISISCircuitTypeChoices,
        label=_('Circuit Type'),
    )
    network_type = django_filters.MultipleChoiceFilter(
        choices=ISISNetworkTypeChoices,
        label=_('Network Type'),
    )
    hello_auth_type = django_filters.MultipleChoiceFilter(
        choices=ISISAuthTypeChoices,
        label=_('Hello Auth Type'),
    )
    frr_protection = django_filters.MultipleChoiceFilter(
        choices=ISISFrrProtectionChoices,
        label=_('FRR Protection'),
    )

    class Meta:
        model = ISISInterface
        fields = (
            'bfd_enabled',
            'frr_enabled',
            'frr_protection',
            'mesh_group',
            'csnp_interval',
            'retransmit_interval',
            'lsp_interval',
            'instance_id',
            'vrf_id',
            'vrf',
            'device_id',
            'device',
            'interface_id',
            'interface',
            'address_family',
            'circuit_type',
            'network_type',
            'metric',
            'passive',
            'hello_auth_type',
        )

    def search(self, queryset, name, value):
        value = (value or '').strip()
        if not value:
            return queryset
        qs_filter = (
            Q(instance__process_tag__icontains=value)
            | Q(instance__net__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(interface__label__icontains=value)
            | Q(interface__device__name__icontains=value)
        )
        return queryset.filter(qs_filter)


@register_filterset
class ISISRedistributionFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    address_family = django_filters.MultipleChoiceFilter(
        choices=ISISAddressFamilyChoices,
        label=_('Address Family'),
    )
    protocol = django_filters.MultipleChoiceFilter(
        choices=ISISRedistributionProtocolChoices,
        label=_('Protocol'),
    )
    level = django_filters.MultipleChoiceFilter(
        choices=ISISLevelScopeChoices,
        label=_('Level'),
    )
    metric_type = django_filters.MultipleChoiceFilter(
        choices=ISISRedistributionMetricTypeChoices,
        label=_('Metric Type'),
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

    class Meta:
        model = ISISRedistribution
        fields = ('instance_id', 'metric', 'route_tag')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(route_policy__icontains=value)


@register_filterset
class ISISSummaryAddressFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    level = django_filters.MultipleChoiceFilter(
        choices=ISISLevelScopeChoices,
        label=_('Level'),
    )
    prefix = django_filters.CharFilter(method='filter_prefix', label=_('Prefix'))

    class Meta:
        model = ISISSummaryAddress
        fields = ('instance_id', 'prefix', 'not_advertise', 'metric', 'route_tag')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(prefix__icontains=value)

    def filter_prefix(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            return queryset.filter(prefix=str(netaddr.IPNetwork(value).cidr))
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()


@register_filterset
class ISISRouteLeakFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    address_family = django_filters.MultipleChoiceFilter(
        choices=ISISAddressFamilyChoices,
        label=_('Address Family'),
    )

    class Meta:
        model = ISISRouteLeak
        fields = ('instance_id',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(route_policy__icontains=value)


@register_filterset
class ISISAreaAddressFilterSet(NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=ISISInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )

    class Meta:
        model = ISISAreaAddress
        fields = ('instance_id', 'net')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(net__icontains=value)
