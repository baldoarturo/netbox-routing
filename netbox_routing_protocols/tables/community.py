import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable, columns
from netbox_routing_protocols.models.community import *

__all__ = (
    'CommunityTable',
    'CommunityListTable',
    'CommunityListEntryTable',
)

from tenancy.tables import TenancyColumnsMixin


class CommunityTable(TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(verbose_name=_('Name'), linkify=True)
    community = tables.Column(verbose_name=_('Community'), linkify=True)
    type = columns.ChoiceFieldColumn()
    well_known = tables.Column(
        verbose_name=_('Well-known'), orderable=False, empty_values=()
    )
    role = tables.Column(verbose_name=_('Role'), linkify=True)
    status = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(url_name='plugins:netbox_routing_protocols:community_list')

    class Meta(NetBoxTable.Meta):
        model = Community
        fields = (
            'pk',
            'id',
            'name',
            'community',
            'type',
            'well_known',
            'role',
            'status',
            'description',
            'tenant_group',
            'tenant',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'id',
            'name',
            'community',
            'type',
            'well_known',
            'status',
            'description',
            'actions',
        )


class CommunityListTable(TenancyColumnsMixin, NetBoxTable):
    name = tables.Column(verbose_name=_('Name'), linkify=True)
    type = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(
        url_name='plugins:netbox_routing_protocols:communitylist_list'
    )

    class Meta(NetBoxTable.Meta):
        model = CommunityList
        fields = (
            'pk',
            'id',
            'name',
            'type',
            'description',
            'tenant_group',
            'tenant',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'id',
            'name',
            'type',
            'description',
            'actions',
        )


class CommunityListEntryTable(NetBoxTable):
    community_list = tables.Column(verbose_name=_('Community List'), linkify=True)
    community = tables.Column(verbose_name=_('Community'), linkify=True)
    action = columns.ChoiceFieldColumn()
    tags = columns.TagColumn(
        url_name='plugins:netbox_routing_protocols:communitylistentry_list'
    )

    class Meta(NetBoxTable.Meta):
        model = CommunityListEntry
        fields = (
            'pk',
            'id',
            'community_list',
            'sequence',
            'action',
            'community',
            'description',
            'comments',
            'tags',
            'created',
            'last_updated',
            'actions',
        )
        default_columns = (
            'pk',
            'id',
            'community_list',
            'sequence',
            'action',
            'community',
            'description',
            'actions',
        )
