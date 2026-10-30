import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable
from tenancy.tables import TenancyColumnsMixin
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceTable',
    'BGPAddressFamilyTable',
    'BGPPeerGroupTable',
    'BGPPeerTable',
    'BGPPeerAddressFamilyTable',
    'BFDProfileTable',
)


class BGPInstanceTable(TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    device = tables.Column(linkify=True, verbose_name=_('Device'))
    vrf = tables.Column(linkify=True, verbose_name=_('VRF'))
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
            'graceful_restart',
            'tenant_group',
            'tenant',
            'description',
            'comments',
        )
        default_columns = ('pk', 'name', 'device', 'vrf', 'asn', 'router_id')


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
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = ('pk', 'id', 'instance', 'address_family', 'maximum_paths')


class _BGPPeerConfigColumns(tables.Table):
    remote_as = tables.Column(linkify=True, verbose_name=_('Remote AS'))
    local_as = tables.Column(linkify=True, verbose_name=_('Local AS'))
    bfd = tables.Column(linkify=True, verbose_name=_('BFD Profile'))


_CONFIG_FIELDS = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ttl',
    'password',
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
            *_CONFIG_FIELDS,
            'tenant_group',
            'tenant',
            'description',
        )
        default_columns = ('pk', 'id', 'name', 'instance', 'remote_as', 'enabled')


class BGPPeerTable(_BGPPeerConfigColumns, TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    instance = tables.Column(linkify=True, verbose_name=_('Instance'))
    peer = tables.Column(linkify=True, verbose_name=_('Peer Address'))
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
    routepolicy_in = tables.Column(linkify=True, verbose_name=_('Route Policy In'))
    routepolicy_out = tables.Column(linkify=True, verbose_name=_('Route Policy Out'))

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
            'routepolicy_in',
            'routepolicy_out',
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
