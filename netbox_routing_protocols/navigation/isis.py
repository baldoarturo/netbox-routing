# SPDX-License-Identifier: Apache-2.0

from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('MENUITEMS',)

COL_ADD = 'mdi mdi-plus'
COL_IMPORT = 'mdi mdi-upload'


def build_menus():
    # Primary objects first (instance, interface), then their EAV settings, then the
    # per-instance detail tables (level, segment-routing, flex-algo). Mirrors the
    # build_menus() loop used by navigation/bgp.py and navigation/community.py so a
    # new model is one row, not a copy-pasted block (and the import button is gated by
    # the real `add` permission, not a non-existent `import_*` one).
    menus = []
    menu_items = (
        ('isisinstance', 'Instances'),
        ('isisinterface', 'Interfaces'),
        ('isissetting', 'Settings'),
        ('isislevel', 'Levels'),
        ('isissegmentrouting', 'Segment Routing'),
        ('isisflexalgo', 'Flex-Algos'),
        ('isisredistribution', 'Redistribution'),
        ('isissummaryaddress', 'Summary Addresses'),
        ('isisrouteleak', 'Route Leaking'),
        ('isisprefixsid', 'Prefix-SIDs'),
        ('isissrv6locator', 'SRv6 Locators'),
    )
    for model, name in menu_items:
        menu = PluginMenuItem(
            link=f'plugins:netbox_routing_protocols:{model}_list',
            link_text=name,
            permissions=[f'netbox_routing_protocols.view_{model}'],
            buttons=(
                PluginMenuButton(
                    link=f'plugins:netbox_routing_protocols:{model}_add',
                    title='Add',
                    icon_class=COL_ADD,
                    permissions=[f'netbox_routing_protocols.add_{model}'],
                ),
                PluginMenuButton(
                    link=f'plugins:netbox_routing_protocols:{model}_bulk_import',
                    title='Import',
                    icon_class=COL_IMPORT,
                    permissions=[f'netbox_routing_protocols.add_{model}'],
                ),
            ),
        )
        menus.append(menu)

    return tuple(menus)


MENUITEMS = build_menus()
