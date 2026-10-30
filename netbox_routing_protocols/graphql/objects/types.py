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
    pattern: str


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
    route_policy_entries: list[
        Annotated[
            "RoutePolicyEntryType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]


@strawberry_django.type(
    models.RoutePolicyEntry,
    fields='__all__',
    filters=RoutePolicyEntryFilter,
    select_related=[
        'route_policy',
        'match_next_hop',
        'set_next_hop',
        'set_community_list',
    ],
    prefetch_related=[
        'match_prefix_list',
        'match_community_list',
        'match_aspath',
    ],
)
class RoutePolicyEntryType(PrimaryObjectType):
    route_policy: Annotated[
        "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    action: str
    sequence: BigInt
    implicit: bool
    jump_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    match_prefix_list: list[
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
    ]
    match_community_list: list[
        Annotated[
            "CommunityListType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]
    match_aspath: list[
        Annotated[
            "ASPathType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
    ]
    match_next_hop: (
        Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')] | None
    )
    match_metric: BigInt | None
    match_origin: str
    match_tag: BigInt | None
    match_weight: int | None
    set_local_preference: BigInt | None
    set_next_hop: (
        Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')] | None
    )
    set_aspath_prepend: list[BigInt]
    set_community_list: (
        Annotated[
            "CommunityListType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    set_community_mode: str
    set_metric: BigInt | None
    set_metric_mode: str
    set_origin: str
    set_tag: BigInt | None
    set_weight: int | None
