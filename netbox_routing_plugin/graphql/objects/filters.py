from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django
from strawberry import ID
from strawberry_django import StrFilterLookup

from netbox.graphql.filter_lookups import BigIntegerLookup, IntegerLookup
from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_plugin import models

if TYPE_CHECKING:
    from netbox_routing_plugin.graphql.community.filters import (
        CommunityListFilter,
    )

__all__ = (
    'ASPathFilter',
    'ASPathEntryFilter',
    'RoutePolicyFilter',
    'RoutePolicyEntryFilter',
    'PrefixListFilter',
    'PrefixListEntryFilter',
)


@strawberry_django.filter(models.ASPath, lookups=True)
class ASPathFilter(PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.ASPathEntry, lookups=True)
class ASPathEntryFilter(PrimaryModelFilter):
    aspath: (
        Annotated[
            'ASPathFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    aspath_id: ID | None = strawberry_django.filter_field()
    sequence: BigIntegerLookup | None = strawberry_django.filter_field()
    action: StrFilterLookup | None = strawberry_django.filter_field()
    pattern: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.PrefixList, lookups=True)
class PrefixListFilter(PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.PrefixListEntry, lookups=True)
class PrefixListEntryFilter(PrimaryModelFilter):
    prefix_list: (
        Annotated[
            'PrefixListFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    prefix_list_id: ID | None = strawberry_django.filter_field()
    sequence: BigIntegerLookup | None = strawberry_django.filter_field()
    action: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.RoutePolicy, lookups=True)
class RoutePolicyFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.RoutePolicyEntry, lookups=True)
class RoutePolicyEntryFilter(PrimaryModelFilter):
    route_policy: (
        Annotated[
            'RoutePolicyFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    route_policy_id: ID | None = strawberry_django.filter_field()
    sequence: BigIntegerLookup | None = strawberry_django.filter_field()
    action: StrFilterLookup | None = strawberry_django.filter_field()
    implicit: bool | None = strawberry_django.filter_field()
    jump_policy_id: ID | None = strawberry_django.filter_field()
    match_prefix_list: (
        Annotated[
            'PrefixListFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    match_community_list: (
        Annotated[
            'CommunityListFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    match_aspath: (
        Annotated[
            'ASPathFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    match_metric: BigIntegerLookup | None = strawberry_django.filter_field()
    match_tag: BigIntegerLookup | None = strawberry_django.filter_field()
    set_local_preference: BigIntegerLookup | None = strawberry_django.filter_field()
    set_metric: BigIntegerLookup | None = strawberry_django.filter_field()
    set_tag: BigIntegerLookup | None = strawberry_django.filter_field()
    match_weight: IntegerLookup | None = strawberry_django.filter_field()
    set_weight: IntegerLookup | None = strawberry_django.filter_field()
    match_origin: StrFilterLookup | None = strawberry_django.filter_field()
    set_origin: StrFilterLookup | None = strawberry_django.filter_field()
    set_community_mode: StrFilterLookup | None = strawberry_django.filter_field()
    set_metric_mode: StrFilterLookup | None = strawberry_django.filter_field()
