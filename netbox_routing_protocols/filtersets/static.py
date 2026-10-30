import django_filters
import netaddr
from django.db.models import Exists, OuterRef, Q

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import MultiValueNumberFilter
from utilities.filtersets import register_filterset

from netbox_routing_protocols.choices import StaticRouteNextHopTypeChoices
from netbox_routing_protocols.models import StaticRoute


@register_filterset
class StaticRouteFilterSet(NetBoxModelFilterSet):
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='devices__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device (name)',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='devices',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    vrf = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf__name',
        queryset=VRF.objects.all(),
        to_field_name='name',
        label='VRF (name)',
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf',
        queryset=VRF.objects.all(),
        label='VRF (ID)',
    )

    prefix = django_filters.CharFilter(
        method='filter_prefix',
        label='Prefix',
    )

    next_hop = django_filters.CharFilter(
        method='filter_address',
        label='Next Hop',
    )

    interface = django_filters.ModelMultipleChoiceFilter(
        field_name='interface__name',
        queryset=Interface.objects.all(),
        to_field_name='name',
        label='Interface next hop (name)',
    )
    interface_id = django_filters.ModelMultipleChoiceFilter(
        field_name='interface',
        queryset=Interface.objects.all(),
        label='Interface next hop (ID)',
    )
    next_hop_type = django_filters.MultipleChoiceFilter(
        choices=StaticRouteNextHopTypeChoices,
        label='Next hop type',
    )
    next_hop_vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='next_hop_vrf',
        queryset=VRF.objects.all(),
        label='Next hop VRF (ID)',
    )
    route_tag = MultiValueNumberFilter(
        field_name='tag',
        label='Route tag',
    )
    family = django_filters.NumberFilter(
        field_name='prefix',
        lookup_expr='family',
        label='Address family (4 or 6)',
    )
    within = django_filters.CharFilter(
        method='filter_prefix_lookup',
        label='Prefix within (excluding the prefix itself)',
    )
    within_include = django_filters.CharFilter(
        method='filter_prefix_lookup',
        label='Prefix within (including the prefix itself)',
    )
    contains = django_filters.CharFilter(
        method='filter_prefix_lookup',
        label='Prefix that contains this one (or equal)',
    )

    class Meta:
        model = StaticRoute
        fields = (
            'name',
            'devices',
            'device',
            'device_id',
            'vrf',
            'vrf_id',
            'prefix',
            'distance',
            'next_hop',
            'interface',
            'interface_id',
            'next_hop_type',
            'next_hop_vrf_id',
            'next_hop_global',
            'route_tag',
            'permanent',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Exists(
                Device.objects.filter(
                    static_routes=OuterRef('pk'), name__icontains=value
                )
            )
            | Q(vrf__name__icontains=value)
            | Q(vrf__rd__icontains=value)
            | Q(prefix__icontains=value)
            | Q(next_hop__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(name__icontains=value)
            | Q(description__icontains=value)
        )
        return queryset.filter(qs_filter)

    def filter_prefix(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            query = str(netaddr.IPNetwork(value).cidr)
            return queryset.filter(**{f'{name}': query})
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()

    def filter_prefix_lookup(self, queryset, name, value):
        lookup = {
            'within': 'net_contained',
            'within_include': 'net_contained_or_equal',
            'contains': 'net_contains_or_equals',
        }[name]
        if not value.strip():
            return queryset
        try:
            query = str(netaddr.IPNetwork(value).cidr)
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()
        return queryset.filter(**{f'prefix__{lookup}': query})

    def filter_address(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            query = netaddr.IPAddress(value)
            return queryset.filter(**{f'{name}': query})
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()
