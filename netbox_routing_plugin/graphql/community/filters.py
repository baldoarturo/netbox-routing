from typing import Annotated

import strawberry
import strawberry_django
from strawberry import ID
from strawberry_django import StrFilterLookup

from ipam.graphql.filters import RoleFilter
from netbox.graphql.filter_lookups import BigIntegerLookup
from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_plugin import models
from tenancy.graphql.filter_mixins import TenancyFilterMixin

__all__ = (
    'CommunityFilter',
    'CommunityListFilter',
    'CommunityListEntryFilter',
)


@strawberry_django.filter(models.Community, lookups=True)
class CommunityFilter(TenancyFilterMixin, PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    community: StrFilterLookup | None = strawberry_django.filter_field()
    type: StrFilterLookup | None = strawberry_django.filter_field()
    status: StrFilterLookup | None = strawberry_django.filter_field()
    role: (
        Annotated[
            'RoleFilter',
            strawberry.lazy('ipam.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    role_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.CommunityList, lookups=True)
class CommunityListFilter(TenancyFilterMixin, PrimaryModelFilter):
    name: StrFilterLookup | None = strawberry_django.filter_field()
    type: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.CommunityListEntry, lookups=True)
class CommunityListEntryFilter(PrimaryModelFilter):
    sequence: BigIntegerLookup | None = strawberry_django.filter_field()
    action: StrFilterLookup | None = strawberry_django.filter_field()
    community_list: (
        Annotated[
            'CommunityListFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    community_list_id: ID | None = strawberry_django.filter_field()

    community: (
        Annotated[
            'CommunityFilter',
            strawberry.lazy('netbox_routing_plugin.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    community_id: ID | None = strawberry_django.filter_field()
