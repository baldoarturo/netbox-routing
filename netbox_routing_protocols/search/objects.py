from netbox.search import SearchIndex, register_search, ObjectFieldValue
from netbox_routing_protocols.models.objects import *


@register_search
class ASPathIndex(SearchIndex):
    model = ASPath
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('name',)


@register_search
class ASPathEntryIndex(SearchIndex):
    model = ASPathEntry
    fields = (
        ('aspath', 100),
        ('pattern', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = (
        'aspath',
        'pattern',
    )


@register_search
class PrefixListIndex(SearchIndex):
    model = PrefixList
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('name',)


@register_search
class PrefixListEntryIndex(SearchIndex):
    model = PrefixListEntry
    fields = (
        ('prefix_list', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = (
        'prefix_list',
        'prefix',
    )

    @classmethod
    def to_cache(cls, instance, custom_fields=None):
        values = super().to_cache(instance, custom_fields)
        if instance.prefix_id:
            type_ = cls.get_field_type(instance.prefix, 'prefix')
            value = cls.get_field_value(instance.prefix, 'prefix')
            values.append(ObjectFieldValue('prefix', type_, 100, value))

        return values


@register_search
class RoutePolicyIndex(SearchIndex):
    model = RoutePolicy
    fields = (
        ('name', 100),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('name',)


@register_search
class RoutePolicyEntryIndex(SearchIndex):
    model = RoutePolicyEntry
    fields = (
        ('route_policy', 100),
        ('match', 200),
        ('set', 300),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('route_policy',)
