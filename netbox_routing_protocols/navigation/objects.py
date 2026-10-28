from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('OBJECT_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

customprefix = PluginMenuItem(
    link='plugins:netbox_routing_protocols:customprefix_list',
    link_text='Custom Prefixes',
    permissions=['netbox_routing_protocols.view_customprefix'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:customprefix_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_customprefix'],
        ),
    ),
)
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
        # PluginMenuButton(
        #     link='plugins:netbox_routing_protocols:prefixlist_bulk_import',
        #     title='Import',
        #     icon_class=COL_IMPORT,
        #     permissions=['netbox_routing_protocols.add_prefixlist'],
        # ),
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
    ),
)
routemap = PluginMenuItem(
    link='plugins:netbox_routing_protocols:routemap_list',
    link_text='Route Maps',
    permissions=['netbox_routing_protocols.view_routemap'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:routemap_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_routemap'],
        ),
    ),
)
routemap_entry = PluginMenuItem(
    link='plugins:netbox_routing_protocols:routemapentry_list',
    link_text='Route Map Entries',
    permissions=['netbox_routing_protocols.view_routemapentry'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:routemapentry_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_routemapentry'],
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
        # PluginMenuButton(
        #     link='plugins:netbox_routing_protocols:aspathentry_bulk_import',
        #     title='Import',
        #     icon_class=COL_IMPORT,
        #     permissions=['netbox_routing_protocols.add_aspathentry'],
        # ),
    ),
)

OBJECT_MENU = (
    customprefix,
    prefixlist,
    prefixlist_entry,
    routemap,
    routemap_entry,
    aspath,
    aspath_entry,
)
