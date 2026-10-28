from netbox.plugins import PluginMenuItem, PluginMenuButton

__all__ = ('BFD_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'

BFD_MENU = (
    PluginMenuItem(
        link='plugins:netbox_routing_protocols:bfdprofile_list',
        link_text='BFD Profile',
        permissions=['netbox_routing_protocols.view_bfdprofile'],
        buttons=(
            PluginMenuButton(
                link='plugins:netbox_routing_protocols:bfdprofile_add',
                title='Add',
                icon_class=COL_ADD,
                permissions=['netbox_routing_protocols.add_bfdprofile'],
            ),
        ),
    ),
)
