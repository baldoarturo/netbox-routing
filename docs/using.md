# Using the plugin

> [!WARNING]
> **Work in progress, not production ready.** The data model, the API and the migrations can still change between versions, and there is no stable release yet. Only **static routes, route policies, prefix lists, AS paths, communities, OSPF and IS-IS** are considered ready; everything else is still in progress.

## About this project

This plugin was created by Daniel Sheppard ([`dansheps`](https://github.com/dansheps/netbox-routing)). This repository is a fork that is developed with the help of AI, using [Claude Code](https://claude.com/claude-code) to speed up development: Claude writes the code, tests and documentation, and the maintainer sets the direction and reviews and approves the changes.

## The menu

Everything lives under **Routing** in the NetBox navigation menu, grouped like this:

| Group | Entries |
| --- | --- |
| **Routing Objects** | Community List, Community, Community List Entry, Prefix Lists, Prefix List Entries, **Search Prefix Match**, Route Policies, Route Policy Entries, AS Path, AS Path Entries |
| **BFD** | BFD Profile |
| **Static** | Static Routes |
| **BGP** | Instances, Address Families, Redistribution, Peer Groups, Listen Ranges, Peers, Peer Address Families |
| **OSPF** (v2 and v3) | Instances, Areas, Interfaces, Networks, Redistribution, Virtual Links, Summary Addresses, Neighbors, Area Ranges, Prefix SIDs, Authentication Keys |
| **IS-IS** | Instances, Interfaces, Settings, Levels, Segment Routing, Flex-Algos, Prefix-SIDs, SRv6 Locators |
| **EIGRP** | Routers, Address Families, Networks, Interfaces |

Each entry opens a **list** of that kind of object. Most entries have an **Add** button and many
have an **Import** button (see [Importing](#importing-in-bulk)).

## Objects and how they relate

Routing configuration is a tree. You build it from the top down, and each object points to its
parent. The same shape repeats for every protocol:

```
Device ── protocol process (instance / router) ── area / address family / level ── interface
                                              └─ per-process extras (redistribution, ranges, ...)
```

| Protocol | Top | Then | Down to |
| --- | --- | --- | --- |
| Static | Static route | (assigned to) Devices | |
| BGP | Instance (on a device, optionally in a VRF) | Address families, Peer groups → Listen ranges, Peer address families | Peers → Peer address families |
| OSPF | Instance (on a device, optionally in a VRF) | Areas → Interfaces → Networks, Neighbors | Redistribution, Virtual links, Summary addresses and Prefix SIDs hang from the instance; Area ranges from the area |
| IS-IS | Instance (on a device, optionally in a VRF) | Levels, Segment routing, Flex-Algos, SRv6 locators | Interfaces → Interface levels, Prefix-SIDs |
| EIGRP | Router (on a device) | Address families | Networks and Interfaces |

The consequence: **create the parent first**. The Add form of an OSPF interface needs an OSPF
instance and an OSPF area of that instance to exist already. If a form asks for something that does
not exist, go back one level.

> **Use what NetBox already has.** Devices, interfaces, IP addresses, prefixes, VRFs, ASNs, tenants and roles are standard NetBox
> objects. The plugin never copies them; it links to them. A prefix list entry points at a NetBox
> prefix, an OSPF network points at an IP address assigned to an interface, a BGP peer points at
> an IP address, a BGP instance points at an ASN.

## What every object has

Because they are standard NetBox objects, all of them support:

* **Description, tags and custom fields**, and a **comments** field on most.
* **Search, filters and export** in the lists. The global NetBox search finds the plugin's objects.
* **Change log** and journal entries, so you can see who changed a timer and when.
* **Cloning** (the Clone button) which copies the fields that make sense to repeat.
* **Bulk edit and bulk delete** from the lists.
* The **REST API** and **GraphQL** for every model, under `/api/plugins/routing/`.

### On the device page

The device page gets one **Routing** tab (and a counter). It has a section per protocol: the static routes
assigned to the device, and its OSPF instances, IS-IS instances, EIGRP routers and BGP instances. Each section
shows how many there are and links to the full list filtered on the device. The device is the page, so the device
column is not repeated. The instances also show their children in tabs on their own detail page, for example an
OSPF instance has an *Interfaces* tab and an OSPF area lists *its* interfaces.

## Importing in bulk

Entries with an **Import** button accept CSV, YAML or JSON through the usual NetBox import form.
Columns refer to related objects by name (a device by its name, an interface by its name and device),
the same way core NetBox imports do. Use *Import* on a list to see the exact columns the form
accepts; it is the quickest way to load hundreds of interfaces or peers.

## Validation

Forms refuse combinations the protocols do not allow, with a message that says why. Examples:
an OSPF dead interval that is not larger than the hello interval, an IS-IS prefix SID with both an
index and a label, a prefix list entry whose `le` is longer than the address family allows. Each
protocol page lists the rules and their RFC.

## Secrets

Authentication keys and BGP passphrases are stored **in plain text** in the NetBox database, like any
other custom field. They are shown in the interface (a few OSPF keys can also show their MD5 digest),
so give *view* permission on these objects only to people who may see the keys. Keys are not added
to the global search index.
