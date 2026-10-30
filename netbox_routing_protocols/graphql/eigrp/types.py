from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.eigrp.filters import (
    EIGRPRouterFilter,
    EIGRPAddressFamilyFilter,
    EIGRPNetworkFilter,
    EIGRPInterfaceFilter,
)

__all__ = (
    'EIGRPRouterType',
    'EIGRPAddressFamilyType',
    'EIGRPNetworkType',
    'EIGRPInterfaceType',
)


@strawberry_django.type(models.EIGRPRouter, fields='__all__', filters=EIGRPRouterFilter)
class EIGRPRouterType(PrimaryObjectType):
    device: Annotated["DeviceType", strawberry.lazy('dcim.graphql.types')]
    import_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    export_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    rid: str
    type: str
    name: str
    pid: str


@strawberry_django.type(
    models.EIGRPAddressFamily, fields='__all__', filters=EIGRPAddressFamilyFilter
)
class EIGRPAddressFamilyType(PrimaryObjectType):
    router: Annotated[
        "EIGRPRouterType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    rid: str


@strawberry_django.type(
    models.EIGRPNetwork, fields='__all__', filters=EIGRPNetworkFilter
)
class EIGRPNetworkType(PrimaryObjectType):
    router: Annotated[
        "EIGRPRouterType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    address_family: (
        Annotated[
            "EIGRPAddressFamilyType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    network: Annotated["PrefixType", strawberry.lazy('ipam.graphql.types')]


@strawberry_django.type(
    models.EIGRPInterface, fields='__all__', filters=EIGRPInterfaceFilter
)
class EIGRPInterfaceType(PrimaryObjectType):
    router: Annotated[
        "EIGRPRouterType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    address_family: (
        Annotated[
            "EIGRPAddressFamilyType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    interface: Annotated["InterfaceType", strawberry.lazy('dcim.graphql.types')]
    passive: str | None
    bfd: bool | None
    authentication: str | None
    passphrase: str | None
