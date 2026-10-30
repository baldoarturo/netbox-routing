from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import PrimaryObjectType
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.static.filters import StaticRouteFilter

__all__ = ('StaticRouteType',)


@strawberry_django.type(models.StaticRoute, fields='__all__', filters=StaticRouteFilter)
class StaticRouteType(PrimaryObjectType):
    name: str
    devices: list[Annotated["DeviceType", strawberry.lazy('dcim.graphql.types')]] | None
    vrf: Annotated["VRFType", strawberry.lazy('ipam.graphql.types')] | None
    prefix: str | None
    next_hop: str | None
    interface: Annotated["InterfaceType", strawberry.lazy('dcim.graphql.types')] | None
    next_hop_type: str
    next_hop_vrf: Annotated["VRFType", strawberry.lazy('ipam.graphql.types')] | None
    next_hop_global: bool
    distance: int
    permanent: bool
    tag: int | None
