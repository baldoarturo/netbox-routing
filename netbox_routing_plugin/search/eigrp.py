from netbox.search import SearchIndex, register_search
from netbox_routing_plugin.models.eigrp import (
    EIGRPAddressFamily,
    EIGRPInterface,
    EIGRPNetwork,
    EIGRPRouter,
)

__all__ = (
    'EIGRPRouterIndex',
    'EIGRPAddressFamilyIndex',
    'EIGRPNetworkIndex',
    'EIGRPInterfaceIndex',
)


@register_search
class EIGRPRouterIndex(SearchIndex):
    model = EIGRPRouter
    fields = (
        ('rid', 100),
        ('pid', 200),
        ('name', 210),
        ('comments', 5000),
    )
    display_attrs = ('device', 'mode')


@register_search
class EIGRPAddressFamilyIndex(SearchIndex):
    model = EIGRPAddressFamily
    fields = (
        ('rid', 100),
        ('comments', 5000),
    )


@register_search
class EIGRPNetworkIndex(SearchIndex):
    model = EIGRPNetwork
    fields = (
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('router', 'address_family')


@register_search
class EIGRPInterfaceIndex(SearchIndex):
    # The passphrase is a secret: it is not indexed
    model = EIGRPInterface
    fields = (
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('router', 'address_family')
