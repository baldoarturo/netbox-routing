import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from netbox.tables.columns import ChoiceFieldColumn
from netbox_routing_protocols.models import StaticRoute


class StaticRouteTable(NetBoxTable):
    devices = tables.ManyToManyColumn(
        verbose_name=_('Devices'),
        linkify_item=True,
    )
    vrf = tables.Column(
        verbose_name=_('VRF'),
        linkify=True,
    )

    interface = tables.Column(
        verbose_name=_('Interface Next Hop'),
        linkify=True,
    )
    next_hop_type = ChoiceFieldColumn(verbose_name=_('Next Hop Type'))
    next_hop_vrf = tables.Column(
        verbose_name=_('Next Hop VRF'),
        linkify=True,
    )
    next_hop_global = columns.BooleanColumn(
        verbose_name=_('Next Hop in the Global Table'),
    )

    class Meta(NetBoxTable.Meta):
        model = StaticRoute
        fields = (
            'pk',
            'id',
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'interface',
            'next_hop_type',
            'next_hop_vrf',
            'next_hop_global',
            'name',
            'distance',
            'permanent',
            'tag',
            'description',
            'comments',
        )
        default_columns = (
            'pk',
            'id',
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'interface',
            'next_hop_type',
            'name',
        )
