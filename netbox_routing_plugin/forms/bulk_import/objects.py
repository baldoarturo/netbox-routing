from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipam.models import IPAddress, Prefix, VRF
from netbox.forms import PrimaryModelImportForm
from utilities.forms.fields import (
    CSVChoiceField,
    CSVModelChoiceField,
    CSVModelMultipleChoiceField,
)

from netbox_routing_plugin.choices import (
    ActionChoices,
    CommunityModeChoices,
    MetricModeChoices,
    OriginChoices,
)
from netbox_routing_plugin.helpers import aspath as aspath_helpers
from netbox_routing_plugin.helpers import route_policy as route_policy_helpers
from netbox_routing_plugin.helpers.prefix_list import any_le, next_sequence
from netbox_routing_plugin.models.community import CommunityList
from netbox_routing_plugin.models.objects import (
    ASPath,
    ASPathEntry,
    PrefixList,
    PrefixListEntry,
    RoutePolicy,
    RoutePolicyEntry,
)

__all__ = (
    'ASPathImportForm',
    'ASPathEntryImportForm',
    'PrefixListImportForm',
    'PrefixListEntryImportForm',
    'RoutePolicyImportForm',
    'RoutePolicyEntryImportForm',
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


class RoutePolicyImportForm(PrimaryModelImportForm):
    class Meta:
        model = RoutePolicy
        fields = (
            'name',
            'description',
            'owner',
            'comments',
            'tags',
        )


class RoutePolicyEntryImportForm(PrimaryModelImportForm):
    """
    Same rules as the entry form: an empty `sequence` takes the next free one, and the
    objects an entry matches are written by name, several separated by commas. The next hops
    are IPAM addresses (`vrf` tells which one when the address is in several VRFs). A deny
    entry cannot set anything (checked by the model).
    """

    route_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        help_text=_('Name of the route policy'),
    )
    action = CSVChoiceField(choices=ActionChoices, help_text=_('permit or deny'))
    sequence = forms.IntegerField(
        required=False,
        help_text=_('Empty takes the next free one of the route policy'),
    )
    jump_policy = CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        to_field_name='name',
        required=False,
        help_text=_('Name of the route policy to jump to (a permit entry only)'),
    )
    match_prefix_list = CSVModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        to_field_name='name',
        required=False,
        help_text=_('Names of prefix lists, separated by commas'),
    )
    match_aspath = CSVModelMultipleChoiceField(
        queryset=ASPath.objects.all(),
        to_field_name='name',
        required=False,
        help_text=_('Names of AS-paths, separated by commas'),
    )
    match_community_list = CSVModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        to_field_name='name',
        required=False,
        help_text=_('Names of community lists, separated by commas'),
    )
    match_next_hop = forms.CharField(
        required=False,
        help_text=_('IPv4 or IPv6 address of IPAM, without the mask'),
    )
    match_origin = CSVChoiceField(
        choices=OriginChoices, required=False, help_text=_('igp, egp or incomplete')
    )
    set_next_hop = forms.CharField(
        required=False,
        help_text=_('IPv4 or IPv6 address of IPAM, without the mask'),
    )
    vrf = CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('VRF of the next hops, when the address is in several VRFs'),
    )
    set_aspath_prepend = forms.CharField(
        required=False,
        help_text=_('AS numbers separated by spaces; repeat a number to repeat it'),
    )
    set_community_list = CSVModelChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the community list to set'),
    )
    set_community_mode = CSVChoiceField(
        choices=CommunityModeChoices,
        required=False,
        help_text=_('replace or additive'),
    )
    set_metric_mode = CSVChoiceField(
        choices=MetricModeChoices,
        required=False,
        help_text=_('set (the default), add or subtract'),
    )
    set_origin = CSVChoiceField(
        choices=OriginChoices, required=False, help_text=_('igp, egp or incomplete')
    )

    class Meta:
        model = RoutePolicyEntry
        fields = (
            'route_policy',
            'sequence',
            'action',
            'jump_policy',
            'match_prefix_list',
            'match_aspath',
            'match_community_list',
            'match_next_hop',
            'match_metric',
            'match_origin',
            'match_tag',
            'match_weight',
            'set_local_preference',
            'set_next_hop',
            'set_aspath_prepend',
            'set_community_list',
            'set_community_mode',
            'set_metric',
            'set_metric_mode',
            'set_origin',
            'set_tag',
            'set_weight',
            'description',
            'owner',
            'comments',
            'tags',
        )

    def clean_set_aspath_prepend(self):
        value = self.cleaned_data.get('set_aspath_prepend')
        if not value:
            return []
        numbers = (
            value if isinstance(value, list) else str(value).replace(',', ' ').split()
        )
        try:
            return [int(number) for number in numbers]
        except (TypeError, ValueError):
            raise ValidationError(_('AS numbers separated by spaces.'))

    def _find_address(self, field, vrf):
        value = (self.cleaned_data.get(field) or '').strip()
        if not value:
            return None
        try:
            addresses = IPAddress.objects.filter(address__net_host=value)
            if vrf:
                addresses = addresses.filter(vrf=vrf)
            matches = list(addresses[:2])
        except (ValidationError, ValueError, TypeError):
            self.add_error(
                field, _('"%(value)s" is not a valid address.') % {'value': value}
            )
            return None
        if not matches:
            self.add_error(
                field,
                _('Address %(value)s does not exist in IPAM: create it first.')
                % {'value': value},
            )
        elif len(matches) > 1:
            self.add_error(
                field,
                _('Address %(value)s exists several times in IPAM: set the vrf column.')
                % {'value': value},
            )
        else:
            return matches[0]
        return None

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        vrf = cleaned.get('vrf')
        for field in ('match_next_hop', 'set_next_hop'):
            if field in cleaned:
                cleaned[field] = self._find_address(field, vrf)
        if cleaned.get('sequence') is None and cleaned.get('route_policy'):
            try:
                cleaned['sequence'] = route_policy_helpers.next_sequence(
                    cleaned['route_policy']
                )
            except ValidationError as e:
                self.add_error('sequence', e)
        return cleaned
