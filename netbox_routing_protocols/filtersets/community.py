import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from netbox.filtersets import PrimaryModelFilterSet
from netbox_routing_protocols.models import RoutePolicyEntry
from tenancy.filtersets import TenancyFilterSet
from ipam.models import Role

from utilities.filtersets import register_filterset

from netbox_routing_protocols.models.community import *

__all__ = (
    'CommunityFilterSet',
    'CommunityListFilterSet',
    'CommunityListEntryFilterSet',
)


@register_filterset
class CommunityFilterSet(TenancyFilterSet, PrimaryModelFilterSet):
    role_id = django_filters.ModelMultipleChoiceFilter(
        field_name='role',
        queryset=Role.objects.all(),
        label=_('Role (ID)'),
    )
    role = django_filters.ModelMultipleChoiceFilter(
        field_name='role__name',
        queryset=Role.objects.all(),
        to_field_name='name',
        label=_('Role (Name)'),
    )
    usable_in_list_id = django_filters.ModelChoiceFilter(
        queryset=CommunityList.objects.all(),
        method='filter_usable_in_list',
        label=_('Usable in the community list (ID)'),
    )

    class Meta:
        model = Community
        fields = (
            'name',
            'community',
            'type',
            'status',
            'description',
            'role_id',
            'role',
            'tenant_id',
            'tenant',
            'tenant_group_id',
            'tenant_group',
        )

    def filter_usable_in_list(self, queryset, name, value):
        """The communities a list accepts: the ones of its type"""
        return queryset.filter(type=value.type) if value else queryset

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value)
            | Q(community__icontains=value)
            | Q(description__icontains=value)
        )
        return queryset.filter(qs_filter)


@register_filterset
class CommunityListFilterSet(TenancyFilterSet, PrimaryModelFilterSet):
    community_id = django_filters.ModelMultipleChoiceFilter(
        field_name='communitylistentries__community',
        queryset=Community.objects.all(),
        label=_('Community (ID)'),
    )
    route_policy_entry_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_policy_entries',
        queryset=RoutePolicyEntry.objects.all(),
        label=_('Route Policy Entry (ID)'),
    )

    class Meta:
        model = CommunityList
        fields = (
            'name',
            'type',
            'description',
            'tenant_id',
            'tenant',
            'tenant_group_id',
            'tenant_group',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(name__icontains=value) | Q(description__icontains=value)
        return queryset.filter(qs_filter)


@register_filterset
class CommunityListEntryFilterSet(PrimaryModelFilterSet):
    community_list_id = django_filters.ModelMultipleChoiceFilter(
        field_name='community_list',
        queryset=CommunityList.objects.all(),
        label=_('Community List (ID)'),
    )
    community_list = django_filters.ModelMultipleChoiceFilter(
        field_name='community_list__name',
        queryset=CommunityList.objects.all(),
        to_field_name='name',
        label=_('Community List (Name)'),
    )
    community_id = django_filters.ModelMultipleChoiceFilter(
        field_name='community',
        queryset=Community.objects.all(),
        label=_('Community (ID)'),
    )
    community = django_filters.ModelMultipleChoiceFilter(
        field_name='community__community',
        queryset=Community.objects.all(),
        to_field_name='community',
        label=_('Community (Community)'),
    )

    class Meta:
        model = CommunityListEntry
        fields = (
            'sequence',
            'action',
            'description',
            'community_list_id',
            'community_list',
            'community_id',
            'community',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(community_list__name__icontains=value)
        qs_filter |= Q(community__community__icontains=value)
        qs_filter |= Q(description__icontains=value)
        return queryset.filter(qs_filter)
