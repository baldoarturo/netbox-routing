import strawberry_django

from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing_plugin import models

__all__ = (
    'BGPInstanceFilter',
    'BGPAddressFamilyFilter',
    'BGPPeerGroupFilter',
    'BGPListenRangeFilter',
    'BGPRedistributionFilter',
    'BGPOriginatedNetworkFilter',
    'BGPAggregateFilter',
    'BGPPeerFilter',
    'BGPPeerAddressFamilyFilter',
    'BFDProfileFilter',
)


@strawberry_django.filter(models.BGPInstance, lookups=True)
class BGPInstanceFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPAddressFamily, lookups=True)
class BGPAddressFamilyFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPPeerGroup, lookups=True)
class BGPPeerGroupFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPListenRange, lookups=True)
class BGPListenRangeFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPRedistribution, lookups=True)
class BGPRedistributionFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPOriginatedNetwork, lookups=True)
class BGPOriginatedNetworkFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPAggregate, lookups=True)
class BGPAggregateFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPPeer, lookups=True)
class BGPPeerFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BGPPeerAddressFamily, lookups=True)
class BGPPeerAddressFamilyFilter(PrimaryModelFilter):
    pass


@strawberry_django.filter(models.BFDProfile, lookups=True)
class BFDProfileFilter(PrimaryModelFilter):
    pass
