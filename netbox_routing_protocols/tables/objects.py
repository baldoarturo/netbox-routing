import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTable',
    'ASPathEntryTable',
    'PrefixListTable',
    'PrefixListEntryTable',
    'RouteMapTable',
    'RouteMapEntryTable',
)


class PrefixListTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    family = tables.Column(
        accessor='get_family_display', order_by=('family',), verbose_name=_('Family')
    )
    entry_count = columns.LinkedCountColumn(
        viewname='plugins:netbox_routing_protocols:prefixlistentry_list',
        url_params={'prefix_list_id': 'pk'},
        verbose_name=_('Entries'),
    )
    tags = columns.TagColumn(
        url_name='plugins:netbox_routing_protocols:prefixlist_list'
    )

    class Meta(NetBoxTable.Meta):
        model = PrefixList
        fields = (
            'pk',
            'id',
            'name',
            'family',
            'entry_count',
            'description',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'name',
            'family',
            'entry_count',
            'description',
            'actions',
        )


class PrefixListEntryTable(NetBoxTable):
    prefix_list = tables.Column(verbose_name=_('Prefix List'), linkify=True)
    prefix = tables.TemplateColumn(
        template_code=(
            '{% if record.any_prefix %}<span class="badge text-bg-secondary">any</span>'
            '{% else %}<a href="{{ record.prefix.get_absolute_url }}">{{ record.prefix }}</a>'
            '{% endif %}'
        ),
        order_by=('any_prefix', 'prefix'),
        verbose_name=_('Prefix'),
    )
    action = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(
        url_name='plugins:netbox_routing_protocols:prefixlistentry_list'
    )

    class Meta(NetBoxTable.Meta):
        model = PrefixListEntry
        fields = (
            'pk',
            'id',
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'ge',
            'le',
            'description',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'id',
            'prefix_list',
            'sequence',
            'action',
            'prefix',
            'ge',
            'le',
            'description',
            'actions',
        )


class RouteMapTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))

    class Meta(NetBoxTable.Meta):
        model = RouteMap
        fields = ('pk', 'id', 'name')
        default_columns = ('pk', 'id', 'name')


class RouteMapEntryTable(NetBoxTable):
    route_map = tables.Column(verbose_name=_('Route Map'), linkify=True)
    action = columns.ChoiceFieldColumn()
    flow_control = tables.Column(verbose_name=_('Flow Control (Continue)'))

    class Meta(NetBoxTable.Meta):
        model = RouteMapEntry
        fields = ('pk', 'id', 'route_map', 'sequence', 'action', 'flow_control')
        default_columns = ('pk', 'id', 'route_map', 'sequence', 'action')


class ASPathTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))

    class Meta(NetBoxTable.Meta):
        model = ASPath
        fields = ('pk', 'id', 'name')
        default_columns = ('pk', 'id', 'name')


class ASPathEntryTable(NetBoxTable):
    aspath = tables.Column(verbose_name=_('AS Path'), linkify=True)
    action = columns.ChoiceFieldColumn()
    asn = tables.Column(verbose_name=_('ASN'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = ASPathEntry
        fields = (
            'pk',
            'id',
            'aspath',
            'sequence',
            'action',
            'asn',
        )
        default_columns = (
            'pk',
            'id',
            'aspath',
            'sequence',
            'action',
            'asn',
        )
