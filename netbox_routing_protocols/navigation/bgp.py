from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('BGP_MENU',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'


def build_menus():
    menus = []
    menu_items = (
        ('bgpinstance', 'Instances'),
        ('bgpaddressfamily', 'Address Families'),
        ('bgppeergroup', 'Peer Groups'),
        ('bgplistenrange', 'Listen Ranges'),
        ('bgpredistribution', 'Redistribution'),
        ('bgporiginatednetwork', 'Originated Networks'),
        ('bgpaggregate', 'Aggregates'),
        ('bgppeer', 'Peers'),
        ('bgppeeraddressfamily', 'Peer Address Families'),
    )
    for model, name in menu_items:
        menu = PluginMenuItem(
            link=f'plugins:netbox_routing_protocols:{model}_list',
            link_text=f'{name}',
            permissions=[f'netbox_routing_protocols.view_{model}'],
            buttons=(
                PluginMenuButton(
                    link=f'plugins:netbox_routing_protocols:{model}_add',
                    title='Add',
                    icon_class=COL_ADD,
                    permissions=[f'netbox_routing_protocols.add_{model}'],
                ),
            ),
        )
        menus.append(menu)

    return tuple(menus)


BGP_MENU = build_menus()
