from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('eigrp',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

routers = PluginMenuItem(
    link='plugins:netbox_routing_protocols:eigrprouter_list',
    link_text='Routers',
    permissions=['netbox_routing_protocols.view_eigrprouter'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrprouter_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_eigrprouter'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrprouter_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_eigrprouter'],
        ),
    ),
)
address_families = PluginMenuItem(
    link='plugins:netbox_routing_protocols:eigrpaddressfamily_list',
    link_text='Address Families',
    permissions=['netbox_routing_protocols.view_eigrpaddressfamily'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpaddressfamily_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_eigrpaddressfamily'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpaddressfamily_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_eigrpaddressfamily'],
        ),
    ),
)
networks = PluginMenuItem(
    link='plugins:netbox_routing_protocols:eigrpnetwork_list',
    link_text='Networks',
    permissions=['netbox_routing_protocols.view_eigrpnetwork'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpnetwork_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_eigrpnetwork'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpnetwork_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_eigrpnetwork'],
        ),
    ),
)
interfaces = PluginMenuItem(
    link='plugins:netbox_routing_protocols:eigrpinterface_list',
    link_text='Interfaces',
    permissions=['netbox_routing_protocols.view_eigrpinterface'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpinterface_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_eigrpinterface'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:eigrpinterface_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_eigrpinterface'],
        ),
    ),
)

eigrp = (routers, address_families, networks, interfaces)
