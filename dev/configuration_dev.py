"""
NetBox configuration to develop the plugin: the shared dev configuration
(netbox/netbox/configuration.py) with its own database, so the plugin's
migrations never run against the shared `netbox` database.

Used through NETBOX_CONFIGURATION=configuration_dev, see dev/run.sh.
"""

import os

from netbox.configuration import *  # noqa: F401,F403
from netbox.configuration import DATABASE

DATABASE = {
    **DATABASE,
    'NAME': os.environ.get('NETBOX_ROUTING_DEV_DB', 'netbox_routing_dev'),
}

PLUGINS = ['netbox_routing']
