from typing import TYPE_CHECKING, Annotated

import strawberry
import strawberry_django
from strawberry import ID
from strawberry_django import BaseFilterLookup, StrFilterLookup

from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.filter_mixins import (
    VRFMixin,
    DeviceMixin,
    InterfaceMixin,
)

if TYPE_CHECKING:
    from netbox_routing_protocols.graphql.objects.filters import RoutePolicyFilter

__all__ = (
    'OSPFAreaFilter',
    'OSPFInstanceFilter',
    'OSPFInterfaceFilter',
    'OSPFNetworkFilter',
    'OSPFRedistributionFilter',
    'OSPFVirtualLinkFilter',
    'OSPFSummaryAddressFilter',
    'OSPFNeighborFilter',
    'OSPFAreaRangeFilter',
    'OSPFPrefixSIDFilter',
)


@strawberry_django.filter(models.OSPFInstance, lookups=True)
class OSPFInstanceFilter(VRFMixin, DeviceMixin, PrimaryModelFilter):
    router_id: BaseFilterLookup[str] | None = strawberry_django.filter_field()
    address_family: BaseFilterLookup[str] | None = strawberry_django.filter_field()
    import_policy: (
        Annotated[
            'RoutePolicyFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    import_policy_id: ID | None = strawberry_django.filter_field()
    export_policy: (
        Annotated[
            'RoutePolicyFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    export_policy_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFArea, lookups=True)
class OSPFAreaFilter(PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()
    area_id: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFInterface, lookups=True)
class OSPFInterfaceFilter(InterfaceMixin, VRFMixin, PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()
    area: (
        Annotated[
            'OSPFAreaFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    area_id: ID | None = strawberry_django.filter_field()
    network_type: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFNetwork, lookups=True)
class OSPFNetworkFilter(PrimaryModelFilter):
    ospf_interface: (
        Annotated[
            'OSPFInterfaceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    ospf_interface_id: ID | None = strawberry_django.filter_field()
    ip_address_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFRedistribution, lookups=True)
class OSPFRedistributionFilter(PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()
    protocol: StrFilterLookup | None = strawberry_django.filter_field()
    route_policy: StrFilterLookup | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFVirtualLink, lookups=True)
class OSPFVirtualLinkFilter(PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()
    transit_area_id: ID | None = strawberry_django.filter_field()
    remote_router_id: BaseFilterLookup[str] | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFSummaryAddress, lookups=True)
class OSPFSummaryAddressFilter(PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFNeighbor, lookups=True)
class OSPFNeighborFilter(PrimaryModelFilter):
    ospf_interface: (
        Annotated[
            'OSPFInterfaceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    ospf_interface_id: ID | None = strawberry_django.filter_field()
    ip_address: BaseFilterLookup[str] | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFAreaRange, lookups=True)
class OSPFAreaRangeFilter(PrimaryModelFilter):
    area: (
        Annotated[
            'OSPFAreaFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    area_id: ID | None = strawberry_django.filter_field()


@strawberry_django.filter(models.OSPFPrefixSID, lookups=True)
class OSPFPrefixSIDFilter(PrimaryModelFilter):
    instance: (
        Annotated[
            'OSPFInstanceFilter',
            strawberry.lazy('netbox_routing_protocols.graphql.filters'),
        ]
        | None
    ) = strawberry_django.filter_field()
    instance_id: ID | None = strawberry_django.filter_field()
