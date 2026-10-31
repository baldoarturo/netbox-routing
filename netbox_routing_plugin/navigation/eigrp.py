from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('eigrp',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

routers = PluginMenuItem(
    link='plugins:netbox_routing_plugin:eigrprouter_list',
    link_text='Routers',
    permissions=['netbox_routing_plugin.view_eigrprouter'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrprouter_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_eigrprouter'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrprouter_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_eigrprouter'],
        ),
    ),
)
address_families = PluginMenuItem(
    link='plugins:netbox_routing_plugin:eigrpaddressfamily_list',
    link_text='Address Families',
    permissions=['netbox_routing_plugin.view_eigrpaddressfamily'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpaddressfamily_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_eigrpaddressfamily'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpaddressfamily_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_eigrpaddressfamily'],
        ),
    ),
)
networks = PluginMenuItem(
    link='plugins:netbox_routing_plugin:eigrpnetwork_list',
    link_text='Networks',
    permissions=['netbox_routing_plugin.view_eigrpnetwork'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpnetwork_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_eigrpnetwork'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpnetwork_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_eigrpnetwork'],
        ),
    ),
)
interfaces = PluginMenuItem(
    link='plugins:netbox_routing_plugin:eigrpinterface_list',
    link_text='Interfaces',
    permissions=['netbox_routing_plugin.view_eigrpinterface'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpinterface_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_eigrpinterface'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:eigrpinterface_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_eigrpinterface'],
        ),
    ),
)

eigrp = (routers, address_families, networks, interfaces)
