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
    OSPF_AUTH_KEY_ID_MAX,
    OSPF_AUTH_KEY_ID_MIN,
    OSPF_DEAD_INTERVAL_MAX,
    OSPF_EXTERNAL_METRIC_MAX,
    OSPF_EXTERNAL_METRIC_MIN,
    OSPF_GRACEFUL_RESTART_PERIOD_MAX,
    OSPF_GRACEFUL_RESTART_PERIOD_MIN,
    OSPF_MAX_LSA_THRESHOLD_MAX,
    OSPF_MAX_LSA_THRESHOLD_MIN,
    OSPF_PRIORITY_MAX,
    OSPF_PRIORITY_MIN,
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
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
)

__all__ = (
    'OSPFInterfaceBulkEditForm',
    'OSPFInstanceBulkEditForm',
    'OSPFAreaBulkEditForm',
    'OSPFNetworkBulkEditForm',
    'OSPFRedistributionBulkEditForm',
    'OSPFVirtualLinkBulkEditForm',
    'OSPFSummaryAddressBulkEditForm',
    'OSPFNeighborBulkEditForm',
)

from utilities.forms.rendering import FieldSet


def _integer(label):
    return forms.IntegerField(label=label, required=False, min_value=0)


def _boolean(label):
    return forms.ChoiceField(
        label=label, choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )


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

    spf_initial_delay = _integer(_('SPF Initial Delay'))
    spf_short_delay = _integer(_('SPF Short Delay'))
    spf_long_delay = _integer(_('SPF Long Delay'))
    spf_time_to_learn = _integer(_('SPF Time to Learn'))
    spf_holddown = _integer(_('SPF Holddown'))
    lsa_min_interval = _integer(_('LSA Minimum Interval'))
    lsa_min_arrival = _integer(_('LSA Minimum Arrival'))
    max_metric_router_lsa = _boolean(_('Max Metric (Stub Router)'))
    max_metric_on_startup = forms.IntegerField(
        label=_('Max Metric On Startup'), required=False, min_value=1
    )
    graceful_restart = forms.ChoiceField(
        label=_('Graceful Restart'),
        choices=add_blank_choice(choices.OSPFGracefulRestartChoices),
        required=False,
    )
    graceful_restart_period = forms.IntegerField(
        label=_('Graceful Restart Period'),
        required=False,
        min_value=OSPF_GRACEFUL_RESTART_PERIOD_MIN,
        max_value=OSPF_GRACEFUL_RESTART_PERIOD_MAX,
    )
    graceful_restart_helper = _boolean(_('Graceful Restart Helper'))
    graceful_restart_helper_strict_lsa_checking = _boolean(_('Strict LSA Checking'))
    rfc1583_compatibility = _boolean(_('RFC 1583 Compatibility'))
    log_adjacency_changes = _boolean(_('Log Adjacency Changes'))
    log_adjacency_changes_detail = _boolean(_('Log Adjacency Changes in Detail'))
    bfd_all_interfaces = _boolean(_('BFD on All Interfaces'))
    passive_interface_default = _boolean(_('Passive Interfaces by Default'))
    max_lsa = forms.IntegerField(label=_('Max LSAs'), required=False, min_value=1)
    max_lsa_threshold = forms.IntegerField(
        label=_('Max LSAs Warning Threshold'),
        required=False,
        min_value=OSPF_MAX_LSA_THRESHOLD_MIN,
        max_value=OSPF_MAX_LSA_THRESHOLD_MAX,
    )
    max_lsa_warning_only = _boolean(_('Max LSAs Warning Only'))
    external_lsdb_limit = _integer(_('External LSDB Limit'))
    exit_overflow_interval = _integer(_('Exit Overflow Interval'))
    reference_bandwidth = forms.IntegerField(
        label=_('Reference Bandwidth'), required=False, min_value=1
    )
    maximum_paths = forms.IntegerField(
        label=_('Maximum Paths'), required=False, min_value=1, max_value=64
    )
    distance_intra_area = forms.IntegerField(
        label=_('Distance (Intra-Area)'), required=False, min_value=1, max_value=255
    )
    distance_inter_area = forms.IntegerField(
        label=_('Distance (Inter-Area)'), required=False, min_value=1, max_value=255
    )
    distance_external = forms.IntegerField(
        label=_('Distance (External)'), required=False, min_value=1, max_value=255
    )
    authentication = forms.ChoiceField(
        label=_('Authentication'),
        choices=add_blank_choice(choices.AuthenticationChoices),
        required=False,
    )
    passphrase = forms.CharField(label=_('Passphrase'), required=False)
    authentication_key_id = forms.IntegerField(
        label=_('Key ID'),
        required=False,
        min_value=OSPF_AUTH_KEY_ID_MIN,
        max_value=OSPF_AUTH_KEY_ID_MAX,
    )
    message_digest_algorithm = forms.ChoiceField(
        label=_('Message Digest Algorithm'),
        choices=add_blank_choice(choices.OSPFMessageDigestAlgorithmChoices),
        required=False,
    )
    key_chain = forms.CharField(label=_('Key Chain'), max_length=100, required=False)
    show_md5 = forms.ChoiceField(
        label=_('MD5 Digest'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
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
        FieldSet(*OSPFInstance.ADVANCED_FIELDS, name='Advanced'),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name='Authentication',
        ),
    )
    nullable_fields = (
        'vrf',
        'default_originate_metric',
        'max_metric_on_startup',
        'max_lsa',
        'external_lsdb_limit',
        'reference_bandwidth',
        'maximum_paths',
        'distance_intra_area',
        'distance_inter_area',
        'distance_external',
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
    authentication = forms.ChoiceField(
        label=_('Authentication'),
        choices=add_blank_choice(choices.AuthenticationChoices),
        required=False,
    )
    passphrase = forms.CharField(label=_('Passphrase'), required=False)
    authentication_key_id = forms.IntegerField(
        label=_('Key ID'),
        required=False,
        min_value=OSPF_AUTH_KEY_ID_MIN,
        max_value=OSPF_AUTH_KEY_ID_MAX,
    )
    message_digest_algorithm = forms.ChoiceField(
        label=_('Message Digest Algorithm'),
        choices=add_blank_choice(choices.OSPFMessageDigestAlgorithmChoices),
        required=False,
    )
    key_chain = forms.CharField(label=_('Key Chain'), max_length=100, required=False)
    show_md5 = forms.ChoiceField(
        label=_('MD5 Digest'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
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
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name='Authentication',
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
    priority = forms.IntegerField(
        label=_('Priority'),
        required=False,
        min_value=OSPF_PRIORITY_MIN,
        max_value=OSPF_PRIORITY_MAX,
    )
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
    prefix_suppression = forms.ChoiceField(
        label=_('Prefix Suppression'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    database_filter_all_out = forms.ChoiceField(
        label=_('Database Filter All Out'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    flood_reduction = forms.ChoiceField(
        label=_('Flood Reduction'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    demand_circuit = forms.ChoiceField(
        label=_('Demand Circuit'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
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
    authentication_key_id = forms.IntegerField(
        label=_('Key ID'),
        required=False,
        min_value=OSPF_AUTH_KEY_ID_MIN,
        max_value=OSPF_AUTH_KEY_ID_MAX,
    )
    message_digest_algorithm = forms.ChoiceField(
        label=_('Message Digest Algorithm'),
        choices=add_blank_choice(choices.OSPFMessageDigestAlgorithmChoices),
        required=False,
    )
    key_chain = forms.CharField(label=_('Key Chain'), max_length=100, required=False)
    show_md5 = forms.ChoiceField(
        label=_('MD5 Digest'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )

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
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
            name='Attributes',
        ),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name='Authentication',
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


class OSPFVirtualLinkBulkEditForm(NetBoxModelBulkEditForm):
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
    authentication_key_id = forms.IntegerField(
        label=_('Key ID'),
        required=False,
        min_value=OSPF_AUTH_KEY_ID_MIN,
        max_value=OSPF_AUTH_KEY_ID_MAX,
    )
    message_digest_algorithm = forms.ChoiceField(
        label=_('Message Digest Algorithm'),
        choices=add_blank_choice(choices.OSPFMessageDigestAlgorithmChoices),
        required=False,
    )
    key_chain = forms.CharField(label=_('Key Chain'), max_length=100, required=False)
    show_md5 = forms.ChoiceField(
        label=_('MD5 Digest'), choices=BOOLEAN_WITH_BLANK_CHOICES, required=False
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFVirtualLink
    fieldsets = (
        FieldSet(
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            name='Timers',
        ),
        FieldSet(
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'passphrase',
            'show_md5',
            'key_chain',
            name='Authentication',
        ),
        FieldSet('description'),
    )
    nullable_fields = ('authentication_key_id', 'description')


class OSPFSummaryAddressBulkEditForm(NetBoxModelBulkEditForm):
    not_advertise = forms.ChoiceField(
        label=_('Do Not Advertise'),
        choices=BOOLEAN_WITH_BLANK_CHOICES,
        required=False,
    )
    route_tag = forms.IntegerField(
        label=_('Route Tag'), required=False, min_value=0, max_value=OSPF_TAG_MAX
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFSummaryAddress
    fieldsets = (
        FieldSet('not_advertise', 'route_tag'),
        FieldSet('description'),
    )
    nullable_fields = ('route_tag', 'description')


class OSPFNeighborBulkEditForm(NetBoxModelBulkEditForm):
    priority = forms.IntegerField(
        label=_('Priority'),
        required=False,
        min_value=OSPF_PRIORITY_MIN,
        max_value=OSPF_PRIORITY_MAX,
    )
    poll_interval = forms.IntegerField(
        label=_('Poll Interval'), required=False, min_value=1
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = OSPFNeighbor
    fieldsets = (
        FieldSet('priority', 'poll_interval'),
        FieldSet('description'),
    )
    nullable_fields = ('priority', 'poll_interval', 'description')
