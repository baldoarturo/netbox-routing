from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from netbox.context import current_request
from django.contrib import messages

from netbox.forms import PrimaryModelForm
from tenancy.forms import TenancyForm
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.helpers import community as community_helpers
from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.models.community import *

# How many duplicates are named in the warning after saving an entry
MAX_WARNINGS = 5

__all__ = (
    'CommunityListDuplicateForm',
    'CommunityListForm',
    'CommunityListEntryForm',
    'CommunityForm',
)


class CommunityListForm(TenancyForm, PrimaryModelForm):
    fieldsets = (
        FieldSet('name', 'type', 'description'),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = CommunityList
        fields = [
            'name',
            'type',
            'tenant_group',
            'tenant',
            'description',
            'comments',
            'tags',
            'owner',
        ]


class CommunityForm(TenancyForm, PrimaryModelForm):
    fieldsets = (
        FieldSet('name', 'community', 'status', 'role', 'description'),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = Community
        fields = [
            'name',
            'community',
            'status',
            'role',
            'tenant_group',
            'tenant',
            'description',
            'comments',
            'tags',
            'owner',
        ]


class CommunityListEntryForm(PrimaryModelForm):
    """
    An empty `sequence` of a new entry takes the next one of the list, suggested here when
    the list is known and assigned on save otherwise. Duplicates (the same community twice
    in the list) are flashed as warnings after saving.
    """

    fieldsets = (
        FieldSet('community_list', 'sequence', 'action', 'community', 'description'),
    )

    class Meta:
        model = CommunityListEntry
        fields = [
            'community_list',
            'sequence',
            'action',
            'community',
            'description',
            'comments',
            'tags',
            'owner',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sequence'].help_text = _(
            'From 1 to 4294967294. Entries are evaluated in this order. Leave empty to '
            'use the next one of the list.'
        )
        # Only for a new entry: emptying it on an existing one would silently move the
        # entry to the end of the list
        if self.instance.pk:
            return
        self.fields['sequence'].required = False
        if not self.initial.get('action'):
            self.initial['action'] = ActionChoices.PERMIT
        if not self.initial.get('sequence'):
            pk = str(self.initial.get('community_list') or '')
            community_list = (
                CommunityList.objects.filter(pk=pk).first() if pk.isdigit() else None
            )
            if community_list:
                try:
                    self.initial['sequence'] = community_helpers.next_sequence(
                        community_list
                    )
                except ValidationError:
                    pass

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        if (
            not self.instance.pk
            and cleaned.get('sequence') is None
            and cleaned.get('community_list')
        ):
            try:
                cleaned['sequence'] = community_helpers.next_sequence(
                    cleaned['community_list']
                )
            except ValidationError as e:
                raise forms.ValidationError({'sequence': e.messages})
            self.instance.sequence = cleaned['sequence']

    def save(self, commit=True):
        entry = super().save(commit)
        if commit and (request := current_request.get()) is not None:
            for duplicate in community_helpers.find_duplicates(entry)[:MAX_WARNINGS]:
                messages.warning(request, duplicate.message + '.')
        return entry


class CommunityListDuplicateForm(forms.Form):
    """The name and description of the copy of a community list"""

    name = forms.CharField(max_length=100, label=_('Name'))
    description = forms.CharField(
        max_length=200, required=False, label=_('Description')
    )

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if CommunityList.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(
                _('A community list with this name already exists.')
            )
        return name
