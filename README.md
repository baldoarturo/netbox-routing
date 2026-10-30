# Netbox Routing Protocols

[![PyPI](https://img.shields.io/pypi/v/netbox-routing-protocols.svg)](https://pypi.org/project/netbox-routing-protocols/)
[![Python](https://img.shields.io/pypi/pyversions/netbox-routing-protocols.svg)](https://pypi.org/project/netbox-routing-protocols/)
[![NetBox](https://img.shields.io/badge/NetBox-4.7%2B-success.svg)](https://github.com/netbox-community/netbox)
[![CI](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml/badge.svg)](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A plugin for tracking all kinds of routing information

> [!WARNING]
> **Work in progress, not production ready.** The data model, the API and the migrations can still change between versions, and there is no stable release yet.

## About this project

This plugin was created by Daniel Sheppard ([`dansheps`](https://github.com/dansheps/netbox-routing)). This repository is a fork that is developed with the help of AI, using [Claude Code](https://claude.com/claude-code) to speed up development: Claude writes the code, tests and documentation, and the maintainer sets the direction and reviews and approves the changes.

## Documentation

The documentation for operators and users (every protocol and feature, with the RFC it comes from) is in [`docs/`](docs/index.md). Start with [Using the plugin](docs/using.md); the [RFC index](docs/rfc-index.md) goes from an RFC to the features that use it, and [Development](docs/development.md) explains how to work on the docs.

## Features

### Ready

* [Routing objects](docs/routing-objects.md)
  * [Prefix lists](docs/routing-objects.md#prefix-lists)
  * [AS paths](docs/routing-objects.md#as-paths)
  * [Communities](docs/routing-objects.md#communities) and [community lists](docs/routing-objects.md#community-lists)
* [Route policies](docs/routing-objects.md#route-policies) (match and set, jump to another policy, final deny, search tool; used by OSPF, IS-IS and EIGRP)
* [Static routes](docs/protocols/static.md) (special next hops, interface, route leaking)
* [OSPF, versions 2 (IPv4) and 3 (IPv6)](docs/protocols/ospf.md) (instances, areas, interfaces, authentication with key rollover, redistribution, virtual links, ranges, neighbors, traffic engineering, segment routing, fast reroute)
* [IS-IS](docs/protocols/isis.md) (instances, levels, interfaces, authentication, redistribution, route leaking, segment routing, Flex-Algo, SRv6)

### Work in progress

Not production ready; the model and the migrations can still change. Each one has a tracking issue.

* Dynamic routing
  * [EIGRP](docs/protocols/eigrp.md) ([tracking #413](https://github.com/baldoarturo/netbox-routing-protocols/issues/413))
  * [BGP](docs/protocols/bgp.md) ([tracking #411](https://github.com/baldoarturo/netbox-routing-protocols/issues/411)): templates/group inheritance, IPv4/IPv6 AF and VRF, VPNv4
* [BFD profiles](docs/bfd.md) ([tracking #414](https://github.com/baldoarturo/netbox-routing-protocols/issues/414))
* Segment routing ([tracking #201](https://github.com/baldoarturo/netbox-routing-protocols/issues/201))

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

See [Using the plugin](docs/using.md): the menu, how the objects relate to each other, bulk import and validation.

## Additional Notes

TBD

## Contribute

Contributions are always welcome!  Please open an issue first before contributing as the scope is going to be kept
intentionally narrow

Install the pre-commit hooks once in your clone (`pip install pre-commit`, then `pre-commit install`): they run Ruff
and Black on every commit with the same configuration as the CI, which runs `pre-commit run --all-files` on every pull
request. See [`dev/README.md`](dev/README.md) to run NetBox and the tests.
