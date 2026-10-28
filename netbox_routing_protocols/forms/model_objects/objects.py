from django import forms
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix
from netbox.forms import PrimaryModelForm
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import TabbedGroups, FieldSet

from netbox_routing_protocols.models.community import Community, CommunityList
from netbox_routing_protocols.models.objects import *

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
        widgets = {'family': forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The address family cannot be changed once the list exists
        if self.instance.pk:
            self.fields['family'].disabled = True
            self.fields['family'].help_text = _(
                'The address family cannot be changed once defined.'
            )


class PrefixListEntryForm(PrimaryModelForm):
    prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        selector=True,
        label=_('Prefix'),
        help_text=_('Declare the prefix in IPAM first.'),
    )

    fieldsets = (
        FieldSet(
            'prefix_list',
            'sequence',
            'action',
        ),
        FieldSet('prefix', name=_('Prefix')),
        FieldSet(
            'ge',
            'le',
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
            'ge',
            'le',
            'description',
            'comments',
            'tags',
            'owner',
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
