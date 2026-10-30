from netbox.search import SearchIndex, register_search
from netbox_routing_protocols.models.static import StaticRoute

__all__ = ('StaticRouteIndex',)


@register_search
class StaticRouteIndex(SearchIndex):
    model = StaticRoute
    fields = (
        ('name', 100),
        ('prefix', 200),
        ('next_hop', 300),
        ('interface_next_hop', 300),
        ('tag', 400),
        ('description', 500),
        ('comments', 5000),
    )
    display_attrs = ('prefix', 'next_hop', 'vrf')
