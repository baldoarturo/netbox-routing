from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'OSPFInstancePanel',
    'OSPFAreaPanel',
    'OSPFInterfacePanel',
    'OSPFInterfaceSettingsPanel',
    'OSPFNetworkPanel',
    'OSPFRedistributionPanel',
)


class OSPFInstancePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    process_id = attrs.NumericAttr('process_id', label=_('Process ID'))
    router_id = attrs.TextAttr('router_id', label=_('Router ID'))
    device = attrs.RelatedObjectAttr('device', label=_('Device'))
    vrf = attrs.RelatedObjectAttr('vrf', linkify=True)
    default_originate = attrs.BooleanAttr(
        'default_originate', label=_('Default Originate')
    )
    default_originate_always = attrs.BooleanAttr(
        'default_originate_always', label=_('Default Originate Always')
    )
    default_originate_metric = attrs.NumericAttr(
        'default_originate_metric', label=_('Default Originate Metric')
    )
    default_originate_metric_type = attrs.ChoiceAttr(
        'default_originate_metric_type', label=_('Default Originate Metric Type')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFAreaPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    area_id = attrs.NumericAttr('area_id', label=_('Area ID'))
    area_type = attrs.ChoiceAttr('area_type', label=_('Area Type'))
    default_cost = attrs.NumericAttr('default_cost', label=_('Default Cost'))
    nssa_translate_always = attrs.BooleanAttr(
        'nssa_translate_always', label=_('Translate Type 7 Always')
    )
    nssa_no_redistribution = attrs.BooleanAttr(
        'nssa_no_redistribution', label=_('No Redistribution')
    )
    nssa_default_originate = attrs.BooleanAttr(
        'nssa_default_originate', label=_('Default Information Originate')
    )
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFInterfacePanel(panels.ObjectAttributesPanel):
    area = attrs.RelatedObjectAttr('area', label=_('Area'))
    device = attrs.RelatedObjectAttr('instance.device', label=_('Device'))
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'))
    interface = attrs.RelatedObjectAttr('interface', label=_('Interface'))


class OSPFInterfaceSettingsPanel(panels.ObjectAttributesPanel):
    priority = attrs.NumericAttr('priority', label=_('Priority'))
    cost = attrs.NumericAttr('cost', label=_('Cost'))
    hello_interval = attrs.NumericAttr('hello_interval', label=_('Hello Interval'))
    dead_interval = attrs.NumericAttr('dead_interval', label=_('Dead Interval'))
    retransmit_interval = attrs.NumericAttr(
        'retransmit_interval', label=_('Retransmit Interval')
    )
    transmit_delay = attrs.NumericAttr('transmit_delay', label=_('Transmit Delay'))
    mtu = attrs.NumericAttr('interface.mtu', label=_('MTU'))
    mtu_ignore = attrs.BooleanAttr('mtu_ignore', label=_('MTU Ignore'))
    network_type = attrs.ChoiceAttr('network_type', label=_('Network Type'))
    passive = attrs.BooleanAttr('passive', label=_('Passive'))
    bfd = attrs.BooleanAttr('bfd', label=_('BFD'))
    authentication = attrs.ChoiceAttr('authentication', label=_('Authentication'))
    passphrase = attrs.TextAttr('passphrase', label=_('Passphrase'))


class OSPFNetworkPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr(
        'ospf_interface.instance', label=_('Instance'), linkify=True
    )
    area = attrs.RelatedObjectAttr('ospf_interface.area', label=_('Area'), linkify=True)
    ospf_interface = attrs.RelatedObjectAttr(
        'ospf_interface', label=_('OSPF Interface'), linkify=True
    )
    ip_address = attrs.RelatedObjectAttr(
        'ip_address', label=_('IP Address'), linkify=True
    )
    subnet = attrs.TextAttr('subnet', label=_('Subnet'))
    description = attrs.TextAttr('description', label=_('Description'))


class OSPFRedistributionPanel(panels.ObjectAttributesPanel):
    instance = attrs.RelatedObjectAttr('instance', label=_('Instance'), linkify=True)
    protocol = attrs.ChoiceAttr('protocol', label=_('Protocol'))
    source = attrs.TextAttr('source', label=_('Source'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    metric_type = attrs.ChoiceAttr('metric_type', label=_('Metric Type'))
    subnets = attrs.BooleanAttr('subnets', label=_('Subnets'))
    route_tag = attrs.NumericAttr('route_tag', label=_('Route Tag'))
    route_policy = attrs.TextAttr('route_policy', label=_('Route Policy'))
    description = attrs.TextAttr('description', label=_('Description'))
