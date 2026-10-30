from ipam.models import VRF
from dcim.models import Device, Interface
from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.choices import StaticRouteNextHopTypeChoices
from netbox_routing_protocols.models import StaticRoute
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from django.utils.translation import gettext_lazy as _

from utilities.forms.rendering import FieldSet
from django import forms


class StaticRouteFilterForm(NetBoxModelFilterSetForm):
    model = StaticRoute
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'device_id',
            'vrf_id',
            'prefix',
            'next_hop',
            'interface_id',
            'next_hop_type',
            'next_hop_vrf_id',
            'next_hop_global',
            'name',
            'family',
            'distance',
            'route_tag',
            'permanent',
            name=_('Route Attributes'),
        ),
    )
    vrf_id = DynamicModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
    )
    prefix = forms.CharField(
        required=False,
        label=_('Prefix'),
    )

    next_hop = forms.CharField(
        required=False,
        label=_('Next Hop'),
    )

    device_id = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )

    name = forms.CharField(
        required=False,
        label=_('Name'),
    )
    interface_id = DynamicModelMultipleChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        label=_('Interface Next Hop'),
    )
    next_hop_type = forms.MultipleChoiceField(
        choices=StaticRouteNextHopTypeChoices,
        required=False,
        label=_('Next Hop Type'),
    )
    next_hop_vrf_id = DynamicModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label=_('Next Hop VRF'),
    )
    next_hop_global = forms.NullBooleanField(
        required=False,
        label=_('Next Hop in the Global Table'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    family = forms.ChoiceField(
        required=False,
        choices=((None, '---------'), (4, 'IPv4'), (6, 'IPv6')),
        label=_('Address family'),
    )
    distance = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=255,
        label=_('Distance'),
    )
    route_tag = forms.IntegerField(
        required=False,
        min_value=0,
        label=_('Route Tag'),
    )
    permanent = forms.NullBooleanField(
        required=False,
        label=_('Permanent'),
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    tag = TagFilterField(model)
