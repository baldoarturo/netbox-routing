from netbox.plugins import PluginConfig
from importlib.metadata import metadata

plugin = metadata('netbox-routing-plugin')


class NetboxRouting(PluginConfig):
    # The distribution is published as netbox-routing-plugin, but the app
    # label, URLs and migrations stay under the module name.
    name = 'netbox_routing_plugin'
    verbose_name = 'Netbox Routing Protocols'
    description = plugin.get('Summary')
    version = plugin.get('Version')
    author = plugin.get('Author')
    author_email = plugin.get('Author-email')
    base_url = 'routing'
    min_version = '4.7.0'
    required_settings = []
    caching_config = {}
    default_settings = {}
    graphql_schema = 'graphql.schema.schema'

    def ready(self):
        super().ready()

        from netbox_routing_plugin import signals  # noqa: F401


config = NetboxRouting
