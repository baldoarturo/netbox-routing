import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import NetBoxModelFilterSet
from dcim.models import Device
from ipam.models import ASN, VRF, IPAddress
from netbox_routing_protocols.models import ASPath, PrefixList, RoutePolicy
from tenancy.filtersets import TenancyFilterSet
from utilities.filtersets import register_filterset

from netbox_routing_protocols.choices.bgp import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceFilterSet',
    'BGPAddressFamilyFilterSet',
    'BGPPeerGroupFilterSet',
    'BGPPeerFilterSet',
    'BGPPeerAddressFamilyFilterSet',
    'BFDProfileFilterSet',
)


class ASPathUsageFilterSetMixin(django_filters.FilterSet):
    """The objects that use an AS-path through the route policy they apply, in or out"""

    aspath_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ASPath.objects.all(),
        method='filter_aspath',
        label=_('AS-Path used by a route policy (ID)'),
    )

    def filter_aspath(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(routepolicy_in__route_policy_entries__match_aspath__in=value)
            | Q(routepolicy_out__route_policy_entries__match_aspath__in=value)
        ).distinct()


class PolicyFilterSetMixin(django_filters.FilterSet):
    prefixlist_in_id = django_filters.ModelMultipleChoiceFilter(
        field_name='prefixlist_in_id',
        queryset=PrefixList.objects.all(),
        label=_('Incoming Prefix List (ID)'),
    )
    prefixlist_in = django_filters.ModelMultipleChoiceFilter(
        field_name='prefixlist_in_id__name',
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        label=_('Incoming Prefix List (Name)'),
    )
    prefixlist_out_id = django_filters.ModelMultipleChoiceFilter(
        field_name='prefixlist_out_id',
        queryset=PrefixList.objects.all(),
        label=_('Outgoing Prefix List (ID)'),
    )
    prefixlist_out = django_filters.ModelMultipleChoiceFilter(
        field_name='prefixlist_out_id__name',
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        label=_('Outgoing Prefix List (Name)'),
    )
    routepolicy_in_id = django_filters.ModelMultipleChoiceFilter(
        field_name='routepolicy_in_id',
        queryset=RoutePolicy.objects.all(),
        label=_('Incoming Route Policy (ID)'),
    )
    routepolicy_in = django_filters.ModelMultipleChoiceFilter(
        field_name='routepolicy_in_id__name',
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        label=_('Incoming Route Policy (Name)'),
    )
    routepolicy_out_id = django_filters.ModelMultipleChoiceFilter(
        field_name='routepolicy_out_id',
        queryset=RoutePolicy.objects.all(),
        label=_('Outgoing Route Policy (ID)'),
    )
    routepolicy_out = django_filters.ModelMultipleChoiceFilter(
        field_name='routepolicy_out_id__name',
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        label=_('Outgoing Route Policy (Name)'),
    )


class PeerConfigFilterSetMixin(django_filters.FilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=BGPInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    remote_as_id = django_filters.ModelMultipleChoiceFilter(
        field_name='remote_as',
        queryset=ASN.objects.all(),
        label=_('Remote AS (ID)'),
    )
    remote_as = django_filters.ModelMultipleChoiceFilter(
        field_name='remote_as__asn',
        queryset=ASN.objects.all(),
        to_field_name='asn',
        label=_('Remote AS (ASN)'),
    )
    local_as_id = django_filters.ModelMultipleChoiceFilter(
        field_name='local_as',
        queryset=ASN.objects.all(),
        label=_('Local AS (ID)'),
    )
    local_as = django_filters.ModelMultipleChoiceFilter(
        field_name='local_as__asn',
        queryset=ASN.objects.all(),
        to_field_name='asn',
        label=_('Local AS (ASN)'),
    )
    bfd_id = django_filters.ModelMultipleChoiceFilter(
        field_name='bfd',
        queryset=BFDProfile.objects.all(),
        label=_('BFD Profile (ID)'),
    )


@register_filterset
class BGPInstanceFilterSet(TenancyFilterSet, NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf',
        queryset=VRF.objects.all(),
        label=_('VRF (ID)'),
    )
    asn_id = django_filters.ModelMultipleChoiceFilter(
        field_name='asn',
        queryset=ASN.objects.all(),
        label=_('ASN (ID)'),
    )
    asn = django_filters.ModelMultipleChoiceFilter(
        field_name='asn__asn',
        queryset=ASN.objects.all(),
        to_field_name='asn',
        label=_('ASN'),
    )

    class Meta:
        model = BGPInstance
        fields = ('id', 'name', 'router_id', 'asdot', 'graceful_restart', 'description')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(device__name__icontains=value)
            | Q(vrf__name__icontains=value)
            | Q(asn__asn__icontains=value)
            | Q(description__icontains=value)
        )


@register_filterset
class BGPAddressFamilyFilterSet(TenancyFilterSet, NetBoxModelFilterSet):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance',
        queryset=BGPInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='instance__vrf',
        queryset=VRF.objects.all(),
        label=_('VRF (ID)'),
    )
    address_family = django_filters.MultipleChoiceFilter(
        choices=BGPAddressFamilyChoices
    )

    class Meta:
        model = BGPAddressFamily
        fields = (
            'id',
            'maximum_paths',
            'default_originate',
            'auto_summary',
            'additional_paths_send',
            'additional_paths_receive',
            'additional_paths_install',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(instance__name__icontains=value)
            | Q(instance__device__name__icontains=value)
            | Q(address_family__icontains=value)
            | Q(description__icontains=value)
        )


@register_filterset
class BGPPeerGroupFilterSet(
    PeerConfigFilterSetMixin, TenancyFilterSet, NetBoxModelFilterSet
):
    class Meta:
        model = BGPPeerGroup
        fields = (
            'id',
            'name',
            'enabled',
            'ttl',
            'keepalive',
            'hold_time',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(instance__name__icontains=value)
            | Q(remote_as__asn__icontains=value)
            | Q(description__icontains=value)
        )


@register_filterset
class BGPPeerFilterSet(
    PeerConfigFilterSetMixin, TenancyFilterSet, NetBoxModelFilterSet
):
    peer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer',
        queryset=IPAddress.objects.all(),
        label=_('Peer (ID)'),
    )
    peer_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer_group',
        queryset=BGPPeerGroup.objects.all(),
        label=_('Peer Group (ID)'),
    )
    status = django_filters.MultipleChoiceFilter(choices=BGPStatusChoices)

    class Meta:
        model = BGPPeer
        fields = (
            'id',
            'name',
            'enabled',
            'ttl',
            'keepalive',
            'hold_time',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(peer__address__icontains=value)
            | Q(peer_group__name__icontains=value)
            | Q(remote_as__asn__icontains=value)
            | Q(local_as__asn__icontains=value)
            | Q(description__icontains=value)
        ).distinct()


@register_filterset
class BGPPeerAddressFamilyFilterSet(
    ASPathUsageFilterSetMixin,
    PolicyFilterSetMixin,
    TenancyFilterSet,
    NetBoxModelFilterSet,
):
    instance_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_family__instance',
        queryset=BGPInstance.objects.all(),
        label=_('Instance (ID)'),
    )
    peer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer',
        queryset=BGPPeer.objects.all(),
        label=_('Peer (ID)'),
    )
    peer_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer_group',
        queryset=BGPPeerGroup.objects.all(),
        label=_('Peer Group (ID)'),
    )
    address_family_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_family',
        queryset=BGPAddressFamily.objects.all(),
        label=_('Address Family (ID)'),
    )

    class Meta:
        model = BGPPeerAddressFamily
        fields = ('id', 'enabled', 'description')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(peer__peer__address__icontains=value)
            | Q(peer__name__icontains=value)
            | Q(peer_group__name__icontains=value)
            | Q(address_family__address_family__icontains=value)
            | Q(description__icontains=value)
        ).distinct()


@register_filterset
class BFDProfileFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = BFDProfile
        fields = ('name',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter).distinct()
