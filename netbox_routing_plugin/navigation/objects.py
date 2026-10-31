from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('OBJECT_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

prefixlist = PluginMenuItem(
    link='plugins:netbox_routing_plugin:prefixlist_list',
    link_text='Prefix Lists',
    permissions=['netbox_routing_plugin.view_prefixlist'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:prefixlist_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_prefixlist'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:prefixlist_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_prefixlist'],
        ),
    ),
)
prefixlist_entry = PluginMenuItem(
    link='plugins:netbox_routing_plugin:prefixlistentry_list',
    link_text='Prefix List Entries',
    permissions=['netbox_routing_plugin.view_prefixlistentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:prefixlistentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_prefixlistentry'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:prefixlistentry_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_prefixlistentry'],
        ),
    ),
)
routepolicy = PluginMenuItem(
    link='plugins:netbox_routing_plugin:routepolicy_list',
    link_text='Route Policies',
    permissions=['netbox_routing_plugin.view_routepolicy'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:routepolicy_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_routepolicy'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:routepolicy_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_routepolicy'],
        ),
    ),
)
routepolicy_entry = PluginMenuItem(
    link='plugins:netbox_routing_plugin:routepolicyentry_list',
    link_text='Route Policy Entries',
    permissions=['netbox_routing_plugin.view_routepolicyentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:routepolicyentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_routepolicyentry'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:routepolicyentry_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_routepolicyentry'],
        ),
    ),
)
aspath = PluginMenuItem(
    link='plugins:netbox_routing_plugin:aspath_list',
    link_text='AS Path',
    permissions=['netbox_routing_plugin.view_aspath'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:aspath_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_aspath'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:aspath_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_aspath'],
        ),
    ),
)
aspath_entry = PluginMenuItem(
    link='plugins:netbox_routing_plugin:aspathentry_list',
    link_text='AS Path Entries',
    permissions=['netbox_routing_plugin.view_aspathentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:aspathentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_aspathentry'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:aspathentry_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.add_aspathentry'],
        ),
    ),
)

prefix_match = PluginMenuItem(
    link='plugins:netbox_routing_plugin:prefix_match',
    link_text='Search Prefix Match',
    permissions=['netbox_routing_plugin.view_prefixlistentry'],
)

aspath_match = PluginMenuItem(
    link='plugins:netbox_routing_plugin:aspath_match',
    link_text='Search AS Path Match',
    permissions=['netbox_routing_plugin.view_aspathentry'],
)

routepolicy_match = PluginMenuItem(
    link='plugins:netbox_routing_plugin:routepolicy_match',
    link_text='Search Route Policy Match',
    permissions=['netbox_routing_plugin.view_routepolicyentry'],
)

OBJECT_MENU = (
    prefixlist,
    prefixlist_entry,
    prefix_match,
    routepolicy,
    routepolicy_entry,
    routepolicy_match,
    aspath,
    aspath_entry,
    aspath_match,
)
