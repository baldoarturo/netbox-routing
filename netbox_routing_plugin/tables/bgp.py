import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from tenancy.tables import TenancyColumnsMixin
from netbox_routing_plugin.models.bgp import *

__all__ = (
    'BGPInstanceTable',
    'BGPAddressFamilyTable',
    'BGPPeerGroupTable',
    'BGPListenRangeTable',
    'BGPRedistributionTable',
    'BGPOriginatedNetworkTable',
    'BGPAggregateTable',
    'BGPPeerTable',
    'BGPPeerAddressFamilyTable',
    'BFDProfileTable',
)


class BGPInstanceTable(TenancyColumnsMixin, NetBoxTable):
    router_id = tables.Column(verbose_name=_('Router ID'), linkify=True)
    address_family = tables.Column(
        accessor='pk',
        verbose_name=_('Address Family'),
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    def render_address_family(self, record):
        return ', '.join(
            af.get_address_family_display() for af in record.address_families.all()
        )

    name = tables.Column(linkify=True, verbose_name=_('Name'))
    import_policy = tables.Column(linkify=True, verbose_name=_('Import Policy'))
    export_policy = tables.Column(linkify=True, verbose_name=_('Export Policy'))
    device = tables.Column(linkify=True, verbose_name=_('Device'))
    vrf = tables.Column(accessor='pk', linkify=True, verbose_name=_('VRF'))
    asn = tables.Column(linkify=True, verbose_name=_('ASN'))

    class Meta(NetBoxTable.Meta):
        model = BGPInstance
        fields = (
            'pk',
            'id',
            'name',
            'device',
            'vrf',
            'asn',
            'router_id',
            'asdot',
            'cluster_id',
            'confederation_identifier',
            'graceful_restart',
            'graceful_restart_time',
            'graceful_restart_stale_time',
            'graceful_restart_helper_only',
            'import_policy',
            'export_policy',
            'tenant_group',
            'tenant',
            'description',
            'comments',
        )
        default_columns = (
            'name',
            'device',
            'router_id',
            'vrf',
            'address_family',
            'asn',
        )


class BGPAddressFamilyTable(TenancyColumnsMixin, NetBoxTable):
    instance = tables.Column(linkify=True, verbose_name=_('Instance'))
    address_family = tables.Column(linkify=True, verbose_name=_('Address Family'))
    device = tables.Column(
        linkify=True, accessor='instance__device', verbose_name=_('Device')
    )
    vrf = tables.Column(linkify=True, accessor='instance__vrf', verbose_name=_('VRF'))

    class Meta(NetBoxTable.Meta):
        model = BGPAddressFamily
        fields = (
            'pk',
            'id',
            'instance',
            'device',
            'vrf',
            'address_family',
            'maximum_paths',
            'default_metric',
            'default_originate',
            'auto_summary',
            'distance_ebgp',
            'distance_ibgp',
            'additional_paths_send',
            'additional_paths_receive',
            'additional_paths_install',
            'long_lived_stale_time',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = ('pk', 'id', 'instance', 'address_family', 'maximum_paths')


class _BGPPeerConfigColumns(tables.Table):
    remote_as = tables.Column(linkify=True, verbose_name=_('Remote AS'))
    local_as = tables.Column(linkify=True, verbose_name=_('Local AS'))
    bfd = tables.Column(linkify=True, verbose_name=_('BFD Profile'))
    import_policy = tables.Column(linkify=True, verbose_name=_('Import Policy'))
    export_policy = tables.Column(linkify=True, verbose_name=_('Export Policy'))


_CONFIG_FIELDS = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ebgp_multihop',
    'ttl_security_hops',
    'passive',
    'as_override',
    'soft_reconfiguration_inbound',
    'graceful_shutdown',
    'import_policy',
    'export_policy',
    'passphrase',
    'show_md5',
    'route_reflector_client',
    'extended_nexthop',
    'keepalive',
    'hold_time',
)


class BGPPeerGroupTable(_BGPPeerConfigColumns, TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    instance = tables.Column(linkify=True, verbose_name=_('Instance'))

    class Meta(NetBoxTable.Meta):
        model = BGPPeerGroup
        fields = (
            'pk',
            'id',
            'name',
            'instance',
            'listen_limit',
            *_CONFIG_FIELDS,
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = ('pk', 'id', 'name', 'instance', 'remote_as', 'enabled')


class BGPRedistributionTable(TenancyColumnsMixin, NetBoxTable):
    instance = tables.Column(
        linkify=True, accessor='address_family__instance', verbose_name=_('Instance')
    )
    address_family = tables.Column(linkify=True, verbose_name=_('Address Family'))
    protocol = tables.Column(linkify=True, verbose_name=_('Protocol'))
    source = tables.Column(linkify=True, orderable=False, verbose_name=_('Source'))
    route_policy = tables.Column(linkify=True, verbose_name=_('Route Policy'))
    ospf_match = tables.Column(
        accessor='ospf_match_display',
        orderable=False,
        verbose_name=_('OSPF Route Types'),
    )

    class Meta(NetBoxTable.Meta):
        model = BGPRedistribution
        fields = (
            'pk',
            'id',
            'instance',
            'address_family',
            'protocol',
            'source',
            'metric',
            'route_policy',
            'ospf_match',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'address_family',
            'protocol',
            'source',
            'metric',
            'route_policy',
        )


class BGPOriginatedNetworkTable(TenancyColumnsMixin, NetBoxTable):
    instance = tables.Column(
        linkify=True, accessor='address_family__instance', verbose_name=_('Instance')
    )
    address_family = tables.Column(linkify=True, verbose_name=_('Address Family'))
    prefix = tables.Column(linkify=True, verbose_name=_('Prefix'))

    class Meta(NetBoxTable.Meta):
        model = BGPOriginatedNetwork
        fields = (
            'pk',
            'id',
            'instance',
            'address_family',
            'prefix',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = ('pk', 'id', 'instance', 'address_family', 'prefix')


class BGPAggregateTable(TenancyColumnsMixin, NetBoxTable):
    instance = tables.Column(
        linkify=True, accessor='address_family__instance', verbose_name=_('Instance')
    )
    address_family = tables.Column(linkify=True, verbose_name=_('Address Family'))
    prefix = tables.Column(linkify=True, verbose_name=_('Prefix'))
    summary_only = columns.BooleanColumn(verbose_name=_('Summary Only'))
    as_set = columns.BooleanColumn(verbose_name=_('AS Set'))

    class Meta(NetBoxTable.Meta):
        model = BGPAggregate
        fields = (
            'pk',
            'id',
            'instance',
            'address_family',
            'prefix',
            'summary_only',
            'as_set',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'instance',
            'address_family',
            'prefix',
            'summary_only',
            'as_set',
        )


class BGPListenRangeTable(NetBoxTable):
    peer_group = tables.Column(linkify=True, verbose_name=_('Peer Group'))
    instance = tables.Column(
        linkify=True, accessor='peer_group__instance', verbose_name=_('Instance')
    )
    prefix = tables.Column(linkify=True, verbose_name=_('Prefix'))

    class Meta(NetBoxTable.Meta):
        model = BGPListenRange
        fields = ('pk', 'id', 'peer_group', 'instance', 'prefix', 'description')
        default_columns = ('pk', 'id', 'peer_group', 'instance', 'prefix')


class BGPPeerTable(_BGPPeerConfigColumns, TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    instance = tables.Column(linkify=True, verbose_name=_('Instance'))
    peer = tables.Column(linkify=True, verbose_name=_('Peer Address'))
    interface = tables.Column(linkify=True, verbose_name=_('Interface'))
    source = tables.Column(linkify=True, verbose_name=_('Source Address'))
    peer_group = tables.Column(linkify=True, verbose_name=_('Peer Group'))

    class Meta(NetBoxTable.Meta):
        model = BGPPeer
        fields = (
            'pk',
            'id',
            'name',
            'instance',
            'peer',
            'interface',
            'source',
            'peer_group',
            *_CONFIG_FIELDS,
            'status',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'name',
            'instance',
            'peer',
            'interface',
            'peer_group',
            'remote_as',
            'enabled',
            'status',
        )


class BGPPeerAddressFamilyTable(TenancyColumnsMixin, NetBoxTable):
    peer = tables.Column(linkify=True, verbose_name=_('Peer'))
    peer_group = tables.Column(linkify=True, verbose_name=_('Peer Group'))
    address_family = tables.Column(linkify=True, verbose_name=_('Address Family'))
    prefixlist_in = tables.Column(linkify=True, verbose_name=_('Prefix List In'))
    prefixlist_out = tables.Column(linkify=True, verbose_name=_('Prefix List Out'))
    import_policy = tables.Column(linkify=True, verbose_name=_('Import Policy'))
    export_policy = tables.Column(linkify=True, verbose_name=_('Export Policy'))
    send_community = tables.Column(
        accessor='send_community_display',
        orderable=False,
        verbose_name=_('Send Community'),
    )

    class Meta(NetBoxTable.Meta):
        model = BGPPeerAddressFamily
        fields = (
            'pk',
            'id',
            'peer',
            'peer_group',
            'address_family',
            'enabled',
            'prefixlist_in',
            'prefixlist_out',
            'import_policy',
            'export_policy',
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            'maximum_prefix',
            'maximum_prefix_warning',
            'maximum_prefix_action',
            'maximum_prefix_restart',
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'peer',
            'peer_group',
            'address_family',
            'enabled',
        )


class BFDProfileTable(TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))

    class Meta(NetBoxTable.Meta):
        model = BFDProfile
        fields = (
            'pk',
            'id',
            'name',
            'min_rx_int',
            'min_tx_int',
            'multiplier',
            'hold',
            'tenant',
        )
        default_columns = (
            'pk',
            'id',
            'name',
        )
