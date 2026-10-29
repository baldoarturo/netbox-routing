from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.models import Role
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.choices import CommunityStatusChoices, ActionChoices
from tenancy.forms import TenancyFilterForm
from utilities.forms import add_blank_choice
from utilities.forms.fields import TagFilterField, DynamicModelMultipleChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.models.community import *

__all__ = (
    'CommunityListFilterForm',
    'CommunityListEntryFilterForm',
    'CommunityFilterForm',
)


class CommunityListFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = CommunityList
    fieldsets = (
        FieldSet(
            'q',
            'filter_id',
            'tag',
        ),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )

    tag = TagFilterField(model)


class CommunityFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = Community
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('name', 'community', 'status', 'role_id', name=_('Community')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityStatusChoices),
        label=_('Status'),
    )
    name = forms.CharField(required=False, label=_('Name'))
    community = forms.CharField(required=False, label=_('Community'))
    role_id = DynamicModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        selector=True,
        label=_('Role'),
    )
    tag = TagFilterField(model)


class CommunityListEntryFilterForm(NetBoxModelFilterSetForm):
    model = CommunityListEntry
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('community_list_id', 'action', 'community_id', name=_('Community')),
    )
    action = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(ActionChoices),
        label=_('Action'),
    )
    community_id = DynamicModelMultipleChoiceField(
        queryset=Community.objects.all(),
        required=False,
        selector=True,
        label=_('Community'),
    )
    community_list_id = DynamicModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        selector=True,
        label=_('Community List'),
    )
    tag = TagFilterField(model)
