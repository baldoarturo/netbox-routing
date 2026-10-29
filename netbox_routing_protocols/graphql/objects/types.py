from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.scalars import BigInt
from netbox.graphql.types import PrimaryObjectType
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.objects.filters import *
from netbox_routing_protocols.graphql.community.types import *

__all__ = (
    'ASPathType',
    'ASPathEntryType',
    'PrefixListType',
    'PrefixListEntryType',
    'RoutePolicyType',
    'RoutePolicyEntryType',
)


@strawberry_django.type(models.ASPath, fields='__all__', filters=ASPathFilter)
class ASPathType(PrimaryObjectType):
    name: str


@strawberry_django.type(
    models.ASPathEntry,
    fields='__all__',
    filters=ASPathEntryFilter,
    select_related=[
        'aspath',
    ],
)
class ASPathEntryType(PrimaryObjectType):
    aspath: Annotated[
        "ASPathType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    action: str
    sequence: BigInt
    pattern: str | None


@strawberry_django.type(models.PrefixList, fields='__all__', filters=PrefixListFilter)
class PrefixListType(PrimaryObjectType):
    name: str


@strawberry_django.type(
    models.PrefixListEntry,
    fields='__all__',
    filters=PrefixListEntryFilter,
    select_related=[
        'prefix_list',
        'prefix',
    ],
)
class PrefixListEntryType(PrimaryObjectType):
    prefix_list: Annotated[
        "PrefixListType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    action: str
    sequence: BigInt
    prefix: Annotated["PrefixType", strawberry.lazy('ipam.graphql.types')] | None
    any_prefix: bool
    le: int | None
    ge: int | None


@strawberry_django.type(models.RoutePolicy, fields='__all__', filters=RoutePolicyFilter)
class RoutePolicyType(PrimaryObjectType):
    name: str


@strawberry_django.type(
    models.RoutePolicyEntry,
    fields='__all__',
    filters=RoutePolicyEntryFilter,
    select_related=[
        'route_policy',
    ],
)
class RoutePolicyEntryType(PrimaryObjectType):
    route_policy: Annotated[
        "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    action: str
    sequence: int
    match_prefix_list: (
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    match_community_list: (
        Annotated[
            "CommunityListType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    match_community: (
        Annotated[
            "CommunityType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    match_aspath: (
        Annotated[
            "ASPathType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
