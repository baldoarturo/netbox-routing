from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix, VRF
from netbox.forms import PrimaryModelImportForm
from utilities.forms.fields import CSVChoiceField, CSVModelChoiceField

from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.helpers import aspath as aspath_helpers
from netbox_routing_protocols.helpers.prefix_list import any_le, next_sequence
from netbox_routing_protocols.models.objects import (
    ASPath,
    ASPathEntry,
    PrefixList,
    PrefixListEntry,
)

__all__ = (
    'ASPathImportForm',
    'ASPathEntryImportForm',
    'PrefixListImportForm',
    'PrefixListEntryImportForm',
)


class ASPathImportForm(PrimaryModelImportForm):
    class Meta:
        model = ASPath
        fields = (
            'name',
            'description',
            'owner',
            'comments',
            'tags',
        )


class ASPathEntryImportForm(PrimaryModelImportForm):
    """Same rules as the entry form: an empty `sequence` takes the next free one"""

    aspath = CSVModelChoiceField(
        queryset=ASPath.objects.all(),
        to_field_name='name',
        help_text=_('Name of the AS-path'),
    )
    action = CSVChoiceField(choices=ActionChoices, help_text=_('permit or deny'))
    sequence = forms.IntegerField(
        required=False,
        help_text=_('Empty takes the next free one of the AS-path'),
    )

    class Meta:
        model = ASPathEntry
        fields = (
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'owner',
            'comments',
            'tags',
        )

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        if cleaned.get('sequence') is None and cleaned.get('aspath'):
            try:
                cleaned['sequence'] = aspath_helpers.next_sequence(cleaned['aspath'])
            except ValidationError as e:
                self.add_error('sequence', e)
        return cleaned


class PrefixListImportForm(PrimaryModelImportForm):
    family = forms.TypedChoiceField(
        choices=((4, 'IPv4'), (6, 'IPv6')),
        coerce=int,
        required=False,
        initial=4,
        help_text=_('Address family: 4 or 6 (4 when empty)'),
    )

    class Meta:
        model = PrefixList
        fields = (
            'name',
            'family',
            'description',
            'owner',
            'comments',
            'tags',
        )

    def clean_family(self):
        return self.cleaned_data.get('family') or 4


class PrefixListEntryImportForm(PrimaryModelImportForm):
    """
    Same rules as the entry form: `prefix` is a CIDR that exists in IPAM (`vrf` tells which
    one when the CIDR is in several VRFs) or `any`, an empty `sequence` takes the next free
    one, `eq` fills ge and le, and Any with no length matches everything.
    """

    prefix_list = CSVModelChoiceField(
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        help_text=_('Name of the prefix list'),
    )
    action = CSVChoiceField(choices=ActionChoices, help_text=_('permit or deny'))
    prefix = forms.CharField(
        help_text=_('Prefix that exists in IPAM (e.g. 10.0.0.0/8), or "any"'),
    )
    vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('VRF of the IPAM prefix, when the same prefix is in several VRFs'),
    )
    sequence = forms.IntegerField(
        required=False,
        help_text=_('Empty takes the next free one of the list'),
    )
    eq = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=128,
        help_text=_('Exact length: sets GE and LE to this value'),
    )

    class Meta:
        model = PrefixListEntry
        fields = (
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'ge',
            'le',
            'description',
            'owner',
            'comments',
            'tags',
        )

    def clean_prefix(self):
        value = self.cleaned_data['prefix'].strip()
        self.any_prefix = value.lower() == 'any'
        if self.any_prefix:
            return None
        return value

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        prefix_list = cleaned.get('prefix_list')

        # `prefix` is a CIDR here, the model wants the IPAM prefix it names
        if 'prefix' in cleaned and not self.any_prefix:
            cleaned['prefix'] = self._find_prefix(cleaned['prefix'], cleaned.get('vrf'))
        self.instance.any_prefix = getattr(self, 'any_prefix', False)

        if cleaned.get('sequence') is None and prefix_list:
            try:
                cleaned['sequence'] = next_sequence(prefix_list)
            except ValidationError as e:
                self.add_error('sequence', e)

        ge, le, eq = (cleaned.get(field) for field in ('ge', 'le', 'eq'))
        if eq is not None:
            if ge is not None or le is not None:
                self.add_error('eq', _('Use either the exact length, or GE and LE.'))
            else:
                cleaned['ge'] = cleaned['le'] = ge = le = eq
        if self.any_prefix and prefix_list and ge is None and le is None:
            cleaned['le'] = any_le(prefix_list.family)
        return cleaned

    def _find_prefix(self, value, vrf):
        try:
            prefixes = Prefix.objects.filter(prefix=value)
        except (ValidationError, ValueError, TypeError):
            self.add_error(
                'prefix', _('"%(value)s" is not a valid prefix.') % {'value': value}
            )
            return None
        if vrf:
            prefixes = prefixes.filter(vrf=vrf)
        matches = list(prefixes[:2])
        if not matches:
            self.add_error(
                'prefix',
                _('Prefix %(value)s does not exist in IPAM: create it first.')
                % {'value': value},
            )
        elif len(matches) > 1:
            self.add_error(
                'prefix',
                _('Prefix %(value)s exists in several VRFs: set the vrf column.')
                % {'value': value},
            )
        else:
            return matches[0]
        return None
