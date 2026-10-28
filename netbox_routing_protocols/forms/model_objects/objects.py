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
    'CustomPrefixForm',
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
    ipam_prefix = DynamicModelChoiceField(
        queryset=Prefix.objects.all(),
        required=False,
        selector=True,
        label=_('Prefix'),
    )
    custom_prefix = DynamicModelChoiceField(
        queryset=CustomPrefix.objects.all(),
        required=False,
        selector=True,
        quick_add=True,
        label=_('Custom Prefix'),
    )

    fieldsets = (
        FieldSet(
            'prefix_list',
            'sequence',
            'action',
        ),
        FieldSet(
            TabbedGroups(
                FieldSet('ipam_prefix', name=_('Prefix')),
                FieldSet('custom_prefix', name=_('Custom Prefix')),
            ),
            name=_('Prefix'),
        ),
        FieldSet(
            'le',
            'ge',
            name=_('Filtering'),
        ),
        FieldSet(
            'description',
        ),
        FieldSet('tenant_group', 'tenant', name=_('Tenancy')),
    )

    class Meta:
        model = PrefixListEntry
        fields = (
            'prefix_list',
            'sequence',
            'action',
            'ipam_prefix',
            'custom_prefix',
            'le',
            'ge',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):

        # Initialize helper selectors
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {}).copy()
        if instance:
            if type(instance.assigned_prefix) is Prefix:
                initial['ipam_prefix'] = instance.assigned_prefix
            elif type(instance.assigned_prefix) is CustomPrefix:
                initial['custom_prefix'] = instance.assigned_prefix
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        # A field that failed its own validation is missing from cleaned_data and
        # already has its error
        selected_objects = [
            field
            for field in ('ipam_prefix', 'custom_prefix')
            if self.cleaned_data.get(field)
        ]
        if len(selected_objects) > 1:
            raise forms.ValidationError(
                {
                    selected_objects[1]: _(
                        "You can only assign a prefix or a custom prefix."
                    )
                }
            )
        # With none selected the assignment is cleared and the model reports that a
        # prefix is required
        self.instance.assigned_prefix = (
            self.cleaned_data[selected_objects[0]] if selected_objects else None
        )

    def _post_clean(self):
        # Without a valid prefix there is nothing to validate on the model, and its
        # "prefix required" error would only repeat the one the field already has
        if any(f in self.errors for f in ('ipam_prefix', 'custom_prefix')):
            return
        super()._post_clean()


class CustomPrefixForm(PrimaryModelForm):
    fieldsets = (
        FieldSet(
            'prefix',
            'description',
        ),
    )

    class Meta:
        model = CustomPrefix
        fields = (
            'prefix',
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
