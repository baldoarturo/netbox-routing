# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Union

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.isis.filters import (
    ISISInstanceFilter,
    ISISInterfaceFilter,
    ISISSettingFilter,
    ISISLevelFilter,
    ISISInterfaceLevelFilter,
    ISISSegmentRoutingFilter,
    ISISFlexAlgoFilter,
    ISISPrefixSIDFilter,
    ISISSRv6LocatorFilter,
    ISISAreaAddressFilter,
    ISISRedistributionFilter,
    ISISSummaryAddressFilter,
    ISISRouteLeakFilter,
)

__all__ = (
    'ISISInstanceType',
    'ISISInterfaceType',
    'ISISSettingType',
    'ISISLevelType',
    'ISISInterfaceLevelType',
    'ISISSegmentRoutingType',
    'ISISFlexAlgoType',
    'ISISPrefixSIDType',
    'ISISSRv6LocatorType',
    'ISISAreaAddressType',
    'ISISRedistributionType',
    'ISISSummaryAddressType',
    'ISISRouteLeakType',
)


@strawberry_django.type(
    models.ISISFlexAlgo, fields='__all__', filters=ISISFlexAlgoFilter
)
class ISISFlexAlgoType(PrimaryObjectType):
    instance: Annotated[
        'ISISInstanceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    algo_id: int


@strawberry_django.type(
    models.ISISPrefixSID, fields='__all__', filters=ISISPrefixSIDFilter
)
class ISISPrefixSIDType(PrimaryObjectType):
    interface: Annotated[
        'ISISInterfaceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    algorithm: int


@strawberry_django.type(
    models.ISISSRv6Locator, fields='__all__', filters=ISISSRv6LocatorFilter
)
class ISISSRv6LocatorType(PrimaryObjectType):
    instance: Annotated[
        'ISISInstanceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    name: str
    # prefix is an IPNetworkField; expose it as a string (mirrors StaticRouteType.prefix).
    # vendor_ext (JSONField) is auto-mapped to the JSON scalar by fields='__all__'.
    prefix: str | None


class ISISSettingsMixin:
    settings: list[
        Annotated[
            'ISISSettingType', strawberry.lazy('netbox_routing_protocols.graphql.types')
        ]
    ]


@strawberry_django.type(
    models.ISISLevel,
    # Drop fields='__all__' so exclude is honoured — keeps the plaintext per-level
    # auth_key off the schema (auth_type stays). See ISISSettingType below.
    exclude=['auth_key'],
    filters=ISISLevelFilter,
)
class ISISLevelType(PrimaryObjectType):
    instance: Annotated[
        'ISISInstanceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    level: int


@strawberry_django.type(
    models.ISISInterfaceLevel,
    exclude=['hello_auth_key'],
    filters=ISISInterfaceLevelFilter,
)
class ISISInterfaceLevelType(PrimaryObjectType):
    interface: Annotated[
        'ISISInterfaceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    level: int
    hello_auth_type: str | None


@strawberry_django.type(
    models.ISISSegmentRouting, fields='__all__', filters=ISISSegmentRoutingFilter
)
class ISISSegmentRoutingType(PrimaryObjectType):
    instance: Annotated[
        'ISISInstanceType', strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]


@strawberry_django.type(
    models.ISISSetting,
    # NB: `exclude` is only honoured when `fields='__all__'` is NOT also set —
    # otherwise `fields` wins and the raw GFK columns leak onto the schema. So we
    # rely on `exclude` alone (= all fields minus the excluded ones). The
    # non-secret `assigned_object_type` is re-added below as a typed
    # ContentTypeType; `assigned_object_id` stays hidden in favour of the
    # resolved `assigned_object` union.
    exclude=['assigned_object_type', 'assigned_object_id'],
    filters=ISISSettingFilter,
)
class ISISSettingType(PrimaryObjectType):

    assigned_object_type: (
        Annotated["ContentTypeType", strawberry.lazy('netbox.graphql.types')] | None
    )
    assigned_object: Union[
        Annotated[
            'ISISInstanceType',
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ],
        Annotated[
            'ISISInterfaceType',
            strawberry.lazy('netbox_routing_protocols.graphql.types'),
        ],
        None,
    ]
    key: str
    value: str


@strawberry_django.type(
    models.ISISInstance,
    exclude=['area_auth_key', 'domain_auth_key'],
    filters=ISISInstanceFilter,
)
class ISISInstanceType(ISISSettingsMixin, PrimaryObjectType):

    device: Annotated["DeviceType", strawberry.lazy('dcim.graphql.types')]
    vrf: Annotated["VRFType", strawberry.lazy('ipam.graphql.types')] | None
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
    process_tag: str
    net: str
    is_type: str
    metric_style: str
    overload_bit: bool | None
    area_auth_type: str
    domain_auth_type: str


@strawberry_django.type(
    models.ISISInterface,
    exclude=['hello_auth_key'],
    filters=ISISInterfaceFilter,
)
class ISISInterfaceType(ISISSettingsMixin, PrimaryObjectType):

    instance: Annotated[
        "ISISInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    interface: Annotated["InterfaceType", strawberry.lazy('dcim.graphql.types')]
    address_family: str
    circuit_type: str | None
    network_type: str | None
    metric: int | None
    passive: bool | None
    hello_auth_type: str | None
    bfd_enabled: bool | None


@strawberry_django.type(
    models.ISISRedistribution, fields='__all__', filters=ISISRedistributionFilter
)
class ISISRedistributionType(PrimaryObjectType):
    instance: Annotated[
        "ISISInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    address_family: str
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
    level: str
    metric: int | None
    metric_type: str
    route_tag: int | None
    route_policy: str


@strawberry_django.type(
    models.ISISSummaryAddress, fields='__all__', filters=ISISSummaryAddressFilter
)
class ISISSummaryAddressType(PrimaryObjectType):
    instance: Annotated[
        "ISISInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    prefix: str
    level: str
    not_advertise: bool
    metric: int | None
    route_tag: int | None


@strawberry_django.type(
    models.ISISRouteLeak, fields='__all__', filters=ISISRouteLeakFilter
)
class ISISRouteLeakType(PrimaryObjectType):
    instance: Annotated[
        "ISISInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    address_family: str
    route_policy: str


@strawberry_django.type(
    models.ISISAreaAddress, fields='__all__', filters=ISISAreaAddressFilter
)
class ISISAreaAddressType(PrimaryObjectType):
    instance: Annotated[
        "ISISInstanceType", strawberry.lazy('netbox_routing_protocols.graphql.types')
    ]
    net: str
