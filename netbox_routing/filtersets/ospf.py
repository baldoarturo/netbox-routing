import django_filters
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF, IPAddress
from utilities.filters import MultiValueCharFilter
from utilities.filtersets import register_filterset

from netbox.filtersets import NetBoxModelFilterSet
from netbox_routing.choices.ospf import (
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFNetworkTypeChoices,
)
from netbox_routing.models import OSPFArea, OSPFInstance, OSPFInterface, OSPFNetwork

__all__ = (
    'OSPFAreaFilterSet',
    'OSPFInstanceFilterSet',
    'OSPFInterfaceFilterSet',
    'OSPFNetworkFilterSet',
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
            'process_id',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
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
        fields = ('instance', 'area_id', 'area_type')

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
            'authentication',
            'passphrase',
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
