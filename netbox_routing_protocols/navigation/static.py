from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('MENUITEMS',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

static = PluginMenuItem(
    link='plugins:netbox_routing_protocols:staticroute_list',
    link_text='Static Routes',
    permissions=['netbox_routing_protocols.view_staticroute'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:staticroute_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing_protocols.add_staticroute'],
        ),
        PluginMenuButton(
            link='plugins:netbox_routing_protocols:staticroute_bulk_import',
            title='Import',
            icon_class=COL_IMPORT,
            permissions=['netbox_routing_protocols.import_staticroute'],
        ),
    ),
)

MENUITEMS = (static,)
