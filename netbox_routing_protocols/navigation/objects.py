from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('OBJECT_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

prefixlist = PluginMenuItem(
    link='plugins:netbox_routing_protocols:prefixlist_list',
    link_text='Prefix Lists',
    permissions=['netbox_routing_protocols.view_prefixlist'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:prefixlist_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_prefixlist'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:prefixlist_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.add_prefixlist'],
        ),
    ),
)
prefixlist_entry = PluginMenuItem(
    link='plugins:netbox_routing_protocols:prefixlistentry_list',
    link_text='Prefix List Entries',
    permissions=['netbox_routing_protocols.view_prefixlistentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:prefixlistentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_prefixlistentry'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:prefixlistentry_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.add_prefixlistentry'],
        ),
    ),
)
routepolicy = PluginMenuItem(
    link='plugins:netbox_routing_protocols:routepolicy_list',
    link_text='Route Policies',
    permissions=['netbox_routing_protocols.view_routepolicy'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:routepolicy_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_routepolicy'],
        ),
    ),
)
routepolicy_entry = PluginMenuItem(
    link='plugins:netbox_routing_protocols:routepolicyentry_list',
    link_text='Route Policy Entries',
    permissions=['netbox_routing_protocols.view_routepolicyentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:routepolicyentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_routepolicyentry'],
        ),
    ),
)
aspath = PluginMenuItem(
    link='plugins:netbox_routing_protocols:aspath_list',
    link_text='AS Path',
    permissions=['netbox_routing_protocols.view_aspath'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:aspath_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_aspath'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:aspath_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.add_aspath'],
        ),
    ),
)
aspath_entry = PluginMenuItem(
    link='plugins:netbox_routing_protocols:aspathentry_list',
    link_text='AS Path Entries',
    permissions=['netbox_routing_protocols.view_aspathentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:aspathentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_aspathentry'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:aspathentry_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.add_aspathentry'],
        ),
    ),
)

prefix_match = PluginMenuItem(
    link='plugins:netbox_routing_protocols:prefix_match',
    link_text='Search Prefix Match',
    permissions=['netbox_routing_protocols.view_prefixlistentry'],
)

OBJECT_MENU = (
    prefixlist,
    prefixlist_entry,
    prefix_match,
    routepolicy,
    routepolicy_entry,
    aspath,
    aspath_entry,
)
