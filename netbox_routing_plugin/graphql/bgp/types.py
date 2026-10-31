from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType

from netbox_routing_plugin import models
from netbox_routing_plugin.graphql.bgp.filters import (
    BGPInstanceFilter,
    BGPAddressFamilyFilter,
    BGPPeerGroupFilter,
    BGPListenRangeFilter,
    BGPRedistributionFilter,
    BGPOriginatedNetworkFilter,
    BGPAggregateFilter,
    BGPPeerFilter,
    BGPPeerAddressFamilyFilter,
    BFDProfileFilter,
)

__all__ = (
    'BGPInstanceType',
    'BGPAddressFamilyType',
    'BGPPeerGroupType',
    'BGPListenRangeType',
    'BGPRedistributionType',
    'BGPOriginatedNetworkType',
    'BGPAggregateType',
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
    cluster_id: str | None
    confederation_identifier: (
        Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    )
    confederation_peers: list[
        Annotated["ASNType", strawberry.lazy('ipam.graphql.types')]
    ]
    graceful_restart: bool | None
    graceful_restart_time: int | None
    graceful_restart_stale_time: int | None
    graceful_restart_helper_only: bool | None
    import_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    export_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    address_families: list[
        Annotated[
            "BGPAddressFamilyType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]
    peer_groups: list[
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]
    peers: list[
        Annotated["BGPPeerType", strawberry.lazy('netbox_routing_plugin.graphql.types')]
    ]


@strawberry_django.type(
    models.BGPAddressFamily, fields='__all__', filters=BGPAddressFamilyFilter
)
class BGPAddressFamilyType(PrimaryObjectType):
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_plugin.graphql.types')
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
    long_lived_stale_time: int | None
    redistributions: list[
        Annotated[
            "BGPRedistributionType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(
    models.BGPPeerGroup, fields='__all__', filters=BGPPeerGroupFilter
)
class BGPPeerGroupType(PrimaryObjectType):
    name: str
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_plugin.graphql.types')
    ]
    listen_limit: int | None
    listen_ranges: list[
        Annotated[
            "BGPListenRangeType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]
    remote_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    local_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    enabled: bool | None
    bfd: (
        Annotated[
            "BFDProfileType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    ebgp_multihop: int | None
    ttl_security_hops: int | None
    passive: bool | None
    as_override: bool | None
    soft_reconfiguration_inbound: bool | None
    graceful_shutdown: bool | None
    import_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    export_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    passphrase: str | None
    show_md5: bool
    route_reflector_client: bool | None
    extended_nexthop: bool | None
    keepalive: int | None
    hold_time: int | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    peers: list[
        Annotated["BGPPeerType", strawberry.lazy('netbox_routing_plugin.graphql.types')]
    ]
    address_families: list[
        Annotated[
            "BGPPeerAddressFamilyType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]


@strawberry_django.type(
    models.BGPListenRange, fields='__all__', filters=BGPListenRangeFilter
)
class BGPListenRangeType(PrimaryObjectType):
    peer_group: Annotated[
        "BGPPeerGroupType", strawberry.lazy('netbox_routing_plugin.graphql.types')
    ]
    prefix: Annotated["PrefixType", strawberry.lazy('ipam.graphql.types')]


@strawberry_django.type(
    models.BGPRedistribution, fields='__all__', filters=BGPRedistributionFilter
)
class BGPRedistributionType(PrimaryObjectType):
    address_family: Annotated[
        "BGPAddressFamilyType",
        strawberry.lazy('netbox_routing_plugin.graphql.types'),
    ]
    protocol: str
    metric: int | None
    route_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    ospf_match: list[str]
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(
    models.BGPOriginatedNetwork, fields='__all__', filters=BGPOriginatedNetworkFilter
)
class BGPOriginatedNetworkType(PrimaryObjectType):
    address_family: Annotated[
        "BGPAddressFamilyType",
        strawberry.lazy('netbox_routing_plugin.graphql.types'),
    ]
    prefix: Annotated["PrefixType", strawberry.lazy('ipam.graphql.types')]
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(
    models.BGPAggregate, fields='__all__', filters=BGPAggregateFilter
)
class BGPAggregateType(PrimaryObjectType):
    address_family: Annotated[
        "BGPAddressFamilyType",
        strawberry.lazy('netbox_routing_plugin.graphql.types'),
    ]
    prefix: Annotated["PrefixType", strawberry.lazy('ipam.graphql.types')]
    summary_only: bool
    as_set: bool
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None


@strawberry_django.type(models.BGPPeer, fields='__all__', filters=BGPPeerFilter)
class BGPPeerType(PrimaryObjectType):
    name: str | None
    instance: Annotated[
        "BGPInstanceType", strawberry.lazy('netbox_routing_plugin.graphql.types')
    ]
    peer: Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')] | None
    interface: Annotated["InterfaceType", strawberry.lazy('dcim.graphql.types')] | None
    source: Annotated["IPAddressType", strawberry.lazy('ipam.graphql.types')] | None
    peer_group: (
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
        | None
    )
    status: str | None
    remote_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    local_as: Annotated["ASNType", strawberry.lazy('ipam.graphql.types')] | None
    enabled: bool | None
    bfd: (
        Annotated[
            "BFDProfileType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    ebgp_multihop: int | None
    ttl_security_hops: int | None
    passive: bool | None
    as_override: bool | None
    soft_reconfiguration_inbound: bool | None
    graceful_shutdown: bool | None
    import_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    export_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    passphrase: str | None
    show_md5: bool
    route_reflector_client: bool | None
    extended_nexthop: bool | None
    keepalive: int | None
    hold_time: int | None
    tenant: Annotated["TenantType", strawberry.lazy('tenancy.graphql.types')] | None
    address_families: list[
        Annotated[
            "BGPPeerAddressFamilyType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
    ]


@strawberry_django.type(
    models.BGPPeerAddressFamily, fields='__all__', filters=BGPPeerAddressFamilyFilter
)
class BGPPeerAddressFamilyType(PrimaryObjectType):
    peer: (
        Annotated["BGPPeerType", strawberry.lazy('netbox_routing_plugin.graphql.types')]
        | None
    )
    peer_group: (
        Annotated[
            "BGPPeerGroupType",
            strawberry.lazy('netbox_routing_plugin.graphql.types'),
        ]
        | None
    )
    address_family: Annotated[
        "BGPAddressFamilyType",
        strawberry.lazy('netbox_routing_plugin.graphql.types'),
    ]
    enabled: bool | None
    send_community: list[str]
    next_hop_self: bool | None
    remove_private_as: bool | None
    allowas_in: int | None
    maximum_prefix: int | None
    maximum_prefix_warning: int | None
    maximum_prefix_action: str | None
    maximum_prefix_restart: int | None
    prefixlist_in: (
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    prefixlist_out: (
        Annotated[
            "PrefixListType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    import_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
        ]
        | None
    )
    export_policy: (
        Annotated[
            "RoutePolicyType", strawberry.lazy('netbox_routing_plugin.graphql.types')
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
