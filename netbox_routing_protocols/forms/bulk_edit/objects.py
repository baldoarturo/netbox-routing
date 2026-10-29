from django.utils.translation import gettext_lazy as _

from netbox.forms import PrimaryModelBulkEditForm
from django import forms

from utilities.forms import add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.models.objects import *

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

    model = RoutePolicyEntry
    fieldsets = (
        FieldSet(
            'route_policy',
            'description',
        ),
    )
    nullable_fields = ('description',)


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
