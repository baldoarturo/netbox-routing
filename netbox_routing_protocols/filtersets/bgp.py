import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import NetBoxModelFilterSet, PrimaryModelFilterSet
from dcim.models import Device
from ipam.models import ASN, VRF, IPAddress
from netbox_routing_protocols.models import ASPath, PrefixList, RoutePolicy
from tenancy.filtersets import TenancyFilterSet
from utilities.filtersets import register_filterset

from netbox_routing_protocols.choices.bgp import *
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPSettingFilterSet',
    'BGPRouterFilterSet',
    'BGPScopeFilterSet',
    'BGPAddressFamilyFilterSet',
    'BGPPeerFilterSet',
    'BGPPeerTemplateFilterSet',
    'BGPPolicyTemplateFilterSet',
    'BGPSessionTemplateFilterSet',
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


class RemoteASFilterSetMixin(django_filters.FilterSet):
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


@register_filterset
class BGPPeerTemplateFilterSet(
    RemoteASFilterSetMixin, TenancyFilterSet, PrimaryModelFilterSet
):
    peer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peers',
        queryset=BGPScope.objects.all(),
        label=_('Peer (ID)'),
    )
    address_family_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_families',
        queryset=BGPPeerAddressFamily.objects.all(),
        label=_('Address Family (ID)'),
    )

    class Meta:
        model = BGPPeerTemplate
        fields = (
            'peer_id',
            'address_family_id',
            'remote_as_id',
            'remote_as',
            'enabled',
            'tenant_group',
            'tenant',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPPolicyTemplateFilterSet(
    ASPathUsageFilterSetMixin,
    PolicyFilterSetMixin,
    TenancyFilterSet,
    PrimaryModelFilterSet,
):
    name = django_filters.CharFilter()
    enabled = django_filters.BooleanFilter()
    parent_id = django_filters.ModelMultipleChoiceFilter(
        field_name='parents',
        queryset=BGPPolicyTemplate.objects.all(),
        label=_('Parent (ID)'),
    )
    parent = django_filters.ModelMultipleChoiceFilter(
        field_name='parents__name',
        queryset=BGPPolicyTemplate.objects.all(),
        to_field_name='name',
        label=_('Parent (Name)'),
    )

    class Meta:
        model = BGPPolicyTemplate
        fields = (
            'name',
            'parent',
            'enabled',
            'prefixlist_in',
            'prefixlist_out',
            'routepolicy_in',
            'routepolicy_out',
            'tenant_group',
            'tenant',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPSessionTemplateFilterSet(
    RemoteASFilterSetMixin, TenancyFilterSet, PrimaryModelFilterSet
):

    class Meta:
        model = BGPSessionTemplate
        fields = ('name', 'remote_as_id', 'remote_as', 'tenant_group', 'tenant')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPSettingFilterSet(PrimaryModelFilterSet):
    key = django_filters.MultipleChoiceFilter(
        choices=BGPSettingChoices, null_value=None, label=_('Setting Name')
    )

    class Meta:
        model = BGPSetting
        fields = ('key',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(key__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPRouterFilterSet(TenancyFilterSet, PrimaryModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label=_('Device (ID)'),
    )
    device = django_filters.ModelMultipleChoiceFilter(
        field_name='device__name',
        queryset=Device.objects.all(),
        to_field_name='name',
        label=_('Device'),
    )
    asn_id = django_filters.ModelMultipleChoiceFilter(
        field_name='asn',
        queryset=ASN.objects.all(),
        label=_('AS Number (ID)'),
    )
    asn = django_filters.ModelMultipleChoiceFilter(
        field_name='asn__asn',
        queryset=ASN.objects.all(),
        to_field_name='asn',
        label=_('AS Number'),
    )

    class Meta:
        model = BGPRouter
        fields = ('device_id', 'device', 'asn_id', 'asn', 'tenant_group', 'tenant')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(device__name__icontains=value)
            | Q(asn__asn__icontains=value)
        )
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPScopeFilterSet(TenancyFilterSet, PrimaryModelFilterSet):
    router_id = django_filters.ModelMultipleChoiceFilter(
        field_name='router',
        queryset=BGPRouter.objects.all(),
        label=_('Router (ID)'),
    )
    vrf_id = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf',
        queryset=VRF.objects.all(),
        label=_('VRF (ID)'),
    )
    vrf = django_filters.ModelMultipleChoiceFilter(
        field_name='vrf__name',
        queryset=VRF.objects.all(),
        to_field_name='vrf',
        label=_('VRF'),
    )

    class Meta:
        model = BGPScope
        fields = ('router_id', 'vrf_id', 'vrf', 'tenant_group', 'tenant')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(router__device__name__icontains=value)
            | Q(router__asn__asn__icontains=value)
            | Q(vrf__name__icontains=value)
        )
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPAddressFamilyFilterSet(TenancyFilterSet, PrimaryModelFilterSet):
    scope_id = django_filters.ModelMultipleChoiceFilter(
        field_name='scope',
        queryset=Device.objects.all(),
        label=_('Router (ID)'),
    )
    address_family = django_filters.MultipleChoiceFilter(
        choices=BGPAddressFamilyChoices, null_value=None, label=_('Address Family')
    )

    class Meta:
        model = BGPAddressFamily
        fields = ('scope_id', 'address_family', 'tenant_group', 'tenant')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(address_family__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPPeerFilterSet(NetBoxModelFilterSet):
    scope_id = django_filters.ModelMultipleChoiceFilter(
        field_name='scope',
        queryset=BGPScope.objects.all(),
        label=_('Scope (ID)'),
    )
    peer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer',
        queryset=IPAddress.objects.all(),
        label=_('Peer (ID)'),
    )
    peer = django_filters.ModelMultipleChoiceFilter(
        field_name='peer__address',
        queryset=IPAddress.objects.all(),
        to_field_name='peer',
        label=_('Peer (Name)'),
    )
    peer_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer_group',
        queryset=BGPPeerTemplate.objects.all(),
        label=_('Peer Group (ID)'),
    )
    remote_as_id = django_filters.ModelMultipleChoiceFilter(
        field_name='remote_as',
        queryset=ASN.objects.all(),
        label=_('Remote AS (ID)'),
    )
    remote_as = django_filters.ModelMultipleChoiceFilter(
        field_name='remote_as__asn',
        queryset=ASN.objects.all(),
        to_field_name='remote_as',
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
        to_field_name='local_as',
        label=_('Local AS (ASN)'),
    )

    class Meta:
        model = BGPPeer
        fields = ('scope_id', 'peer_id', 'remote_as_id', 'local_as_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        qs_filter |= Q(peer__address__icontains=value)
        qs_filter |= Q(remote_as__asn__icontains=value)
        qs_filter |= Q(local_as__asn__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class BGPPeerAddressFamilyFilterSet(ASPathUsageFilterSetMixin, NetBoxModelFilterSet):
    peer_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer',
        queryset=BGPScope.objects.all(),
        label=_('Peer (ID)'),
    )
    peer_group_id = django_filters.ModelMultipleChoiceFilter(
        field_name='peer_group',
        queryset=BGPPeerTemplate.objects.all(),
        label=_('Peer Group (ID)'),
    )
    address_family_id = django_filters.ModelMultipleChoiceFilter(
        field_name='address_family',
        queryset=BGPAddressFamily.objects.all(),
        label=_('Address Family (ID)'),
    )

    class Meta:
        model = BGPPeerAddressFamily
        fields = (
            'peer_id',
            'peer_group_id',
            'address_family',
            'enabled',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(peer__address__icontains=value)
        qs_filter |= Q(remote_as__asn__icontains=value)
        qs_filter |= Q(local_as__asn__icontains=value)
        return queryset.filter(qs_filter).distinct()


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
