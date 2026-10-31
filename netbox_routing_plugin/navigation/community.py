from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('COMMUNITY_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'


def build_menus():
    menus = []
    menu_items = (
        ('communitylist', 'Community List'),
        ('community', 'Community'),
        ('communitylistentry', 'Community List Entry'),
    )
    for model, name in menu_items:
        menu = PluginMenuItem(
            link=f'plugins:netbox_routing_plugin:{model}_list',
            link_text=f'{name}',
            permissions=[f'netbox_routing_plugin.view_{model}'],
            buttons=(
                PluginMenuButton(
                    link=f'plugins:netbox_routing_plugin:{model}_add',
                    title='Add',
                    icon_class=COL_ADD,
                    permissions=[f'netbox_routing_plugin.add_{model}'],
                ),
                PluginMenuButton(
                    link=f'plugins:netbox_routing_plugin:{model}_bulk_import',
                    title='Import',
                    icon_class=COL_IMPORT,
                    permissions=[f'netbox_routing_plugin.add_{model}'],
                ),
            ),
        )
        menus.append(menu)

    menus.append(
        PluginMenuItem(
            link='plugins:netbox_routing_plugin:community_match',
            link_text='Search Community Match',
            permissions=['netbox_routing_plugin.view_communitylistentry'],
        )
    )
    return tuple(menus)


COMMUNITY_MENU = build_menus()
