from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Device
from ipam.models import VRF
from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, add_blank_choice
from utilities.forms.fields import DynamicModelChoiceField, CommentField

from netbox_routing import choices
from netbox_routing.choices.ospf import OSPFAreaTypeChoices
from netbox_routing.constants.ospf import (
    OSPF_COST_MAX,
    OSPF_COST_MIN,
    OSPF_DEAD_INTERVAL_MAX,
    OSPF_EXTERNAL_METRIC_MAX,
    OSPF_EXTERNAL_METRIC_MIN,
    OSPF_TAG_MAX,
    OSPF_DEAD_INTERVAL_MIN,
    OSPF_HELLO_INTERVAL_MAX,
    OSPF_HELLO_INTERVAL_MIN,
    OSPF_RETRANSMIT_INTERVAL_MAX,
    OSPF_RETRANSMIT_INTERVAL_MIN,
    OSPF_STUB_DEFAULT_COST_MAX,
    OSPF_STUB_DEFAULT_COST_MIN,
    OSPF_TRANSMIT_DELAY_MAX,
    OSPF_TRANSMIT_DELAY_MIN,
)
from netbox_routing.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
)

__all__ = (
    'OSPFInterfaceBulkEditForm',
    'OSPFInstanceBulkEditForm',
    'OSPFAreaBulkEditForm',
    'OSPFNetworkBulkEditForm',
    'OSPFRedistributionBulkEditForm',
)

from utilities.forms.rendering import FieldSet


class OSPFInstanceBulkEditForm(NetBoxModelBulkEditForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(), label=_('Device'), required=False, selector=True
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(), label=_('VRF'), required=False, selector=True
    )

    default_originate = forms.ChoiceField(
        label=_('Default Originate'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    default_originate_always = forms.ChoiceField(
        label=_('Default Originate Always'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    default_originate_metric = forms.IntegerField(
        label=_('Default Originate Metric'),
        required=False,
        min_value=OSPF_EXTERNAL_METRIC_MIN,
        max_value=OSPF_EXTERNAL_METRIC_MAX,
    )
    default_originate_metric_type = forms.ChoiceField(
        label=_('Default Originate Metric Type'),
        choices=add_blank_choice(choices.OSPFExternalMetricTypeChoices),
        required=False,
    )

    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFInstance
    fieldsets = (
        FieldSet('device', 'vrf', name='OSPF'),
        FieldSet(
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            name='Default Information',
        ),
        FieldSet(
            'description',
        ),
    )
    nullable_fields = (
        'vrf',
        'default_originate_metric',
        'description',
    )


class OSPFAreaBulkEditForm(NetBoxModelBulkEditForm):
    area_type = forms.ChoiceField(
        label=_('Area Type'), choices=OSPFAreaTypeChoices, required=False
    )
    default_cost = forms.IntegerField(
        label=_('Default Cost'),
        required=False,
        min_value=OSPF_STUB_DEFAULT_COST_MIN,
        max_value=OSPF_STUB_DEFAULT_COST_MAX,
    )
    nssa_translate_always = forms.ChoiceField(
        label=_('Translate Type 7 Always'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    nssa_no_redistribution = forms.ChoiceField(
        label=_('No Redistribution'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    nssa_default_originate = forms.ChoiceField(
        label=_('Default Information Originate'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFArea
    fieldsets = (
        FieldSet('area_type', 'default_cost'),
        FieldSet(
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            name='NSSA',
        ),
        FieldSet('description'),
    )
    nullable_fields = ('default_cost',)


class OSPFInterfaceBulkEditForm(NetBoxModelBulkEditForm):
    instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        label=_('OSPF Instance'),
        required=False,
        selector=True,
    )
    area = DynamicModelChoiceField(
        queryset=OSPFArea.objects.all(),
        label=_('OSPF Area'),
        required=False,
        selector=True,
    )
    network_type = forms.ChoiceField(
        label=_('Network Type'),
        choices=add_blank_choice(choices.OSPFNetworkTypeChoices),
        required=False,
    )
    passive = forms.ChoiceField(
        label=_('Passive'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    priority = forms.IntegerField(label=_('Priority'), required=False)
    cost = forms.IntegerField(
        label=_('Cost'),
        required=False,
        min_value=OSPF_COST_MIN,
        max_value=OSPF_COST_MAX,
    )
    bfd = forms.ChoiceField(
        label=_('BFD'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    mtu_ignore = forms.ChoiceField(
        label=_('MTU Ignore'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    hello_interval = forms.IntegerField(
        label=_('Hello Interval'),
        required=False,
        min_value=OSPF_HELLO_INTERVAL_MIN,
        max_value=OSPF_HELLO_INTERVAL_MAX,
    )
    dead_interval = forms.IntegerField(
        label=_('Dead Interval'),
        required=False,
        min_value=OSPF_DEAD_INTERVAL_MIN,
        max_value=OSPF_DEAD_INTERVAL_MAX,
    )
    retransmit_interval = forms.IntegerField(
        label=_('Retransmit Interval'),
        required=False,
        min_value=OSPF_RETRANSMIT_INTERVAL_MIN,
        max_value=OSPF_RETRANSMIT_INTERVAL_MAX,
    )
    transmit_delay = forms.IntegerField(
        label=_('Transmit Delay'),
        required=False,
        min_value=OSPF_TRANSMIT_DELAY_MIN,
        max_value=OSPF_TRANSMIT_DELAY_MAX,
    )
    authentication = forms.ChoiceField(
        label=_('Authentication'),
        choices=add_blank_choice(choices.AuthenticationChoices),
        required=False,
    )
    passphrase = forms.CharField(label=_('Passphrase'), required=False)

    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFInterface
    fieldsets = (
        FieldSet('instance', 'area', name='OSPF'),
        FieldSet(
            'network_type',
            'passive',
            'priority',
            'cost',
            'bfd',
            'mtu_ignore',
            'authentication',
            'passphrase',
            name='Attributes',
        ),
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            name='Timers',
        ),
        FieldSet('description'),
    )
    nullable_fields = ()


class OSPFNetworkBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFNetwork
    fieldsets = (FieldSet('description'),)
    nullable_fields = ('description',)


class OSPFRedistributionBulkEditForm(NetBoxModelBulkEditForm):
    metric = forms.IntegerField(
        label=_('Metric'),
        required=False,
        min_value=OSPF_EXTERNAL_METRIC_MIN,
        max_value=OSPF_EXTERNAL_METRIC_MAX,
    )
    metric_type = forms.ChoiceField(
        label=_('Metric Type'),
        choices=add_blank_choice(choices.OSPFExternalMetricTypeChoices),
        required=False,
    )
    subnets = forms.ChoiceField(
        label=_('Subnets'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    route_tag = forms.IntegerField(
        label=_('Route Tag'), required=False, min_value=0, max_value=OSPF_TAG_MAX
    )
    route_policy = forms.CharField(
        label=_('Route Policy'), max_length=100, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFRedistribution
    fieldsets = (
        FieldSet('metric', 'metric_type', 'subnets', 'route_tag', 'route_policy'),
        FieldSet('description'),
    )
    nullable_fields = ('metric', 'route_tag', 'route_policy', 'description')
