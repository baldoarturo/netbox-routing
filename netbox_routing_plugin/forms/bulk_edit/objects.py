from django.utils.translation import gettext_lazy as _

from netbox.forms import PrimaryModelBulkEditForm
from django import forms

from utilities.forms import add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing_plugin.choices import (
    ActionChoices,
    MetricModeChoices,
    OriginChoices,
)
from netbox_routing_plugin.models.objects import *

__all__ = (
    'PrefixListBulkEditForm',
    'PrefixListEntryBulkEditForm',
    'RoutePolicyBulkEditForm',
    'RoutePolicyEntryBulkEditForm',
    'ASPathBulkEditForm',
    'ASPathEntryBulkEditForm',
)


class PrefixListBulkEditForm(PrimaryModelBulkEditForm):
    model = PrefixList
    fieldsets = (
        FieldSet(
            'description',
        ),
    )
    nullable_fields = ('description',)


class PrefixListEntryBulkEditForm(PrimaryModelBulkEditForm):
    prefix_list = DynamicModelChoiceField(
        queryset=PrefixList.objects.all(),
        label=_('Prefix List'),
        required=False,
        selector=True,
    )

    action = forms.ChoiceField(
        label=_('Action'),
        choices=add_blank_choice(ActionChoices),
        required=False,
    )
    ge = forms.IntegerField(label=_('GE'), required=False, min_value=0, max_value=128)
    le = forms.IntegerField(label=_('LE'), required=False, min_value=0, max_value=128)

    model = PrefixListEntry
    fieldsets = (
        FieldSet(
            'prefix_list',
            'action',
            'description',
        ),
        FieldSet('ge', 'le', name=_('Filtering')),
    )
    nullable_fields = ('description', 'ge', 'le')


class RoutePolicyBulkEditForm(PrimaryModelBulkEditForm):
    model = RoutePolicy
    fieldsets = (
        FieldSet(
            'description',
        ),
    )
    nullable_fields = ('description',)


class RoutePolicyEntryBulkEditForm(PrimaryModelBulkEditForm):
    route_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        label=_('Route Policy'),
        required=False,
        selector=True,
    )

    action = forms.ChoiceField(
        label=_('Action'),
        choices=add_blank_choice(ActionChoices),
        required=False,
    )
    jump_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        label=_('Jump to Route Policy'),
        required=False,
        selector=True,
    )
    match_metric = forms.IntegerField(
        label=_('Match Metric'), required=False, min_value=0, max_value=4294967295
    )
    match_origin = forms.ChoiceField(
        label=_('Match Origin'),
        choices=add_blank_choice(OriginChoices),
        required=False,
    )
    match_tag = forms.IntegerField(
        label=_('Match Tag'), required=False, min_value=0, max_value=4294967295
    )
    match_weight = forms.IntegerField(
        label=_('Match Weight'), required=False, min_value=0, max_value=65535
    )
    set_local_preference = forms.IntegerField(
        label=_('Set Local Preference'),
        required=False,
        min_value=0,
        max_value=4294967295,
    )
    set_metric = forms.IntegerField(
        label=_('Set Metric'), required=False, min_value=0, max_value=4294967295
    )
    set_metric_mode = forms.ChoiceField(
        label=_('Set Metric Mode'),
        choices=add_blank_choice(MetricModeChoices),
        required=False,
    )
    set_origin = forms.ChoiceField(
        label=_('Set Origin'),
        choices=add_blank_choice(OriginChoices),
        required=False,
    )
    set_tag = forms.IntegerField(
        label=_('Set Tag'), required=False, min_value=0, max_value=4294967295
    )
    set_weight = forms.IntegerField(
        label=_('Set Weight'), required=False, min_value=0, max_value=65535
    )

    model = RoutePolicyEntry
    fieldsets = (
        FieldSet(
            'route_policy',
            'action',
            'jump_policy',
            'description',
        ),
        FieldSet(
            'match_metric',
            'match_origin',
            'match_tag',
            'match_weight',
            name=_('Match'),
        ),
        FieldSet(
            'set_local_preference',
            'set_metric',
            'set_metric_mode',
            'set_origin',
            'set_tag',
            'set_weight',
            name=_('Set'),
        ),
    )
    nullable_fields = (
        'description',
        'jump_policy',
        'match_metric',
        'match_origin',
        'match_tag',
        'match_weight',
        'set_local_preference',
        'set_metric',
        'set_metric_mode',
        'set_origin',
        'set_tag',
        'set_weight',
    )


class ASPathBulkEditForm(PrimaryModelBulkEditForm):
    model = ASPath
    fieldsets = (
        FieldSet(
            'description',
        ),
    )
    nullable_fields = ('description',)


class ASPathEntryBulkEditForm(PrimaryModelBulkEditForm):
    aspath = DynamicModelChoiceField(
        queryset=ASPath.objects.all(),
        label=_('AS Path'),
        required=False,
        selector=True,
    )

    action = forms.ChoiceField(
        label=_('Action'),
        choices=add_blank_choice(ActionChoices),
        required=False,
    )

    model = ASPathEntry
    fieldsets = (
        FieldSet(
            'aspath',
            'action',
            'description',
        ),
    )
    nullable_fields = ('description',)
