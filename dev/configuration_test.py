"""
NetBox configuration to run the plugin tests: NetBox's testing configuration
with the plugin enabled. Used through NETBOX_CONFIGURATION=configuration_test,
see dev/test.sh.
"""

from netbox.configuration_testing import *  # noqa: F401,F403
from netbox.configuration_testing import PLUGINS

PLUGINS = [*PLUGINS, 'netbox_routing']
DEVELOPER = True
