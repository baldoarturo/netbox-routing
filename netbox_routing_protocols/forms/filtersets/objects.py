from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.choices import IPAddressFamilyChoices
from ipam.models import Prefix
from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.models.objects import *

__all__ = (
    'PrefixListFilterForm',
    'PrefixListEntryFilterForm',
    'RoutePolicyFilterForm',
    'RoutePolicyEntryFilterForm',
    'ASPathFilterForm',
    'ASPathEntryFilterForm',
)


class PrefixListFilterForm(NetBoxModelFilterSetForm):
    model = PrefixList
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('family', name=_('Attributes')),
    )
    family = forms.ChoiceField(
        label=_('Address family'),
        choices=add_blank_choice(IPAddressFamilyChoices),
        required=False,
    )
    tag = TagFilterField(model)


class PrefixListEntryFilterForm(NetBoxModelFilterSetForm):
    model = PrefixListEntry
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('prefix_list_id', 'family', 'action', name=_('Prefix List')),
        FieldSet('prefix_id', 'any_prefix', 'ge', 'le', name=_('Match')),
    )
    prefix_list_id = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        label=_('Prefix List'),
    )
    family = forms.ChoiceField(
        label=_('Address family'),
        choices=add_blank_choice(IPAddressFamilyChoices),
        required=False,
    )
    action = forms.MultipleChoiceField(
        label=_('Action'),
        choices=ActionChoices,
        required=False,
    )
    prefix_id = DynamicModelMultipleChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        label=_('Prefix'),
    )
    any_prefix = forms.NullBooleanField(
        label=_('Any'),
        required=False,
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    ge = forms.IntegerField(label=_('GE'), required=False, min_value=0, max_value=128)
    le = forms.IntegerField(label=_('LE'), required=False, min_value=0, max_value=128)
    tag = TagFilterField(model)


class RoutePolicyFilterForm(NetBoxModelFilterSetForm):
    model = RoutePolicy


class RoutePolicyEntryFilterForm(NetBoxModelFilterSetForm):
    model = RoutePolicyEntry


class ASPathFilterForm(NetBoxModelFilterSetForm):
    model = ASPath
    fieldsets = (FieldSet('q', 'filter_id', 'tag'),)
    tag = TagFilterField(model)


class ASPathEntryFilterForm(NetBoxModelFilterSetForm):
    model = ASPathEntry
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('aspath_id', 'action', 'sequence', 'pattern', name=_('Entry')),
    )
    aspath_id = DynamicModelMultipleChoiceField(
        queryset=ASPath.objects.all(),
        required=False,
        label=_('AS Path'),
    )
    action = forms.MultipleChoiceField(
        label=_('Action'),
        choices=ActionChoices,
        required=False,
    )
    sequence = forms.IntegerField(
        label=_('Sequence'), required=False, min_value=1, max_value=4294967294
    )
    pattern = forms.CharField(label=_('Pattern'), required=False)
    tag = TagFilterField(model)
