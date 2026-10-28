from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('MENUITEMS',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

ospf_instance = PluginMenuItem(
    link='plugins:netbox_routing:ospfinstance_list',
    link_text='Instances',
    permissions=['netbox_routing.view_ospfinstance'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfinstance_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfinstance'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing:ospfinstance_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing.import_ospfinstance'],
        ),
    ),
)
ospf_area = PluginMenuItem(
    link='plugins:netbox_routing:ospfarea_list',
    link_text='Areas',
    permissions=['netbox_routing.view_ospfarea'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfarea_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfarea'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing:ospfarea_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing.import_ospfarea'],
        ),
    ),
)
ospf_interfaces = PluginMenuItem(
    link='plugins:netbox_routing:ospfinterface_list',
    link_text='Interfaces',
    permissions=['netbox_routing.view_ospfinterface'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfinterface_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfinterface'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing:ospfinterface_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing.import_ospfinterface'],
        ),
    ),
)

ospf_networks = PluginMenuItem(
    link='plugins:netbox_routing:ospfnetwork_list',
    link_text='Networks',
    permissions=['netbox_routing.view_ospfnetwork'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfnetwork_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfnetwork'],
        ),
    ),
)

ospf_redistributions = PluginMenuItem(
    link='plugins:netbox_routing:ospfredistribution_list',
    link_text='Redistribution',
    permissions=['netbox_routing.view_ospfredistribution'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfredistribution_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfredistribution'],
        ),
    ),
)

ospf_virtual_links = PluginMenuItem(
    link='plugins:netbox_routing:ospfvirtuallink_list',
    link_text='Virtual Links',
    permissions=['netbox_routing.view_ospfvirtuallink'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfvirtuallink_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfvirtuallink'],
        ),
    ),
)

ospf_summary_addresses = PluginMenuItem(
    link='plugins:netbox_routing:ospfsummaryaddress_list',
    link_text='Summary Addresses',
    permissions=['netbox_routing.view_ospfsummaryaddress'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfsummaryaddress_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfsummaryaddress'],
        ),
    ),
)

ospf_neighbors = PluginMenuItem(
    link='plugins:netbox_routing:ospfneighbor_list',
    link_text='Neighbors',
    permissions=['netbox_routing.view_ospfneighbor'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfneighbor_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfneighbor'],
        ),
    ),
)

ospf_area_ranges = PluginMenuItem(
    link='plugins:netbox_routing:ospfarearange_list',
    link_text='Area Ranges',
    permissions=['netbox_routing.view_ospfarearange'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:ospfarearange_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_ospfarearange'],
        ),
    ),
)

MENUITEMS = (
    ospf_instance,
    ospf_area,
    ospf_interfaces,
    ospf_networks,
    ospf_redistributions,
    ospf_virtual_links,
    ospf_summary_addresses,
    ospf_neighbors,
    ospf_area_ranges,
)
