from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.choices import IPAddressFamilyChoices
from ipam.models import IPAddress, Prefix
from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.choices import (
    ActionChoices,
    CommunityModeChoices,
    MetricModeChoices,
    OriginChoices,
)
from netbox_routing_protocols.models.community import CommunityList
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
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'match_prefix_list_id',
            'match_aspath_id',
            'match_community_list_id',
            name=_('Matches'),
        ),
    )
    match_prefix_list_id = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        label=_('Prefix List'),
    )
    match_aspath_id = DynamicModelMultipleChoiceField(
        queryset=ASPath.objects.all(),
        required=False,
        label=_('AS Path'),
    )
    match_community_list_id = DynamicModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        label=_('Community List'),
    )
    tag = TagFilterField(model)


class RoutePolicyEntryFilterForm(NetBoxModelFilterSetForm):
    model = RoutePolicyEntry
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('route_policy_id', 'action', 'sequence', name=_('Entry')),
        FieldSet(
            'match_prefix_list_id',
            'match_aspath_id',
            'match_community_list_id',
            'match_next_hop_id',
            'match_metric',
            'match_origin',
            'match_tag',
            'match_weight',
            name=_('Match'),
        ),
        FieldSet(
            'set_local_preference',
            'set_next_hop_id',
            'set_community_list_id',
            'set_community_mode',
            'set_metric',
            'set_metric_mode',
            'set_origin',
            'set_tag',
            'set_weight',
            name=_('Set'),
        ),
    )
    route_policy_id = DynamicModelMultipleChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        label=_('Route Policy'),
    )
    action = forms.MultipleChoiceField(
        label=_('Action'), choices=ActionChoices, required=False
    )
    sequence = forms.IntegerField(
        label=_('Sequence'), required=False, min_value=1, max_value=4294967294
    )
    match_prefix_list_id = DynamicModelMultipleChoiceField(
        queryset=PrefixList.objects.all(), required=False, label=_('Prefix List')
    )
    match_aspath_id = DynamicModelMultipleChoiceField(
        queryset=ASPath.objects.all(), required=False, label=_('AS Path')
    )
    match_community_list_id = DynamicModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        label=_('Community List'),
    )
    match_next_hop_id = DynamicModelMultipleChoiceField(
        queryset=IPAddress.objects.all(), required=False, label=_('Next Hop')
    )
    match_metric = forms.IntegerField(label=_('Metric'), required=False, min_value=0)
    match_origin = forms.MultipleChoiceField(
        label=_('Origin'), choices=OriginChoices, required=False
    )
    match_tag = forms.IntegerField(label=_('Tag'), required=False, min_value=0)
    match_weight = forms.IntegerField(label=_('Weight'), required=False, min_value=0)
    set_local_preference = forms.IntegerField(
        label=_('Local Preference'), required=False, min_value=0
    )
    set_next_hop_id = DynamicModelMultipleChoiceField(
        queryset=IPAddress.objects.all(), required=False, label=_('Next Hop')
    )
    set_community_list_id = DynamicModelMultipleChoiceField(
        queryset=CommunityList.objects.all(),
        required=False,
        label=_('Community List'),
    )
    set_community_mode = forms.MultipleChoiceField(
        label=_('Community Mode'), choices=CommunityModeChoices, required=False
    )
    set_metric = forms.IntegerField(label=_('Metric'), required=False, min_value=0)
    set_metric_mode = forms.MultipleChoiceField(
        label=_('Metric Mode'), choices=MetricModeChoices, required=False
    )
    set_origin = forms.MultipleChoiceField(
        label=_('Origin'), choices=OriginChoices, required=False
    )
    set_tag = forms.IntegerField(label=_('Tag'), required=False, min_value=0)
    set_weight = forms.IntegerField(label=_('Weight'), required=False, min_value=0)
    tag = TagFilterField(model)


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
