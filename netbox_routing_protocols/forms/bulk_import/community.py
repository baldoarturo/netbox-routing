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
    """
    Same rules as the entry form: an empty `sequence` takes the next free one. `community`
    must be written in its normal form (what the page of the community shows), not as a
    name or with leading zeros; when several tenants have the same value, `community_tenant`
    says which one (by default the one of the list's tenant, then the one with no tenant).
    """

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
    community = forms.CharField(
        help_text=_('Community value, in its normal form (see the community page)'),
    )
    community_tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Tenant of the community, when several have the same value'),
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

    def clean_community(self):
        value = self.cleaned_data['community'].strip()
        try:
            normal = community_helpers.normalize(value)
        except ValidationError as e:
            raise forms.ValidationError(e.messages)
        if value != normal:
            raise forms.ValidationError(
                _('Write the community in its normal form: %(normal)s.')
                % {'normal': normal}
            )
        return value

    def _find_community(self, value, community_list, tenant):
        """The community with the value, or an error message"""
        found = Community.objects.filter(community=value)
        if tenant is not None:
            found = found.filter(tenant=tenant)
        count = found.count()
        if count > 1 and community_list is not None:
            # the tenant of the list first, then the communities with no tenant
            for preferred in (community_list.tenant, None):
                narrowed = found.filter(tenant=preferred)
                if narrowed.count() == 1:
                    return narrowed.get(), None
        if count == 1:
            return found.get(), None
        if count == 0:
            return None, _('No community %(value)s%(where)s.') % {
                'value': value,
                'where': (
                    _(' of the tenant %(tenant)s') % {'tenant': tenant}
                    if tenant
                    else ''
                ),
            }
        return None, _(
            'Several communities have the value %(value)s: add community_tenant.'
        ) % {'value': value}

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        community_list = cleaned.get('community_list')
        if cleaned.get('community'):
            community, error = self._find_community(
                cleaned['community'], community_list, cleaned.get('community_tenant')
            )
            if error:
                self.add_error('community', error)
            else:
                cleaned['community'] = community
                self.instance.community = community
        if cleaned.get('sequence') is None and community_list:
            try:
                cleaned['sequence'] = community_helpers.next_sequence(community_list)
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
