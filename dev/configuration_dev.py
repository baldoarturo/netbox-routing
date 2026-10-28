"""
NetBox configuration to develop the plugin: self-contained (it does not need
the configuration.py of the NetBox checkout), with its own database so the
plugin's migrations never run against any other database.

Used through NETBOX_CONFIGURATION=configuration_dev, see dev/run.sh.
"""

import os

ALLOWED_HOSTS = ['*']

DATABASE = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ.get('NETBOX_ROUTING_DEV_DB', 'netbox_routing_protocols_dev'),
    'USER': 'netbox',
    'PASSWORD': 'netbox',
    'HOST': os.environ.get('NETBOX_DB_HOST', 'localhost'),
    'PORT': '',
    'CONN_MAX_AGE': 300,
}

REDIS = {
    'tasks': {
        'HOST': os.environ.get('NETBOX_REDIS_HOST', 'localhost'),
        'PORT': 6379,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 0,
        'SSL': False,
    },
    'caching': {
        'HOST': os.environ.get('NETBOX_REDIS_CACHE_HOST', 'localhost'),
        'PORT': 6380,
        'USERNAME': '',
        'PASSWORD': '',
        'DATABASE': 1,
        'SSL': False,
    },
}

# Development only: this instance is never exposed
SECRET_KEY = 'netbox-routing-protocols-development-only-secret-key-0123456789'

DEBUG = True
DEVELOPER = True

PLUGINS = ['netbox_routing_protocols']
