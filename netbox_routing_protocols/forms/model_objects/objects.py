from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix
from netbox.context import current_request
from netbox.forms import PrimaryModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import TabbedGroups, FieldSet

from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.forms.widgets import InlineRadioSelect
from netbox_routing_protocols.helpers.prefix_list import (
    SEQUENCE_STEP,
    any_le,
    find_overlaps,
    next_sequence,
)
from netbox_routing_protocols.models.community import Community, CommunityList
from netbox_routing_protocols.models.objects import *

# How many overlapping entries are named in the warnings after saving an entry
MAX_WARNINGS = 5

__all__ = (
    'PrefixListForm',
    'PrefixListEntryForm',
    'RouteMapForm',
    'RouteMapEntryForm',
    'ASPathForm',
    'ASPathEntryForm',
)


class ASPathForm(PrimaryModelForm):
    class Meta:
        model = ASPath
        fields = (
            'name',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ASPathEntryForm(PrimaryModelForm):
    class Meta:
        model = ASPathEntry
        fields = (
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'comments',
            'tags',
            'owner',
        )


class PrefixListForm(PrimaryModelForm):
    """
    The family is chosen once: the form shows it read only when editing.
    """

    class Meta:
        model = PrefixList
        fields = (
            'name',
            'family',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {'family': InlineRadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The address family cannot be changed once the list exists
        if self.instance.pk:
            self.fields['family'].disabled = True
            self.fields['family'].help_text = _(
                'The address family cannot be changed once defined.'
            )


class PrefixListEntryForm(PrimaryModelForm):
    """
    Empty sequence takes the next one (new entries only), `eq` fills ge and le, Any with no
    length matches everything, and overlaps with other entries are flashed as warnings.
    """

    prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        selector=True,
        label=_('Prefix'),
        help_text=_('Declare the prefix in IPAM first, or select Any.'),
    )
    eq = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=128,
        label=_('Exact length'),
        help_text=_('Match only prefixes of this length: sets GE and LE to it.'),
    )

    fieldsets = (
        FieldSet(
            'prefix_list',
            'sequence',
            'action',
        ),
        FieldSet('prefix', 'any_prefix', name=_('Prefix')),
        FieldSet(
            'ge',
            'le',
            'eq',
            name=_('Filtering'),
        ),
        FieldSet(
            'description',
            'tags',
            'owner',
        ),
    )

    class Meta:
        model = PrefixListEntry
        fields = (
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'any_prefix',
            'ge',
            'le',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A new entry gets the next sequence number of the list, suggested here when
        # the list is known (the add button of the list) and assigned on save otherwise
        # A new entry permits unless told otherwise
        if not self.instance.pk:
            self.fields['action'].initial = ActionChoices.PERMIT
        # Only for a new entry: emptying it on an existing one would silently move the
        # entry to the end of the list
        if not self.instance.pk:
            sequence = self.fields['sequence']
            sequence.required = False
            sequence.help_text = _(
                'Leave empty to use the next one of the list (steps of %(step)s).'
            ) % {'step': SEQUENCE_STEP}
        if not self.instance.pk and not self.initial.get('sequence'):
            prefix_list = str(self.initial.get('prefix_list') or '')
            prefix_list = (
                PrefixList.objects.filter(pk=prefix_list).first()
                if prefix_list.isdigit()
                else None
            )
            if prefix_list:
                try:
                    self.initial['sequence'] = next_sequence(prefix_list)
                except ValidationError:
                    pass

    def clean(self):
        super().clean()
        cleaned = self.cleaned_data
        ge, le, eq = (cleaned.get(field) for field in ('ge', 'le', 'eq'))

        if cleaned.get('sequence') is None and cleaned.get('prefix_list'):
            try:
                cleaned['sequence'] = next_sequence(cleaned['prefix_list'])
            except ValidationError as e:
                raise forms.ValidationError({'sequence': e.messages})

        if eq is not None:
            if ge is not None or le is not None:
                raise forms.ValidationError(
                    {'eq': _('Use either the exact length, or GE and LE.')}
                )
            cleaned['ge'] = cleaned['le'] = eq
            ge = le = eq

        # Any with no length given matches any prefix: LE is the longest length
        prefix_list = cleaned.get('prefix_list')
        if cleaned.get('any_prefix') and prefix_list and ge is None and le is None:
            cleaned['le'] = any_le(prefix_list.family)

    def _post_clean(self):
        # Without a valid prefix there is nothing to validate on the model, and its
        # "prefix required" error would only repeat the one the field already has
        if 'prefix' in self.errors:
            return
        super()._post_clean()

    def save(self, commit=True):
        entry = super().save(commit)
        if commit:
            self._warn_about_overlaps(entry)
        return entry

    @staticmethod
    def _warn_about_overlaps(entry):
        # The entry is saved anyway: overlaps are legitimate, the user is just told
        request = current_request.get()
        if request is None:
            return
        overlaps = find_overlaps(entry)
        for overlap in overlaps[:MAX_WARNINGS]:
            messages.warning(request, overlap.message + '.')
        if len(overlaps) > MAX_WARNINGS:
            messages.warning(
                request,
                f'{len(overlaps) - MAX_WARNINGS} more overlapping entries in the prefix list.',
            )


class RouteMapForm(PrimaryModelForm):
    class Meta:
        model = RouteMap
        fields = (
            'name',
            'description',
            'comments',
            'tags',
            'owner',
        )


class RouteMapEntryForm(PrimaryModelForm):
    flow_control = forms.IntegerField(
        required=False,
        label=_("Continue"),
        help_text=_("None = Not enabled; 0 = Next Entry; >0 = Sequence Number"),
    )
    match_community = DynamicModelMultipleChoiceField(
        queryset=Community.objects.all(),
        required=False,
        selector=True,
        label=_('Match Community'),
    )
    match_community_list = DynamicModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        selector=True,
        label=_('Match Community List'),
    )
    match_prefix_list = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        selector=True,
        label=_('Match Prefix List'),
    )
    match_aspath = DynamicModelMultipleChoiceField(
        queryset=ASPath.objects.all(),
        required=False,
        selector=True,
        label=_('Match AS-Path'),
    )

    fieldsets = (
        FieldSet(
            'route_map',
            'sequence',
            'action',
        ),
        FieldSet(
            TabbedGroups(
                FieldSet('flow_control', name=_('Flow Control')),
                FieldSet(
                    'match_prefix_list',
                    'match_community_list',
                    'match_community',
                    'match_aspath',
                    'match',
                    name=_('Match'),
                ),
                FieldSet('set', name=_('Set')),
            ),
        ),
    )

    class Meta:
        model = RouteMapEntry
        fields = (
            'route_map',
            'sequence',
            'action',
            'flow_control',
            'match_prefix_list',
            'match_community_list',
            'match_community',
            'match_aspath',
            'match',
            'set',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def save(self, commit=True):
        result = super().save(commit)

        self.instance.match_community.set(self.cleaned_data['match_community'])
        self.instance.match_community_list.set(
            self.cleaned_data['match_community_list']
        )
        self.instance.match_prefix_list.set(self.cleaned_data['match_prefix_list'])
        self.instance.match_aspath.set(self.cleaned_data['match_aspath'])

        return result
