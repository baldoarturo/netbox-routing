from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.ospf.filters import (
    OSPFInstanceFilter,
    OSPFAreaFilter,
    OSPFInterfaceFilter,
    OSPFNetworkFilter,
    OSPFRedistributionFilter,
    OSPFVirtualLinkFilter,
    OSPFSummaryAddressFilter,
    OSPFNeighborFilter,
    OSPFAreaRangeFilter,
)

__all__ = (
    'OSPFInstanceType',
    'OSPFAreaType',
    'OSPFInterfaceType',
    'OSPFNetworkType',
    'OSPFRedistributionType',
    'OSPFVirtualLinkType',
    'OSPFSummaryAddressType',
    'OSPFNeighborType',
    'OSPFAreaRangeType',
)


@strawberry_django.type(
    models.OSPFInstance, fields='__all__', filters=OSPFInstanceFilter
)
class OSPFInstanceType(PrimaryObjectType):
    name: str
    device: Annotated["DeviceType", strawberry.lazy('dcim.graphql.types')]
    vrf: Annotated["VRFType", strawberry.lazy('ipam.graphql.types')] | None
    router_id: str
    default_originate: bool
    default_originate_always: bool
    default_originate_metric: int | None
    default_originate_metric_type: str


@strawberry_django.type(models.OSPFArea, fields='__all__', filters=OSPFAreaFilter)
class OSPFAreaType(PrimaryObjectType):
    instance: Annotated[
        "OSPFInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    area_id: str
    area_type: str
    default_cost: int | None
    nssa_translate_always: bool
    nssa_no_redistribution: bool
    nssa_default_originate: bool


@strawberry_django.type(
    models.OSPFInterface, fields='__all__', filters=OSPFInterfaceFilter
)
class OSPFInterfaceType(PrimaryObjectType):
    instance: Annotated[
        "OSPFInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    area: Annotated[
        "OSPFAreaType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    interface: Annotated["InterfaceType", strawberry.lazy('dcim.graphql.types')]
    network_type: str | None
    passive: bool | None
    priority: str | None
    cost: int | None
    hello_interval: int
    dead_interval: int
    retransmit_interval: int
    transmit_delay: int
    bfd: bool | None
    mtu_ignore: bool
    authentication: str | None
    passphrase: str | None


@strawberry_django.type(models.OSPFNetwork, fields='__all__', filters=OSPFNetworkFilter)
class OSPFNetworkType(PrimaryObjectType):
    ospf_interface: Annotated[
        "OSPFInterfaceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    ip_address: Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')]


@strawberry_django.type(
    models.OSPFRedistribution, fields='__all__', filters=OSPFRedistributionFilter
)
class OSPFRedistributionType(PrimaryObjectType):
    instance: Annotated[
        "OSPFInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    protocol: str
    ospf_source: (
        Annotated[
            "OSPFInstanceType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    eigrp_source: (
        Annotated[
            "EIGRPRouterType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    bgp_source: (
        Annotated[
            "BGPRouterType", strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
        | None
    )
    isis_source: (
        Annotated[
            "ISISInstanceType",
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ]
        | None
    )
    metric: int | None
    metric_type: str
    subnets: bool
    route_tag: int | None
    route_policy: str
    ospf_match: list[str]


@strawberry_django.type(
    models.OSPFVirtualLink, fields='__all__', filters=OSPFVirtualLinkFilter
)
class OSPFVirtualLinkType(PrimaryObjectType):
    instance: Annotated[
        "OSPFInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    transit_area: Annotated[
        "OSPFAreaType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    remote_router_id: str


@strawberry_django.type(
    models.OSPFSummaryAddress, fields='__all__', filters=OSPFSummaryAddressFilter
)
class OSPFSummaryAddressType(PrimaryObjectType):
    instance: Annotated[
        "OSPFInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    prefix: str
    not_advertise: bool
    route_tag: int | None


@strawberry_django.type(
    models.OSPFNeighbor, fields='__all__', filters=OSPFNeighborFilter
)
class OSPFNeighborType(PrimaryObjectType):
    ospf_interface: Annotated[
        "OSPFInterfaceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    ip_address: str
    priority: int | None
    poll_interval: int | None


@strawberry_django.type(
    models.OSPFAreaRange, fields='__all__', filters=OSPFAreaRangeFilter
)
class OSPFAreaRangeType(PrimaryObjectType):
    area: Annotated[
        "OSPFAreaType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    prefix: str
    range_type: str
    advertise: bool
