import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTable',
    'ASPathEntryTable',
    'PrefixListTable',
    'PrefixListEntryTable',
    'RoutePolicyTable',
    'RoutePolicyEntryTable',
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


class RoutePolicyTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))

    class Meta(NetBoxTable.Meta):
        model = RoutePolicy
        fields = ('pk', 'id', 'name')
        default_columns = ('pk', 'id', 'name')


class RoutePolicyEntryTable(NetBoxTable):
    route_policy = tables.Column(verbose_name=_('Route Policy'), linkify=True)
    action = columns.ChoiceFieldColumn()
    flow_control = tables.Column(verbose_name=_('Flow Control (Continue)'))
    match_next_hop = tables.Column(verbose_name=_('Match Next Hop'), linkify=True)
    match_origin = tables.Column(verbose_name=_('Match Origin'))
    set_next_hop = tables.Column(verbose_name=_('Set Next Hop'), linkify=True)
    set_aspath_prepend = tables.Column(
        accessor='aspath_prepend_text',
        orderable=False,
        verbose_name=_('Set AS-Path Prepend'),
    )
    set_community_list = tables.Column(
        verbose_name=_('Set Community List'), linkify=True
    )
    set_community_mode = tables.Column(verbose_name=_('Set Community Mode'))
    set_metric_mode = tables.Column(verbose_name=_('Set Metric Mode'))
    set_origin = tables.Column(verbose_name=_('Set Origin'))

    class Meta(NetBoxTable.Meta):
        model = RoutePolicyEntry
        fields = (
            'pk',
            'id',
            'route_policy',
            'sequence',
            'action',
            'flow_control',
            'match_next_hop',
            'match_metric',
            'match_origin',
            'match_tag',
            'match_weight',
            'set_local_preference',
            'set_next_hop',
            'set_aspath_prepend',
            'set_community_list',
            'set_community_mode',
            'set_metric',
            'set_metric_mode',
            'set_origin',
            'set_tag',
            'set_weight',
        )
        default_columns = ('pk', 'id', 'route_policy', 'sequence', 'action')


class ASPathTable(NetBoxTable):
    name = tables.Column(linkify=True, verbose_name=_('Name'))
    entry_count = columns.LinkedCountColumn(
        viewname='plugins:netbox_routing_protocols:aspathentry_list',
        url_params={'aspath_id': 'pk'},
        verbose_name=_('Entries'),
    )
    tags = columns.TagColumn(url_name='plugins:netbox_routing_protocols:aspath_list')

    class Meta(NetBoxTable.Meta):
        model = ASPath
        fields = (
            'pk',
            'id',
            'name',
            'entry_count',
            'description',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = ('pk', 'name', 'entry_count', 'description', 'actions')


class ASPathEntryTable(NetBoxTable):
    aspath = tables.Column(verbose_name=_('AS Path'), linkify=True)
    action = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(
        url_name='plugins:netbox_routing_protocols:aspathentry_list'
    )

    class Meta(NetBoxTable.Meta):
        model = ASPathEntry
        fields = (
            'pk',
            'id',
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'id',
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'actions',
        )
