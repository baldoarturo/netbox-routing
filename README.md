# Netbox Routing Protocols

[![PyPI](https://img.shields.io/pypi/v/netbox-routing-protocols.svg)](https://pypi.org/project/netbox-routing-protocols/)
[![Python](https://img.shields.io/pypi/pyversions/netbox-routing-protocols.svg)](https://pypi.org/project/netbox-routing-protocols/)
[![NetBox](https://img.shields.io/badge/NetBox-4.7%2B-success.svg)](https://github.com/netbox-community/netbox)
[![CI](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml/badge.svg)](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml)
[![License: AGPL-3.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A plugin for tracking all kinds of routing information

> [!WARNING]
> **Work in progress, not production ready.** The data model, the API and the migrations can still change between versions, and there is no stable release yet.

## Documentation

The documentation for operators and users (every protocol and feature, with the RFC it comes from) is in [`docs/`](docs/index.md).

## Features

### Current features

* Static routing
* Dynamic routing
  * EIGRP
  * BGP
    * Templates/Group inheritance
    * IPv4/IPv46 AF VRF support
    * VPNv4 support
  * OSPF

### Under development


### Roadmapped

* Dynamic Routing
  * IS-IS

# Requirements

* NetBox 4.7+
* Python 3.12+

## Compatibility Matrix

| NetBox Version | Plugin Version |
| -------------- | -------------- |
| 3.2.x | 0.1.x |
| 4.1.x | 0.2.x |
| 4.2.x | 0.3.0 |
| 4.3.x | 0.3.1 |
| 4.4.x | 0.3.1 |
| 4.5.x | 0.4.x |
| 4.6.x | 0.5.0 |
| 4.7.x | 0.5.1 and later |

## Installation

Follows the standard [NetBox plugin installation procedure](https://netboxlabs.com/docs/netbox/plugins/#installing-plugins).

> [!NOTE]
> PyPI publishing is disabled in this fork for now, so the plugin is installed straight from GitHub instead of `pip install netbox-routing-protocols`.

### Bare metal

The steps below assume NetBox lives in `/opt/netbox`; adjust paths to match your environment.

1. Install the package into the NetBox virtual environment:

   ```shell
   source /opt/netbox/venv/bin/activate
   pip install git+https://github.com/baldoarturo/netbox-routing-protocols.git
   ```

2. Add it to `local_requirements.txt` so it is reinstalled whenever NetBox is upgraded:

   ```shell
   echo "git+https://github.com/baldoarturo/netbox-routing-protocols.git" >> /opt/netbox/local_requirements.txt
   ```

3. Enable the plugin in `configuration.py`:

   ```python
   PLUGINS = [
       'netbox_routing_protocols',
   ]
   ```

4. Apply the database migrations and collect static files:

   ```shell
   python3 /opt/netbox/netbox/manage.py migrate
   python3 /opt/netbox/netbox/manage.py collectstatic --no-input
   ```

5. Restart NetBox (e.g. `sudo systemctl restart netbox netbox-rq`).

### Docker

Plugins in Docker are installed by building a custom image, not with `pip` inside a running container. Follow the [netbox-docker plugin instructions](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins) and use the same git URL as the package, and `netbox_routing_protocols` as the plugin name in `PLUGINS`. Migrations and `collectstatic` run automatically when the container starts.

### Migrating from netbox-bgp

> [!NOTE]
> This plugin is not compatible with `netbox-bgp`, but there is a built-in migration tool.
>
> Remove `netbox-bgp` from `PLUGINS`, make sure `netbox-routing-protocols` is installed, then run:
>
> `python3 /opt/netbox/netbox/manage.py migrate-netbox-bgp`

## Configuration

None

## Usage

TBD

## Additional Notes

TBD

## Contribute

Contributions are always welcome!  Please open an issue first before contributing as the scope is going to be kept
intentionally narrow

Install the pre-commit hooks once in your clone (`pip install pre-commit`, then `pre-commit install`): they run Ruff
and Black on every commit with the same configuration as the CI, which runs `pre-commit run --all-files` on every pull
request. See `dev/README.md` to run NetBox and the tests.
