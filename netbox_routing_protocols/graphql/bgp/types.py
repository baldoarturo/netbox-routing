from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType

from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.bgp.filters import (
    BGPInstanceFilter,
    BGPAddressFamilyFilter,
    BGPPeerGroupFilter,
    BGPPeerFilter,
    BGPPeerAddressFamilyFilter,
    BFDProfileFilter,
)

__all__ = (
    'BGPInstanceType',
    'BGPAddressFamilyType',
    'BGPPeerGroupType',
    'BGPPeerType',
    'BGPPeerAddressFamilyType',
    'BFDProfileType',
)


@strawberry_django.type(models.BGPInstance, fields='__all__', filters=BGPInstanceFilter)
class BGPInstanceType(PrimaryObjectType):
    name: str
    device: Annotated["DeviceType", strawberry.lazy('dcim.graphql.types')]
    vrf: Annotated["VRFType", strawberry.lazy('ipam.graphql.types')] | None
    asn: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')]
    router_id: str | None
    asdot: bool | None
    graceful_restart: bool | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    address_families: list[
        Annotated[
            "BGPAddressFamilyType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]
    peer_groups: list[
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]
    peers: list[
        Annotated[
            "BGPPeerType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
    ]


@strawberry_django.type(
    models.BGPAddressFamily, fields='__all__', filters=BGPAddressFamilyFilter
)
class BGPAddressFamilyType(PrimaryObjectType):
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    address_family: str
    maximum_paths: int | None
    default_metric: int | None
    default_originate: bool | None
    auto_summary: bool | None
    distance_ebgp: int | None
    distance_ibgp: int | None
    additional_paths_send: bool | None
    additional_paths_receive: bool | None
    additional_paths_install: bool | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(
    models.BGPPeerGroup, fields='__all__', filters=BGPPeerGroupFilter
)
class BGPPeerGroupType(PrimaryObjectType):
    name: str
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    remote_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    local_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    enabled: bool | None
    bfd: (
        Annotated[
            "BFDProfileType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    ttl: int | None
    password: str | None
    keepalive: int | None
    hold_time: int | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    peers: list[
        Annotated[
            "BGPPeerType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
    ]
    address_families: list[
        Annotated[
            "BGPPeerAddressFamilyType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]


@strawberry_django.type(models.BGPPeer, fields='__all__', filters=BGPPeerFilter)
class BGPPeerType(PrimaryObjectType):
    name: str | None
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    peer: Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')]
    source: Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')] | None
    peer_group: (
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    status: str | None
    remote_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    local_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    enabled: bool | None
    bfd: (
        Annotated[
            "BFDProfileType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    ttl: int | None
    password: str | None
    keepalive: int | None
    hold_time: int | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    address_families: list[
        Annotated[
            "BGPPeerAddressFamilyType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
    ]


@strawberry_django.type(
    models.BGPPeerAddressFamily, fields='__all__', filters=BGPPeerAddressFamilyFilter
)
class BGPPeerAddressFamilyType(PrimaryObjectType):
    peer: (
        Annotated[
            "BGPPeerType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    peer_group: (
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    address_family: Annotated[
        "BGPAddressFamilyType",
        strawberry.lazy('netbox_routing_protocols.graphql.types'),
    ]
    enabled: bool | None
    prefixlist_in: (
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    prefixlist_out: (
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    routepolicy_in: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    routepolicy_out: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(models.BFDProfile, fields='__all__', filters=BFDProfileFilter)
class BFDProfileType(PrimaryObjectType):
    name: str
    min_tx_int: int
    min_rx_int: int
    multiplier: int
    hold: int | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
