from typing import Annotated

import strawberry
import strawberry_django
from strawberry import ID

from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_protocols import models

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
    pass


@strawberry_django.filter(models.ASPathEntry, lookups=True)
class ASPathEntryFilter(PrimaryModelFilter):
    aspath: (
        Annotated[
            'ASPathFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    aspath_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.PrefixList, lookups=True)
class PrefixListFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.PrefixListEntry, lookups=True)
class PrefixListEntryFilter(PrimaryModelFilter):
    prefix_list: (
        Annotated[
            'PrefixListFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    prefix_list_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.RoutePolicy, lookups=True)
class RoutePolicyFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.RoutePolicyEntry, lookups=True)
class RoutePolicyEntryFilter(PrimaryModelFilter):
    route_policy: (
        Annotated[
            'RoutePolicyFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    route_policy_id: ID | None = strawberry_django.filter_field()
