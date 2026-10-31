from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('MENUITEMS',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

ospf_instance = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfinstance_list',
    link_text='Instances',
    permissions=['netbox_routing_plugin.view_ospfinstance'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfinstance_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfinstance'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfinstance_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfinstance'],
        ),
    ),
)
ospf_area = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfarea_list',
    link_text='Areas',
    permissions=['netbox_routing_plugin.view_ospfarea'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfarea_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfarea'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfarea_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfarea'],
        ),
    ),
)
ospf_interfaces = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfinterface_list',
    link_text='Interfaces',
    permissions=['netbox_routing_plugin.view_ospfinterface'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfinterface_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfinterface'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfinterface_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfinterface'],
        ),
    ),
)

ospf_networks = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfnetwork_list',
    link_text='Networks',
    permissions=['netbox_routing_plugin.view_ospfnetwork'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfnetwork_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfnetwork'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfnetwork_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfnetwork'],
        ),
    ),
)

ospf_redistributions = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfredistribution_list',
    link_text='Redistribution',
    permissions=['netbox_routing_plugin.view_ospfredistribution'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfredistribution_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfredistribution'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfredistribution_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfredistribution'],
        ),
    ),
)

ospf_virtual_links = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfvirtuallink_list',
    link_text='Virtual Links',
    permissions=['netbox_routing_plugin.view_ospfvirtuallink'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfvirtuallink_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfvirtuallink'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfvirtuallink_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfvirtuallink'],
        ),
    ),
)

ospf_summary_addresses = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfsummaryaddress_list',
    link_text='Summary Addresses',
    permissions=['netbox_routing_plugin.view_ospfsummaryaddress'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfsummaryaddress_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfsummaryaddress'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfsummaryaddress_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfsummaryaddress'],
        ),
    ),
)

ospf_neighbors = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfneighbor_list',
    link_text='Neighbors',
    permissions=['netbox_routing_plugin.view_ospfneighbor'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfneighbor_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfneighbor'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfneighbor_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfneighbor'],
        ),
    ),
)

ospf_area_ranges = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfarearange_list',
    link_text='Area Ranges',
    permissions=['netbox_routing_plugin.view_ospfarearange'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfarearange_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfarearange'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfarearange_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfarearange'],
        ),
    ),
)

ospf_prefix_sids = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfprefixsid_list',
    link_text='Prefix SIDs',
    permissions=['netbox_routing_plugin.view_ospfprefixsid'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfprefixsid_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfprefixsid'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfprefixsid_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfprefixsid'],
        ),
    ),
)

ospf_authentication_keys = PluginMenuItem(
    link='plugins:netbox_routing_plugin:ospfauthenticationkey_list',
    link_text='Authentication Keys',
    permissions=['netbox_routing_plugin.view_ospfauthenticationkey'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfauthenticationkey_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_plugin.add_ospfauthenticationkey'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_plugin:ospfauthenticationkey_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_plugin.import_ospfauthenticationkey'],
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
    ospf_prefix_sids,
    ospf_authentication_keys,
)
