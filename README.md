# Netbox Routing Protocols

[![PyPI](https://img.shields.io/pypi/v/netbox-routing-plugin.svg)](https://pypi.org/project/netbox-routing-plugin/)
[![Python](https://img.shields.io/pypi/pyversions/netbox-routing-plugin.svg)](https://pypi.org/project/netbox-routing-plugin/)
[![NetBox](https://img.shields.io/badge/NetBox-4.7%2B-success.svg)](https://github.com/netbox-community/netbox)
[![CI](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml/badge.svg)](https://github.com/baldoarturo/netbox-routing-protocols/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/LICENSE)

A plugin for tracking all kinds of routing information

<p align="center">
  <img src="https://raw.githubusercontent.com/baldoarturo/netbox-routing-protocols/main/docs/images/device-routing-tab.png" alt="The Routing tab of a device, with its static routes, OSPF instances and IS-IS instances" width="900">
</p>

Every routing protocol of a device in one Routing tab: static routes, OSPF, IS-IS, BGP and EIGRP.

> [!WARNING]
> **Work in progress, not production ready.** The data model, the API and the migrations can still change between versions. 1.0.0 is the first release on PyPI.

## About this project

This plugin was created by Daniel Sheppard ([`dansheps`](https://github.com/dansheps/netbox-routing)), who is credited as the original author and a historical contributor. The package is now maintained by Arturo ([`baldoarturo`](https://github.com/baldoarturo)). This repository is a fork that is developed with the help of AI, using [Claude Code](https://claude.com/claude-code) to speed up development: Claude writes the code, tests and documentation, and the maintainer sets the direction and reviews and approves the changes.

## Documentation

The documentation for operators and users (every protocol and feature, with the RFC it comes from) is in [`docs/`](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/index.md). Start with [Using the plugin](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/using.md); the [RFC index](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/rfc-index.md) goes from an RFC to the features that use it, and [Development](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/development.md) explains how to work on the docs.

## Features

### Ready

* [Routing objects](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md)
  * [Prefix lists](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md#prefix-lists)
  * [AS paths](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md#as-paths)
  * [Communities](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md#communities) and [community lists](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md#community-lists)
* [Route policies](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/routing-objects.md#route-policies) (match and set, jump to another policy, final deny, search tool; used by OSPF, IS-IS and EIGRP)
* [Static routes](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/protocols/static.md) (special next hops, interface, route leaking)
* [OSPF, versions 2 (IPv4) and 3 (IPv6)](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/protocols/ospf.md) (instances, areas, interfaces, authentication with key rollover, redistribution, virtual links, ranges, neighbors, traffic engineering, segment routing, fast reroute)
* [IS-IS](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/protocols/isis.md) (instances, levels, interfaces, authentication, redistribution, route leaking, segment routing, Flex-Algo, SRv6)
* [BGP](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/protocols/bgp.md) (instances, address families, peer groups, peers, listen ranges, redistribution, originated networks and aggregates, route policy; RFC 4271 and its extensions)

### Work in progress

Not production ready; the model and the migrations can still change. Each one has a tracking issue.

* Dynamic routing
  * [EIGRP](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/protocols/eigrp.md) ([tracking #413](https://github.com/baldoarturo/netbox-routing-protocols/issues/413))
* [BFD profiles](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/bfd.md) ([tracking #414](https://github.com/baldoarturo/netbox-routing-protocols/issues/414))
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
| 4.7.x | 1.0.0 and later |

## Installation

Follows the standard [NetBox plugin installation procedure](https://netboxlabs.com/docs/netbox/plugins/#installing-plugins).

> [!NOTE]
The package is published on PyPI as `netbox-routing-plugin`. You can also install the development version straight from GitHub.

### Bare metal

The steps below assume NetBox lives in `/opt/netbox`; adjust paths to match your environment.

1. Install the package into the NetBox virtual environment:

   ```shell
   source /opt/netbox/venv/bin/activate
   pip install netbox-routing-plugin
   ```

   To install the development version from GitHub instead, use `pip install git+https://github.com/baldoarturo/netbox-routing-protocols.git`.

2. Add it to `local_requirements.txt` so it is reinstalled whenever NetBox is upgraded:

   ```shell
   echo "git+https://github.com/baldoarturo/netbox-routing-protocols.git" >> /opt/netbox/local_requirements.txt
   ```

3. Enable the plugin in `configuration.py`:

   ```python
   PLUGINS = [
       'netbox_routing_plugin',
   ]
   ```

4. Apply the database migrations and collect static files:

   ```shell
   python3 /opt/netbox/netbox/manage.py migrate
   python3 /opt/netbox/netbox/manage.py collectstatic --no-input
   ```

5. Restart NetBox (e.g. `sudo systemctl restart netbox netbox-rq`).

### Docker

Plugins in Docker are installed by building a custom image, not with `pip` inside a running container. Follow the [netbox-docker plugin instructions](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins) and use the same git URL as the package, and `netbox_routing_plugin` as the plugin name in `PLUGINS`. Migrations and `collectstatic` run automatically when the container starts.

## Configuration

None

## Usage

See [Using the plugin](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/docs/using.md): the menu, how the objects relate to each other, bulk import and validation.

## Additional Notes

TBD

## Contribute

Contributions are always welcome!  Please open an issue first before contributing as the scope is going to be kept
intentionally narrow

Install the pre-commit hooks once in your clone (`pip install pre-commit`, then `pre-commit install`): they run Ruff
and Black on every commit with the same configuration as the CI, which runs `pre-commit run --all-files` on every pull
request. See [`dev/README.md`](https://github.com/baldoarturo/netbox-routing-protocols/blob/main/dev/README.md) to run NetBox and the tests.
