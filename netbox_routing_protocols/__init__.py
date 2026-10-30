from netbox.plugins import PluginConfig
from importlib.metadata import metadata

plugin = metadata('netbox_routing_protocols')


class NetboxRouting(PluginConfig):
    name = plugin.get('Name').replace('-', '_')
    verbose_name = plugin.get('Name').replace('-', ' ').title()
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

        from netbox_routing_protocols import signals  # noqa: F401


config = NetboxRouting
