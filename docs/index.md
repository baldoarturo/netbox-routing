# NetBox Routing Protocols

A NetBox plugin to **document the routing configuration of your network**: static routes, BGP,
OSPF, IS-IS and EIGRP, together with the objects they use (prefix lists, route maps, AS paths,
communities) and BFD profiles.

NetBox already knows your devices, interfaces, IP addresses, prefixes, VRFs, ASNs and tenants.
This plugin adds the routing layer on top of them, so the answer to *"which routers speak OSPF in
area 0.0.0.10?"*, *"which peers use this prefix list?"* or *"what is the SRGB of this IS-IS
instance?"* is one search away, next to the rest of your inventory.

> **The plugin documents, it does not configure.** The plugin stores the **intended** routing configuration. It never connects to a device. Use
> it as the source of truth that your templates, automation or documentation read from, through
> the NetBox UI, REST API or GraphQL.

## What is covered

| Area | What you can describe | Page |
| --- | --- | --- |
| Static routes | Prefix, next hop, interface, VRF, metric, tag, the devices that carry the route | [Static routes](protocols/static.md) |
| BGP | Routers, VRF scopes, address families, peers, session/peer/policy templates, settings | [BGP](protocols/bgp.md) |
| OSPF (v2, IPv4) | Instances, areas, interfaces, networks, authentication, redistribution, virtual links, summaries, ranges, neighbors, traffic engineering, segment routing, fast reroute | [OSPF](protocols/ospf.md) |
| IS-IS | Instances, interfaces, levels, authentication, segment routing, Flex-Algo, SRv6 | [IS-IS](protocols/isis.md) |
| EIGRP | Routers (classic and named), address families, networks, interfaces | [EIGRP](protocols/eigrp.md) |
| Routing objects | Prefix lists, route maps, AS paths, communities and community lists | [Routing objects](routing-objects.md) |
| BFD | Reusable BFD timer profiles | [BFD](bfd.md) |

## Where to start

* **Never used it?** Read [Using the plugin](using.md): the menu, how objects relate to each other,
  and what every list and form offers.
* **Looking for a feature?** Each protocol page lists its features, fields and the RFC they come
  from. The [RFC index](rfc-index.md) goes the other way: from an RFC to the features that use it.
* **Installing?** See the [README](https://github.com/baldoarturo/netbox-routing-protocols#installation).

## Why the RFCs are mentioned

Routing protocols have precise rules: allowed ranges, default timers, which options require which.
The plugin follows the standards, so the field names, defaults and validations match what the RFC
says and what your routers implement. Wherever a feature or a default comes from an RFC, the page
says which one and, when it is not obvious, why it is there. Vendor-specific features without an RFC
are marked as such.

## Requirements

* NetBox 4.7 or newer.
* PostgreSQL, as NetBox itself.
