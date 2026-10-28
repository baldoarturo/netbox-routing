from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('MENUITEMS',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

ospf_instance = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfinstance_list',
    link_text='Instances',
    permissions=['netbox_routing_protocols.view_ospfinstance'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfinstance_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfinstance'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfinstance_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_ospfinstance'],
        ),
    ),
)
ospf_area = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfarea_list',
    link_text='Areas',
    permissions=['netbox_routing_protocols.view_ospfarea'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfarea_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfarea'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfarea_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_ospfarea'],
        ),
    ),
)
ospf_interfaces = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfinterface_list',
    link_text='Interfaces',
    permissions=['netbox_routing_protocols.view_ospfinterface'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfinterface_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfinterface'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfinterface_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_ospfinterface'],
        ),
    ),
)

ospf_networks = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfnetwork_list',
    link_text='Networks',
    permissions=['netbox_routing_protocols.view_ospfnetwork'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfnetwork_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfnetwork'],
        ),
    ),
)

ospf_redistributions = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfredistribution_list',
    link_text='Redistribution',
    permissions=['netbox_routing_protocols.view_ospfredistribution'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfredistribution_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfredistribution'],
        ),
    ),
)

ospf_virtual_links = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfvirtuallink_list',
    link_text='Virtual Links',
    permissions=['netbox_routing_protocols.view_ospfvirtuallink'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfvirtuallink_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfvirtuallink'],
        ),
    ),
)

ospf_summary_addresses = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfsummaryaddress_list',
    link_text='Summary Addresses',
    permissions=['netbox_routing_protocols.view_ospfsummaryaddress'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfsummaryaddress_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfsummaryaddress'],
        ),
    ),
)

ospf_neighbors = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfneighbor_list',
    link_text='Neighbors',
    permissions=['netbox_routing_protocols.view_ospfneighbor'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfneighbor_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfneighbor'],
        ),
    ),
)

ospf_area_ranges = PluginMenuItem(
    link='plugins:netbox_routing_protocols:ospfarearange_list',
    link_text='Area Ranges',
    permissions=['netbox_routing_protocols.view_ospfarearange'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:ospfarearange_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_ospfarearange'],
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
