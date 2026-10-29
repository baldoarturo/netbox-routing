import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filtersets import register_filterset

from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.models.community import *

__all__ = (
    'PrefixListFilterSet',
    'PrefixListEntryFilterSet',
    'RoutePolicyFilterSet',
    'RoutePolicyEntryFilterSet',
    'ASPathFilterSet',
    'ASPathEntryFilterSet',
)


@register_filterset
class ASPathFilterSet(NetBoxModelFilterSet):
    route_policy_entry_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy_entries',
        queryset=RoutePolicyEntry.objects.all(),
        label=_('Route Policy Entry (ID)'),
    )

    class Meta:
        model = ASPath
        fields = ('name', 'description')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(description__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class ASPathEntryFilterSet(NetBoxModelFilterSet):
    aspath_id = django_filters.ModelMultipleChoiceFilter(
        field_name='aspath',
        queryset=ASPath.objects.all(),
        label=_('AS-Path (ID)'),
    )
    aspath = django_filters.ModelMultipleChoiceFilter(
        field_name='aspath__name',
        queryset=ASPath.objects.all(),
        to_field_name='name',
        label=_('AS-Path (Name)'),
    )

    class Meta:
        model = ASPathEntry
        fields = (
            'aspath_id',
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(aspath__name__icontains=value)
            | Q(pattern__icontains=value)
            | Q(description__icontains=value)
            | Q(action=value)
        )
        return queryset.filter(qs_filter).distinct()


@register_filterset
class PrefixListFilterSet(NetBoxModelFilterSet):
    route_policy_entry_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy_entries',
        queryset=RoutePolicyEntry.objects.all(),
        label=_('Route Policy Entry (ID)'),
    )

    class Meta:
        model = PrefixList
        fields = ('name', 'family')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(description__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class PrefixListEntryFilterSet(NetBoxModelFilterSet):
    prefix_list_id = django_filters.ModelMultipleChoiceFilter(
        field_name='prefix_list',
        queryset=PrefixList.objects.all(),
        label=_('Prefix List (ID)'),
    )
    prefix_list = django_filters.ModelMultipleChoiceFilter(
        field_name='prefix_list__name',
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        label=_('Prefix List (Name)'),
    )
    prefix_id = django_filters.ModelMultipleChoiceFilter(
        field_name='prefix',
        queryset=Prefix.objects.all(),
        label=_('Prefix (ID)'),
    )
    prefix = django_filters.ModelMultipleChoiceFilter(
        field_name='prefix__prefix',
        queryset=Prefix.objects.all(),
        to_field_name='prefix',
        label=_('Prefix (Name)'),
    )
    family = django_filters.NumberFilter(
        field_name='prefix_list__family',
        label=_('Address family'),
    )

    class Meta:
        model = PrefixListEntry
        fields = (
            'prefix_list_id',
            'prefix_list',
            'prefix_id',
            'prefix',
            'any_prefix',
            'sequence',
            'action',
            'le',
            'ge',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(prefix_list__name__icontains=value)
        qs_filter |= Q(prefix__prefix__icontains=value)
        qs_filter |= Q(description__icontains=value)

        return queryset.filter(qs_filter)


@register_filterset
class RoutePolicyFilterSet(NetBoxModelFilterSet):
    match_aspath_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy_entries__match_aspath',
        queryset=ASPath.objects.all(),
        distinct=True,
        label=_('Matches AS-Path (ID)'),
    )

    class Meta:
        model = RoutePolicy
        fields = ()

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value)
        return queryset.filter(qs_filter).distinct()


@register_filterset
class RoutePolicyEntryFilterSet(NetBoxModelFilterSet):
    route_policy_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy',
        queryset=RoutePolicy.objects.all(),
        label=_('Route Policy (ID)'),
    )
    route_policy = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy__name',
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        label=_('Route Policy (Name)'),
    )
    match_prefix_list_id = django_filters.ModelMultipleChoiceFilter(
        field_name='match_prefix_list',
        queryset=PrefixList.objects.all(),
        label=_('Prefix List (ID)'),
    )
    match_prefix_list = django_filters.ModelMultipleChoiceFilter(
        field_name='match_prefix_list__name',
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        label=_('Prefix List (Name)'),
    )
    match_community_list_id = django_filters.ModelMultipleChoiceFilter(
        field_name='match_community_list',
        queryset=CommunityList.objects.all(),
        label=_('Community List (ID)'),
    )
    match_community_list = django_filters.ModelMultipleChoiceFilter(
        field_name='match_community_list__name',
        queryset=CommunityList.objects.all(),
        to_field_name='name',
        label=_('Community List (Name)'),
    )
    match_community_id = django_filters.ModelMultipleChoiceFilter(
        field_name='match_community',
        queryset=Community.objects.all(),
        label=_('Community (ID)'),
    )
    match_community = django_filters.ModelMultipleChoiceFilter(
        field_name='match_community__community',
        queryset=Community.objects.all(),
        to_field_name='community',
        label=_('Community (Community)'),
    )
    match_aspath_id = django_filters.ModelMultipleChoiceFilter(
        field_name='match_aspath',
        queryset=ASPath.objects.all(),
        label=_('AS Path List (ID)'),
    )
    match_aspath = django_filters.ModelMultipleChoiceFilter(
        field_name='match_aspath__name',
        queryset=ASPath.objects.all(),
        to_field_name='name',
        label=_('AS Path List (Name)'),
    )

    class Meta:
        model = RoutePolicyEntry
        fields = (
            'route_policy_id',
            'route_policy',
            'sequence',
            'action',
            'match_prefix_list_id',
            'match_prefix_list',
            'match_community_list_id',
            'match_community_list',
            'match_community_id',
            'match_community',
            'match_aspath_id',
            'match_aspath',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(route_policy__name__icontains=value)
        qs_filter |= Q(match__icontains=value)
        qs_filter |= Q(set__icontains=value)
        return queryset.filter(qs_filter).distinct()
