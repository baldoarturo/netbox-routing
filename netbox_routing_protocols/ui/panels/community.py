from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'CommunityListPanel',
    'CommunityPanel',
    'CommunityListEntryPanel',
)


class CommunityListPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    type = attrs.ChoiceAttr('type', label=_('Type'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True, label=_('Tenant'))
    description = attrs.TextAttr('description', label=_('Description'))


class CommunityPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    community = attrs.TextAttr('community', label=_('Community'))
    type = attrs.ChoiceAttr('type', label=_('Type'))
    well_known = attrs.TextAttr('well_known', label=_('Well-known'))
    status = attrs.ChoiceAttr('status', label=_('Status'))
    role = attrs.RelatedObjectAttr('role', linkify=True, label=_('Role'))
    tenant = attrs.RelatedObjectAttr('tenant', linkify=True, label=_('Tenant'))
    description = attrs.TextAttr('description', label=_('Description'))


class CommunityListEntryPanel(panels.ObjectAttributesPanel):
    community_list = attrs.RelatedObjectAttr('community_list', linkify=True)
    sequence = attrs.NumericAttr('sequence', label=_('Sequence'))
    action = attrs.ChoiceAttr('action', label=_('Action'))
    community = attrs.RelatedObjectAttr('community', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
