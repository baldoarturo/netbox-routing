import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable
from netbox_routing.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
    OSPFAreaRange,
)

__all__ = (
    'OSPFAreaTable',
    'OSPFInstanceTable',
    'OSPFInterfaceTable',
    'OSPFNetworkTable',
    'OSPFRedistributionTable',
    'OSPFVirtualLinkTable',
    'OSPFSummaryAddressTable',
    'OSPFNeighborTable',
    'OSPFAreaRangeTable',
)


class OSPFInstanceTable(NetBoxTable):
    device = tables.Column(verbose_name=_('Device'), linkify=True)
    vrf = tables.Column(verbose_name=_('VRF'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = OSPFInstance
        fields = (
            'pk',
            'id',
            'name',
            'router_id',
            'process_id',
            'device',
            'vrf',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            *OSPFInstance.ADVANCED_FIELDS,
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
        )
        default_columns = (
            'pk',
            'id',
            'name',
            'router_id',
            'process_id',
            'device',
        )


class OSPFAreaTable(NetBoxTable):
    instance = tables.Column(verbose_name=_('Instance'), linkify=True)
    device = tables.Column(
        verbose_name=_('Device'), linkify=True, accessor='instance__device'
    )
    area_id = tables.Column(verbose_name=_('Area ID'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = OSPFArea
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'area_id',
            'area_type',
            'default_cost',
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
        )
        default_columns = ('pk', 'id', 'instance', 'area_id', 'area_type')


class OSPFInterfaceTable(NetBoxTable):
    instance = tables.Column(verbose_name=_('Instance'), linkify=True)
    device = tables.Column(
        verbose_name=_('Device'),
        linkify=True,
        accessor='instance__device',
    )
    area = tables.Column(verbose_name=_('Area'), linkify=True)
    interface = tables.Column(verbose_name=_('Interface'), linkify=True)
    mtu = tables.Column(
        verbose_name=_('MTU'), accessor='interface__mtu', orderable=False
    )

    class Meta(NetBoxTable.Meta):
        model = OSPFInterface
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'area',
            'interface',
            'network_type',
            'passive',
            'priority',
            'cost',
            'bfd',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'mtu',
            'mtu_ignore',
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
            'authentication',
            'passphrase',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
            'show_md5',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'area',
            'interface',
            'network_type',
            'passive',
        )


class OSPFNetworkTable(NetBoxTable):
    ospf_interface = tables.Column(verbose_name=_('OSPF Interface'), linkify=True)
    instance = tables.Column(
        verbose_name=_('Instance'),
        linkify=True,
        accessor='ospf_interface__instance',
    )
    area = tables.Column(
        verbose_name=_('Area'), linkify=True, accessor='ospf_interface__area'
    )
    device = tables.Column(
        verbose_name=_('Device'),
        linkify=True,
        accessor='ospf_interface__interface__device',
    )
    ip_address = tables.Column(verbose_name=_('IP Address'), linkify=True)
    subnet = tables.Column(
        verbose_name=_('Subnet'), accessor='ip_address__address', orderable=False
    )

    class Meta(NetBoxTable.Meta):
        model = OSPFNetwork
        fields = (
            'pk',
            'id',
            'instance',
            'area',
            'device',
            'ospf_interface',
            'ip_address',
            'subnet',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'area',
            'ospf_interface',
            'ip_address',
            'subnet',
        )

    def render_subnet(self, record):
        return str(record.subnet)


class OSPFRedistributionTable(NetBoxTable):
    instance = tables.Column(verbose_name=_('Instance'), linkify=True)
    device = tables.Column(
        verbose_name=_('Device'), linkify=True, accessor='instance__device'
    )
    protocol = tables.Column(verbose_name=_('Protocol'))
    source = tables.Column(verbose_name=_('Source'), orderable=False, empty_values=())
    subnets = tables.BooleanColumn(verbose_name=_('Subnets'))

    class Meta(NetBoxTable.Meta):
        model = OSPFRedistribution
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'protocol',
            'source',
            'metric',
            'metric_type',
            'subnets',
            'route_tag',
            'route_policy',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'protocol',
            'source',
            'metric',
            'metric_type',
            'route_policy',
        )

    def render_protocol(self, record):
        return record.get_protocol_display()

    def render_source(self, record):
        return str(record.source) if record.source else '—'


class OSPFVirtualLinkTable(NetBoxTable):
    instance = tables.Column(verbose_name=_('Instance'), linkify=True)
    device = tables.Column(
        verbose_name=_('Device'), linkify=True, accessor='instance__device'
    )
    transit_area = tables.Column(verbose_name=_('Transit Area'), linkify=True)
    remote_router_id = tables.Column(verbose_name=_('Remote Router ID'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = OSPFVirtualLink
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'transit_area',
            'remote_router_id',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'authentication',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'transit_area',
            'remote_router_id',
            'hello_interval',
            'dead_interval',
            'authentication',
        )


class OSPFSummaryAddressTable(NetBoxTable):
    instance = tables.Column(verbose_name=_('Instance'), linkify=True)
    device = tables.Column(
        verbose_name=_('Device'), linkify=True, accessor='instance__device'
    )
    prefix = tables.Column(verbose_name=_('Prefix'), linkify=True)
    not_advertise = tables.BooleanColumn(verbose_name=_('Do Not Advertise'))

    class Meta(NetBoxTable.Meta):
        model = OSPFSummaryAddress
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'prefix',
            'not_advertise',
            'route_tag',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'prefix',
            'not_advertise',
            'route_tag',
        )


class OSPFNeighborTable(NetBoxTable):
    ospf_interface = tables.Column(verbose_name=_('OSPF Interface'), linkify=True)
    instance = tables.Column(
        verbose_name=_('Instance'),
        linkify=True,
        accessor='ospf_interface__instance',
    )
    device = tables.Column(
        verbose_name=_('Device'),
        linkify=True,
        accessor='ospf_interface__interface__device',
    )
    ip_address = tables.Column(verbose_name=_('IP Address'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = OSPFNeighbor
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'ospf_interface',
            'ip_address',
            'priority',
            'poll_interval',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'ospf_interface',
            'ip_address',
            'priority',
            'poll_interval',
        )


class OSPFAreaRangeTable(NetBoxTable):
    area = tables.Column(verbose_name=_('Area'), linkify=True)
    instance = tables.Column(
        verbose_name=_('Instance'), linkify=True, accessor='area__instance'
    )
    device = tables.Column(
        verbose_name=_('Device'), linkify=True, accessor='area__instance__device'
    )
    prefix = tables.Column(verbose_name=_('Prefix'), linkify=True)
    advertise = tables.BooleanColumn(verbose_name=_('Advertise'))

    class Meta(NetBoxTable.Meta):
        model = OSPFAreaRange
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'area',
            'prefix',
            'advertise',
            'description',
        )
        default_columns = ('pk', 'id', 'instance', 'area', 'prefix', 'advertise')
