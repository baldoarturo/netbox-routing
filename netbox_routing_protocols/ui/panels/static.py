from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'StaticRoutePanel',
    'StaticRouteRoutePanel',
)


class StaticRoutePanel(panels.ObjectAttributesPanel):
    display = attrs.TextAttr('__str__', label=_('Display Name'))
    description = attrs.TextAttr('description', label=_('Description'))


class StaticRouteRoutePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Route Name'))
    vrf = attrs.RelatedObjectAttr('vrf', linkify=True, label=_('VRF'))
    prefix = attrs.TextAttr('prefix', label=_('Prefix'))
    next_hop = attrs.TextAttr('next_hop', label=_('Next Hop'))
    next_hop_type = attrs.ChoiceAttr('next_hop_type', label=_('Next Hop Type'))
    interface = attrs.RelatedObjectAttr(
        'interface', linkify=True, label=_('Interface Next Hop')
    )
    next_hop_vrf = attrs.RelatedObjectAttr(
        'next_hop_vrf', linkify=True, label=_('Next Hop VRF')
    )
    next_hop_global = attrs.BooleanAttr(
        'next_hop_global', label=_('Next Hop in the Global Table')
    )
    distance = attrs.TextAttr('distance', label=_('Distance'))
    tag = attrs.TextAttr('tag', label=_('Route Tag'))
    permanent = attrs.BooleanAttr('permanent', label=_('Permanent'))
