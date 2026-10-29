from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipam.models import Role
from netbox.context import current_request
from netbox.forms import NetBoxModelImportForm
from tenancy.models import Tenant
from utilities.forms.fields import CSVChoiceField, CSVModelChoiceField

from netbox_routing_protocols.choices import ActionChoices, CommunityTypeChoices
from netbox_routing_protocols.helpers import community as community_helpers

from netbox_routing_protocols.models.community import (
    Community,
    CommunityList,
    CommunityListEntry,
)

__all__ = (
    'CommunityImportForm',
    'CommunityListImportForm',
    'CommunityListEntryImportForm',
)


class CommunityImportForm(NetBoxModelImportForm):
    role = CSVModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Role name'),
    )
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Tenant name'),
    )

    class Meta:
        model = Community
        fields = (
            'name',
            'community',
            'status',
            'role',
            'tenant',
            'description',
            'comments',
            'tags',
        )


class CommunityListImportForm(NetBoxModelImportForm):
    type = CSVChoiceField(
        choices=CommunityTypeChoices,
        required=False,
        help_text=_('standard (default), extended or large'),
    )
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Tenant name'),
    )

    class Meta:
        model = CommunityList
        fields = (
            'name',
            'type',
            'tenant',
            'description',
            'comments',
            'tags',
        )


class CommunityListEntryImportForm(NetBoxModelImportForm):
    """Same rules as the entry form: an empty `sequence` takes the next free one"""

    community_list = CSVModelChoiceField(
        queryset=CommunityList.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Community list name'),
    )
    action = CSVChoiceField(choices=ActionChoices, help_text=_('permit or deny'))
    sequence = forms.IntegerField(
        required=False,
        help_text=_('Empty takes the next free one of the list'),
    )
    community = CSVModelChoiceField(
        queryset=Community.objects.all(),
        required=True,
        to_field_name='community',
        help_text=_('Community value, in its normal form (see the community page)'),
    )

    class Meta:
        model = CommunityListEntry
        fields = (
            'community_list',
            'sequence',
            'action',
            'community',
            'description',
            'comments',
            'tags',
        )

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        if cleaned.get('sequence') is None and cleaned.get('community_list'):
            try:
                cleaned['sequence'] = community_helpers.next_sequence(
                    cleaned['community_list']
                )
            except ValidationError as e:
                self.add_error('sequence', e)
            else:
                self.instance.sequence = cleaned['sequence']
        return cleaned

    def save(self, commit=True):
        entry = super().save(commit)
        if commit and (request := current_request.get()) is not None:
            for duplicate in community_helpers.find_duplicates(entry)[:5]:
                messages.warning(request, duplicate.message + '.')
        return entry
