from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import VRF
from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    CommentField,
)
from utilities.forms.rendering import FieldSet

from netbox_routing_protocols.models import StaticRoute

__all__ = ('StaticRouteBulkEditForm',)


class StaticRouteBulkEditForm(NetBoxModelBulkEditForm):
    devices = DynamicModelMultipleChoiceField(
        label='Device',
        queryset=Device.objects.all(),
        required=False,
        selector=True,
    )
    vrf = DynamicModelChoiceField(
        label='VRF',
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
    )
    name = forms.CharField(label=_('Name'), max_length=50, required=False)
    interface_next_hop = forms.CharField(
        label=_('Interface Next Hop'), max_length=100, required=False
    )
    distance = forms.IntegerField(
        label=_('Distance'), min_value=1, max_value=255, required=False
    )
    tag = forms.IntegerField(label=_('Route Tag'), required=False)
    permanent = forms.ChoiceField(
        label=_('Permanent'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )

    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = StaticRoute
    fieldsets = (
        FieldSet('devices', 'vrf', 'interface_next_hop', name='Route'),
        FieldSet('name', 'distance', 'tag', 'permanent', name='Attributes'),
        FieldSet(
            'description',
        ),
    )
    nullable_fields = (
        'devices',
        'vrf',
        'name',
        'interface_next_hop',
        'tag',
        'description',
        'comments',
    )
