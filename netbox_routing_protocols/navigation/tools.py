from netbox.plugins import PluginMenuItem

__all__ = ('TOOLS_MENU',)

TOOLS_MENU = (
    PluginMenuItem(
        link='plugins:netbox_routing_protocols:prefix_match',
        link_text='Prefix Match',
        permissions=['netbox_routing_protocols.view_prefixlistentry'],
    ),
)
