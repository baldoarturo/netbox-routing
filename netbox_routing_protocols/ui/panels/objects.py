from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'UnreachablePanel',
    'ASPathPanel',
    'ASPathEntryPanel',
    'PrefixListPanel',
    'PrefixListEntryPanel',
    'OverlapsPanel',
    'RoutePolicyPanel',
    'RoutePolicyEntryPanel',
    'RoutePolicyEntryMatchPanel',
    'RoutePolicyEntrySetPanel',
)


class ASPathPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    description = attrs.TextAttr('description', label=_('Description'))


class ASPathEntryPanel(panels.ObjectAttributesPanel):
    aspath = attrs.RelatedObjectAttr('aspath', linkify=True, label=_('AS-Path'))
    sequence = attrs.NumericAttr('sequence', label=_('Sequence'))
    action = attrs.ChoiceAttr('action', label=_('Action'))
    pattern = attrs.TextAttr('pattern', label=_('Pattern'))
    description = attrs.TextAttr('description', label=_('Description'))


class PrefixListPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    family = attrs.ChoiceAttr('family', label=_('Family'))
    description = attrs.TextAttr('description', label=_('Description'))


class PrefixListEntryPanel(panels.ObjectAttributesPanel):
    prefix_list = attrs.RelatedObjectAttr(
        'prefix_list', linkify=True, label=_('Prefix List')
    )
    sequence = attrs.NumericAttr('sequence', label=_('Sequence'))
    action = attrs.ChoiceAttr('action', label=_('Action'))
    prefix = attrs.RelatedObjectAttr('prefix', linkify=True, label=_('Prefix'))
    any_prefix = attrs.BooleanAttr('any_prefix', label=_('Any'))
    ge = attrs.NumericAttr('ge', label=_('Greater Than or Equal'))
    le = attrs.NumericAttr('le', label=_('Less Than or Equal'))
    description = attrs.TextAttr('description', label=_('Description'))


class RoutePolicyPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    description = attrs.TextAttr('description', label=_('Description'))


class RoutePolicyEntryPanel(panels.ObjectAttributesPanel):
    route_policy = attrs.RelatedObjectAttr(
        'route_policy', linkify=True, label=_('Route Policy')
    )
    sequence = attrs.NumericAttr('sequence', label=_('Sequence'))
    action = attrs.ChoiceAttr('action', label=_('Action'))
    jump_policy = attrs.RelatedObjectAttr(
        'jump_policy', linkify=True, label=_('Jump to Route Policy')
    )
    matches_everything = attrs.BooleanAttr(
        'matches_everything', label=_('Matches every route')
    )
    implicit = attrs.BooleanAttr('implicit', label=_('Final deny'))
    description = attrs.TextAttr('description', label=_('Description'))


class RoutePolicyEntryMatchPanel(panels.ObjectAttributesPanel):
    match_prefix_list = attrs.RelatedObjectListAttr(
        'match_prefix_list', linkify=True, label=_('Prefix List')
    )
    match_aspath = attrs.RelatedObjectListAttr(
        'match_aspath', linkify=True, label=_('AS Path List')
    )
    match_community_list = attrs.RelatedObjectListAttr(
        'match_community_list', linkify=True, label=_('Community List')
    )
    match_next_hop = attrs.RelatedObjectAttr(
        'match_next_hop', linkify=True, label=_('Next Hop')
    )
    match_metric = attrs.NumericAttr('match_metric', label=_('Metric'))
    match_origin = attrs.ChoiceAttr('match_origin', label=_('Origin'))
    match_tag = attrs.NumericAttr('match_tag', label=_('Tag'))
    match_weight = attrs.NumericAttr('match_weight', label=_('Weight'))


class RoutePolicyEntrySetPanel(panels.ObjectAttributesPanel):
    set_local_preference = attrs.NumericAttr(
        'set_local_preference', label=_('Local Preference')
    )
    set_next_hop = attrs.RelatedObjectAttr(
        'set_next_hop', linkify=True, label=_('Next Hop')
    )
    set_aspath_prepend = attrs.TextAttr(
        'aspath_prepend_text', label=_('AS-Path Prepend')
    )
    set_community_list = attrs.RelatedObjectAttr(
        'set_community_list', linkify=True, label=_('Community List')
    )
    set_community_mode = attrs.ChoiceAttr(
        'set_community_mode', label=_('Community Mode')
    )
    set_metric = attrs.NumericAttr('set_metric', label=_('Metric'))
    set_metric_mode = attrs.ChoiceAttr('set_metric_mode', label=_('Metric Mode'))
    set_origin = attrs.ChoiceAttr('set_origin', label=_('Origin'))
    set_tag = attrs.NumericAttr('set_tag', label=_('Tag'))
    set_weight = attrs.NumericAttr('set_weight', label=_('Weight'))


class UnreachablePanel(panels.TemplatePanel):
    """The entries of a route policy that are never evaluated, and the one that stops them"""

    def __init__(self, **kwargs):
        super().__init__('netbox_routing_protocols/panels/unreachable.html', **kwargs)

    def should_render(self, context):
        return bool(context.get('unreachable'))


class OverlapsPanel(panels.TemplatePanel):
    """The entries of the same list that overlap or are nested with the one shown"""

    def __init__(self, **kwargs):
        super().__init__('netbox_routing_protocols/panels/overlaps.html', **kwargs)

    def should_render(self, context):
        return bool(context.get('overlaps'))
