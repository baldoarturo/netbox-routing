# Changelog

## 1.0.0

First release on PyPI, as `netbox-routing-models` (the name `netbox-routing-protocols` was already taken on PyPI). The Python module and the plugin name stay `netbox_routing_protocols`.

Supports NetBox 4.7 and later.

- Static routes, with special next hops, interface routes and route leaking.
- Routing objects: prefix lists, AS paths, communities and community lists, and route policies (match and set, used by OSPF, IS-IS and EIGRP).
- OSPFv2 (IPv4) and OSPFv3 (IPv6): instances, areas, interfaces, authentication with key rollover, redistribution, virtual links, ranges, neighbors, traffic engineering, segment routing and fast reroute.
- IS-IS: instances, levels, interfaces, authentication, redistribution, route leaking, segment routing, Flex-Algo and SRv6.
- BGP: instances, address families, templates and peer groups, peers, listen ranges, redistribution, originated networks and aggregates, route policy and settings.
- BFD profiles.
- Device routing tab and a menu under Routing, with REST API, GraphQL and bulk import/export.

Original author: Daniel Sheppard ([`dansheps`](https://github.com/dansheps/netbox-routing)).
