from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.models import Role
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.choices import (
    ActionChoices,
    CommunityStatusChoices,
    CommunityTypeChoices,
)
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
        FieldSet('name', 'type', name=_('Community List')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    name = forms.CharField(required=False, label=_('Name'))
    type = forms.MultipleChoiceField(
        choices=CommunityTypeChoices, required=False, label=_('Type')
    )
    tag = TagFilterField(model)


class CommunityFilterForm(TenancyFilterForm, NetBoxModelFilterSetForm):
    model = Community
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('name', 'community', 'type', 'status', 'role_id', name=_('Community')),
        FieldSet('tenant_group_id', 'tenant_id', name=_('Tenancy')),
    )
    status = forms.ChoiceField(
        required=False,
        choices=add_blank_choice(CommunityStatusChoices),
        label=_('Status'),
    )
    name = forms.CharField(required=False, label=_('Name'))
    community = forms.CharField(required=False, label=_('Community'))
    type = forms.MultipleChoiceField(
        choices=CommunityTypeChoices, required=False, label=_('Type')
    )
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
        FieldSet(
            'community_list_id',
            'sequence',
            'action',
            'community_id',
            name=_('Community'),
        ),
    )
    sequence = forms.IntegerField(
        label=_('Sequence'), required=False, min_value=1, max_value=4294967294
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
