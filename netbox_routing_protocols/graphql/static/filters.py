import strawberry_django
from strawberry_django import BaseFilterLookup, StrFilterLookup

from netbox.graphql.filter_lookups import BigIntegerLookup, IntegerLookup
from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_protocols import models
from netbox_routing_protocols.graphql.filter_mixins import VRFMixin, DeviceMixin

__all__ = ('StaticRouteFilter',)


@strawberry_django.filter(models.StaticRoute, lookups=True)
class StaticRouteFilter(VRFMixin, DeviceMixin, PrimaryModelFilter):
    prefix: StrFilterLookup | None = strawberry_django.filter_field()
    next_hop: BaseFilterLookup[str] | None = strawberry_django.filter_field()
    next_hop_type: StrFilterLookup | None = strawberry_django.filter_field()
    next_hop_global: BaseFilterLookup[bool] | None = strawberry_django.filter_field()
    name: StrFilterLookup | None = strawberry_django.filter_field()
    distance: IntegerLookup | None = strawberry_django.filter_field()
    tag: BigIntegerLookup | None = strawberry_django.filter_field()
    permanent: BaseFilterLookup[bool] | None = strawberry_django.filter_field()
