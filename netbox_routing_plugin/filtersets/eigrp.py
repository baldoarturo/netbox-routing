import django_filters
import netaddr

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import Prefix
from utilities.filters import MultiValueCharFilter
from utilities.filtersets import register_filterset

from netbox.filtersets import NetBoxModelFilterSet
from netbox_routing_plugin.models import (
    EIGRPAddressFamily,
    EIGRPRouter,
    EIGRPNetwork,
    EIGRPInterface,
)
from netbox_routing_plugin.models.objects import RoutePolicy

__all__ = (
    'EIGRPRouterFilterSet',
    'EIGRPAddressFamilyFilterSet',
    'EIGRPNetworkFilterSet',
    'EIGRPInterfaceFilterSet',
)


class RouterMixin:

    def filter_rid(self, queryset, name, value):
        try:
            return queryset.filter(**{f'{name}__in': value})
        except ValidationError:
            return queryset.none()


@register_filterset
class EIGRPRouterFilterSet(RouterMixin, NetBoxModelFilterSet):
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

    rid = MultiValueCharFilter(
        method='filter_rid',
        label=_('Router ID'),
    )

    class Meta:
        model = EIGRPRouter
        fields = (
            'device_id',
            'device',
            'mode',
            'rid',
            'import_policy_id',
            'import_policy',
            'export_policy_id',
            'export_policy',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q()
        qs_filter |= Q(name__icontains=value)
        qs_filter |= Q(device__name__icontains=value)
        qs_filter |= Q(rid__icontains=value)

        return queryset.filter(qs_filter).distinct()


@register_filterset
class EIGRPAddressFamilyFilterSet(RouterMixin, NetBoxModelFilterSet):
    router_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router',
        queryset=EIGRPRouter.objects.all(),
        label='Router (ID)',
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name='router__name',
        queryset=EIGRPRouter.objects.all(),
        to_field_name='name',
        label='Router (Name)',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router__device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='router__device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device',
    )
    rid = MultiValueCharFilter(
        method='filter_rid',
        label=_('Router ID'),
    )

    class Meta:
        model = EIGRPAddressFamily
        fields = (
            'router_id',
            'router',
            'device_id',
            'device',
            'rid',
            'family',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(Q(rid__icontains=value))
        qs_filter |= Q(router__name__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class EIGRPNetworkFilterSet(NetBoxModelFilterSet):
    router_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router',
        queryset=EIGRPRouter.objects.all(),
        label='Router (ID)',
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name='router__name',
        queryset=EIGRPRouter.objects.all(),
        to_field_name='name',
        label='Router (Name)',
    )
    address_family_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_family',
        queryset=EIGRPAddressFamily.objects.all(),
        label='Address Family (ID)',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router__device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='router__device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label='Device',
    )
    network_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network',
        queryset=Prefix.objects.all(),
        label='Network (ID)',
    )
    network = django_filters.CharFilter(
        method='filter_prefix',
        label=_('Network'),
    )

    class Meta:
        model = EIGRPNetwork
        fields = (
            'router_id',
            'router',
            'address_family_id',
            'address_family',
            'device_id',
            'device',
            'network_id',
            'network',
        )

    def filter_prefix(self, queryset, name, value):
        if not value.strip():
            return queryset
        try:
            query = str(netaddr.IPNetwork(value).cidr)
            return queryset.filter(prefix=query)
        except (netaddr.AddrFormatError, ValueError):
            return queryset.none()

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(
            Q(router__name__icontains=value) | Q(address_family__rid__icontains=value)
        )
        qs_filter |= Q(network__prefix__contains=value.strip())
        try:
            prefix = str(netaddr.IPNetwork(value.strip()).cidr)
            qs_filter |= Q(network__prefix__net_contains_or_equals=prefix)
        except (netaddr.AddrFormatError, ValueError):
            pass
        return queryset.filter(qs_filter).distinct()


@register_filterset
class EIGRPInterfaceFilterSet(NetBoxModelFilterSet):
    router_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router',
        queryset=EIGRPRouter.objects.all(),
        label='Router (ID)',
    )
    router = django_filters.ModelMultipleChoiceFilter(
        field_name='router__name',
        queryset=EIGRPRouter.objects.all(),
        to_field_name='name',
        label='Router (Name)',
    )
    address_family_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_family',
        queryset=EIGRPAddressFamily.objects.all(),
        label='Address Family (ID)',
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

    class Meta:
        model = EIGRPInterface
        fields = (
            'router_id',
            'router',
            'address_family_id',
            'address_family',
            'device_id',
            'device',
            'interface_id',
            'interface',
            'bfd',
            'passive',
            'authentication',
            'passphrase',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(router__name__icontains=value)
            | Q(router__device__name__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(interface__label__icontains=value)
            | Q(interface__device__name__icontains=value)
        )
        return queryset.filter(qs_filter).distinct()
