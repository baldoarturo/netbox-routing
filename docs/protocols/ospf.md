# OSPF (OSPFv2 and OSPFv3)

**Routing → OSPF**

OSPF (Open Shortest Path First) is a link-state interior routing protocol: every router floods
descriptions of its links, and each one computes the shortest paths on its own. The plugin models
**OSPF version 2 for IPv4**, defined in [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328), and
**OSPF version 3 for IPv6**, defined in [RFC 5340](https://www.rfc-editor.org/rfc/rfc5340), and the
extensions that real networks use on top of it. Defaults and ranges follow the RFC, and each feature
below says which RFC it comes from.

> **Scope.** Each instance has an **address family**: IPv4 is OSPFv2 ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328))
> and IPv6 is OSPFv3 ([RFC 5340](https://www.rfc-editor.org/rfc/rfc5340)). What the family does not allow is
> refused, and the forms offer only what applies. Not supported yet: the IPv4 address family inside OSPFv3
> ([RFC 5838](https://www.rfc-editor.org/rfc/rfc5838)) and IPsec authentication of OSPFv3
> ([RFC 4552](https://www.rfc-editor.org/rfc/rfc4552)).

## How it is organized

```
OSPF instance (a process on a device, optionally in a VRF)
 ├─ Area ── Interface (a device interface in the area) ── Network (its IP addresses)
 │                                                    └─ Neighbor (static neighbors)
 │   └─ Area range
 ├─ Redistribution
 ├─ Summary address
 ├─ Virtual link
 └─ Prefix SID
```

Build it top-down: **Instance → Area → Interface → Network**. The rest are optional extras of the
instance or area.

## Instances

**OSPF → Instances**

An instance is one OSPF process: "OSPF on this device, in this VRF".

### Identity

| Field | Meaning |
| --- | --- |
| Name | The process name or number, as on the device. |
| Device | The device that runs it. |
| VRF | Optional. OSPF can run once per VRF. |
| Address family | IPv4 (OSPFv2, the default) or IPv6 (OSPFv3). A device has **one instance per VRF and address family** (no VRF is the default VRF): it can run OSPFv2 and OSPFv3 side by side, but not two OSPFv2 in the same VRF. **It cannot be changed** once the instance exists, because everything under it (networks, neighbors, ranges, SIDs) depends on it: create another instance. |
| Router ID | The 32-bit identifier of the router in the OSPF domain ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) §C.1), written like an IPv4 address. It must be a valid IPv4 address, not `0.0.0.0` and without a mask, and it should be unique in the network. |
| Instance ID | Lets several OSPF processes run over the same link: routers form an adjacency only with a neighbor that has the same ID ([RFC 6549](https://www.rfc-editor.org/rfc/rfc6549)). Default 0. It goes from 0 to 127 in OSPFv2 and from 0 to 255 in OSPFv3 (an 8-bit field, [RFC 5340](https://www.rfc-editor.org/rfc/rfc5340) §2.4). |

### Default route

| Field | Meaning |
| --- | --- |
| Default originate | Advertise a default route (`0.0.0.0/0`) into OSPF. By default it is advertised only while the router has a default route itself. |
| Always | Advertise it even when no default route exists locally. |
| Metric, metric type | Metric of the originated route, and whether it is **Type 1 (E1)** or **Type 2 (E2)** (see [redistribution](#redistribution)). These options require *Default originate*. |

### Route policies

| Field | Meaning |
| --- | --- |
| Import policy | Optional [route policy](../routing-objects.md#route-policies) that filters the routes OSPF **installs** in the routing table (Cisco `distribute-list route-map … in`, Juniper `import`). |
| Export policy | Optional route policy that filters the routes **injected into** OSPF from other sources (Cisco `redistribute … route-map`, Juniper `export`). |

A route policy that an instance uses **cannot be deleted**: choose another one, or clear the field, first. The same goes for the one of a redistribution.

### Timers

| Field | Meaning | Default |
| --- | --- | --- |
| SPF initial / short / long delay, time to learn, hold-down | The *SPF back-off algorithm*: after a topology change the router waits a short time before recomputing paths, and backs off when changes keep coming, to protect the CPU during instability ([RFC 8405](https://www.rfc-editor.org/rfc/rfc8405)). Milliseconds. The delays must be in order. | 50 / 200 / 5000 ms, learn 500 ms, hold-down 10000 ms |
| LSA minimum interval | Minimum time between originations of the same LSA (`MinLSInterval`, RFC 2328). | 5000 ms |
| LSA minimum arrival | Minimum time before accepting a new copy of the same LSA (`MinLSArrival`, RFC 2328). | 1000 ms |

### Stability and maintenance

| Field | Meaning |
| --- | --- |
| Max metric (router LSA) | Advertise the maximum metric for the router's links so that **transit traffic avoids the router** while it is being maintained or started ([RFC 6987](https://www.rfc-editor.org/rfc/rfc6987)). The *on startup* value keeps it for that many seconds after boot; it requires the max-metric option. |
| Graceful restart | **Disabled**, **planned restarts only**, or **planned and unplanned** restarts: the router keeps forwarding while OSPF restarts ([RFC 3623](https://www.rfc-editor.org/rfc/rfc3623)). |
| Restart period | Seconds neighbors wait for the restart to finish: 1 to 1800, default 120. |
| Helper, strict LSA checking | Whether this router **helps neighbors** that restart gracefully, and whether it ends the help when the topology changes (RFC 3623; both enabled by default, as the RFC suggests). |

### Limits

| Field | Meaning |
| --- | --- |
| Max LSAs, threshold, warning only | Cap on the number of LSAs the process accepts, the percentage that triggers a warning (default 75) and whether to only warn at the limit. Protects the router from being flooded with routes. |
| External LSDB limit, exit overflow interval | Cap on non-default AS-external LSAs and how long to wait before leaving the overflow state; 0 means until restart. This is the **database overflow** feature of [RFC 1765](https://www.rfc-editor.org/rfc/rfc1765). |

### Routing behaviour

| Field | Meaning |
| --- | --- |
| RFC 1583 compatibility | Rules used to choose among AS-external routes. RFC 2328 §16.4.1 changed them; the default (enabled) keeps the old behaviour so mixed networks agree. All routers in an OSPF domain should use the same setting. |
| Reference bandwidth | Mbps that gets an interface cost of 1, used to derive the cost of interfaces that have none. Raise it on networks with links faster than 100 Mbps. |
| Maximum paths | Equal-cost paths installed (ECMP), 1 to 64. |
| Distances | Administrative distance of intra-area, inter-area and external routes (1 to 255). |
| Default metric | Metric given to redistributed routes that have none. |
| Passive interface default | Interfaces are passive (no neighbors) unless configured otherwise. |
| BFD on all interfaces | Enable [BFD](../bfd.md) on every OSPF interface. |
| Log adjacency changes (+ detail) | Log neighbor state changes, or every state change. |

Empty optional fields mean "use the platform default".

### Advanced features

| Field | Meaning | Standard |
| --- | --- | --- |
| Opaque capability | Support *opaque LSAs*, the extensible LSA type that carries traffic-engineering and segment-routing data. Required by the two features below. | [RFC 5250](https://www.rfc-editor.org/rfc/rfc5250) |
| TE router address | Stable address of the router in traffic-engineering LSAs, usually a loopback. Empty uses the router ID. | [RFC 3630](https://www.rfc-editor.org/rfc/rfc3630) |
| Segment routing, SRGB start/size | Advertise segment routing and the label block (SRGB) the router uses. Requires opaque LSAs. | [RFC 8665](https://www.rfc-editor.org/rfc/rfc8665), [RFC 7684](https://www.rfc-editor.org/rfc/rfc7684) |
| LDP sync, hold-down | Advertise the maximum metric on interfaces until LDP is up on them, so traffic never takes a path without labels. | [RFC 5443](https://www.rfc-editor.org/rfc/rfc5443) |

**By address family.** Opaque LSAs are an OSPFv2 mechanism ([RFC 5250](https://www.rfc-editor.org/rfc/rfc5250)):
OSPFv3 carries the flooding scope in the LSA type ([RFC 5340](https://www.rfc-editor.org/rfc/rfc5340)
A.4.2.1), so on an IPv6 instance the *Opaque capability* cannot be set and traffic engineering and
segment routing do not ask for it. The TE router address and the prefix SIDs must be of the family of
the instance. LDP sync, TTL security and fast reroute apply to both families.

The instance's **authentication** is described in [Authentication](#authentication).

## Areas

**OSPF → Areas**

OSPF divides a large network into **areas**; routers in an area know the detail of that area only, and
**area border routers (ABRs)** summarize it to the rest. Area **0 (the backbone)** connects all the
others.

| Field | Meaning |
| --- | --- |
| Instance | The OSPF instance. |
| Area ID | A number (`10`) or dotted form (`0.0.0.10`). Unique within the instance. |
| Area type | See the table below. |

| Type | What it means | Standard |
| --- | --- | --- |
| Standard | A normal area: receives all routes. | RFC 2328 |
| Backbone | Area 0. **Area 0 must be of type Backbone, and no other area can be.** | RFC 2328 |
| Stub | No external (AS-external) routes inside; the ABR injects a default route instead, which shrinks the routing table of small routers. | RFC 2328 §3.6 |
| Totally Stubby | A stub area that also blocks inter-area routes: only a default route enters. | Vendor extension of the stub area |
| NSSA | A stub-like area that **can still contain an ASBR** (a router that imports external routes). Its external routes travel as type 7 LSAs and the ABR translates them to type 5. | [RFC 3101](https://www.rfc-editor.org/rfc/rfc3101) |
| Totally NSSA | An NSSA that also blocks inter-area routes. | Vendor extension of RFC 3101 |

Area 0 cannot be a stub area, and an area cannot be removed while it has interfaces.

Extra settings for **Stub and NSSA** areas:

| Field | Meaning |
| --- | --- |
| Default cost | Cost of the default route the ABR advertises into the area (stub and NSSA only). |
| Translate always (NSSA) | Always translate type 7 into type 5 LSAs ([RFC 3101](https://www.rfc-editor.org/rfc/rfc3101)). |
| No redistribution (NSSA) | Do not import redistributed routes into the NSSA. |
| Default originate (NSSA) | Originate a default type 7 LSA into the NSSA. |

For all areas:

| Field | Meaning | Standard |
| --- | --- | --- |
| Traffic engineering | Originate TE LSAs (opaque type 10) for the area. Needs opaque LSAs on the instance, and cannot be switched off while interfaces use TE attributes. | [RFC 3630](https://www.rfc-editor.org/rfc/rfc3630) |
| Fast reroute | Compute loop-free alternate next hops for the routes of the area; each interface picks its mode. Cannot be switched off while interfaces use it. | [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286) |

## Interfaces

**OSPF → Interfaces**

An OSPF interface says "this device interface takes part in OSPF, in this area, with these settings".
An interface can run **one** OSPF instance. The interface must be on the same **device and VRF** as
the instance, and the area must belong to the instance.

### Basics

| Field | Meaning |
| --- | --- |
| Interface | A device interface (NetBox DCIM). |
| Instance, Area | Where it takes part. |
| Network type | See below. |
| Passive | Advertise the interface's network but form no neighbors on it. |
| Priority | Designated Router election priority, 0 to 255 (default 1). **0 means the router never becomes DR**. |
| Cost | Output cost, 1 to 65535. Empty derives it from the interface bandwidth and the instance's reference bandwidth. |
| BFD | Use [BFD](../bfd.md) for fast neighbor failure detection. |
| MTU ignore | Skip the MTU mismatch check when forming adjacencies. The MTU itself comes from the device interface. |

### Network types

The network type tells OSPF how the link behaves ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)):

| Type | Meaning |
| --- | --- |
| Broadcast | A LAN such as Ethernet: neighbors are discovered with multicast and a DR is elected. The default. |
| Point to Point | A link between two routers; no election. |
| Non Broadcast (NBMA) | A multi-access network without broadcast (such as Frame Relay): neighbors are **configured by hand** and a DR is elected. |
| Point to Multipoint | One interface connected to several routers treated as a set of point-to-point links. |
| Point to Multipoint Non Broadcast | The same, with neighbors configured by hand. |
| Loopback | A loopback interface, advertised as a host route. |

### Timers

| Field | Meaning | Default |
| --- | --- | --- |
| Hello interval | Seconds between Hello packets. | 10 |
| Dead interval | Seconds without Hellos before a neighbor is declared down. It **must be larger than the hello interval**. | 40 |
| Retransmit interval | Seconds between LSA retransmissions. | 5 |
| Transmit delay | Estimated seconds to transmit an LSA. | 1 |

The defaults are the values of [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) appendix C.3 for a LAN. Routers
must agree on hello and dead intervals to become neighbors.

### Other interface options

| Field | Meaning | Standard |
| --- | --- | --- |
| TTL security, hops | Send OSPF packets with TTL 255 and drop received ones whose TTL shows they crossed more than the allowed hops, so only directly connected routers can speak OSPF. Use 1 hop for direct neighbors. | [RFC 5082](https://www.rfc-editor.org/rfc/rfc5082) |
| Prefix suppression | Do not advertise the interface's prefixes in the router LSA, hiding transit-only networks. | [RFC 6860](https://www.rfc-editor.org/rfc/rfc6860) |
| Flood reduction | Flood LSAs as *DoNotAge* to cut refresh traffic in stable networks. | [RFC 4136](https://www.rfc-editor.org/rfc/rfc4136) |
| Demand circuit | Suppress periodic Hellos and refreshes on a link that is charged by use. | [RFC 1793](https://www.rfc-editor.org/rfc/rfc1793) |
| Database filter all out | Do not flood any LSA out of the interface. | Vendor feature |
| TE metric, max reservable bandwidth, admin group | Traffic-engineering attributes of the link: its TE metric, bandwidth that can be reserved, and the colour mask used by affinity rules. They require traffic engineering on the area. | [RFC 3630](https://www.rfc-editor.org/rfc/rfc3630) |
| Adjacency SID | Local MPLS label for the adjacency over this link (16 to 1048575). Needs segment routing on the instance. | [RFC 8665](https://www.rfc-editor.org/rfc/rfc8665) |
| Fast reroute | Protect the traffic with a precomputed alternate: **Loop-Free Alternate** or **Remote LFA**. Needs fast reroute on the area. | [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286), [RFC 7490](https://www.rfc-editor.org/rfc/rfc7490) |
| LDP sync | Override the instance's LDP synchronization for this interface; leave empty to inherit. | [RFC 5443](https://www.rfc-editor.org/rfc/rfc5443) |

## Networks

**OSPF → Networks**

The IP addresses of an OSPF interface that OSPF advertises: pick the **interface** and a NetBox **IP
address** assigned to that interface. An interface may have several networks, each only once. An
interface with no addresses (an unnumbered interface) has no networks. Only IPv4 is accepted, and the
network is derived from the address and its mask. Deleting the IP address in IPAM removes the network.

Networks are for **IPv4 instances only**: OSPFv3 runs per link, so it is enabled on the interface itself
and has no network statements ([RFC 5340](https://www.rfc-editor.org/rfc/rfc5340) §2.1). For the same
reason an interface of an IPv6 instance cannot be unnumbered. In the same way, the neighbors, area ranges,
summary addresses, prefix SIDs and the TE router address of an instance must be of its family; the neighbors
of an OSPFv3 instance are identified by their link-local address (RFC 5340 §3.1.1).

## Authentication

OSPFv2 can authenticate its packets so that only trusted routers join the domain
([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) appendix D). The same block of fields appears on
**instances, areas, interfaces and virtual links**:

| Type | Meaning |
| --- | --- |
| Null | No authentication. |
| Simple Password | A clear-text password, up to **8 characters**. Weak: only protects against mistakes. |
| Message Digest | A cryptographic digest with a **key ID (0 to 255)** and a key of up to **16 characters** for MD5. |
| Authentication Trailer | **OSPFv3 only.** The key with an **SA ID (0 to 65535)** and an **HMAC-SHA algorithm** ([RFC 7166](https://www.rfc-editor.org/rfc/rfc7166)); MD5 is not allowed. |
| Key Chain | The name of a key chain configured on the device, which rotates keys. No key is stored here. |

**The family decides what you can choose.** OSPFv2 (IPv4 instances) uses Null, Simple Password, Message
Digest and Key Chain. OSPFv3 (IPv6 instances) dropped the authentication of the packet header
([RFC 5340](https://www.rfc-editor.org/rfc/rfc5340) §2.5) and uses the Authentication Trailer, a Key
Chain or none. The forms offer only the types of the family, the model refuses the others, and an
instance, area, interface or virtual link cannot mix them because they all belong to one instance. The
rule of OSPFv2 that one area uses a single authentication type does not exist in OSPFv3: each interface
has its own. IPsec authentication of OSPFv3 ([RFC 4552](https://www.rfc-editor.org/rfc/rfc4552)) is not
supported yet.

For message digest, choose the **algorithm**: **MD5** ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)),
or **HMAC-SHA-1/256/384/512** ([RFC 5709](https://www.rfc-editor.org/rfc/rfc5709)). The key is stored
as plain text; tick *Show MD5* to also display the MD5 digest the key produces on devices that store
it that way.

### Inheritance

Authentication is set where convenient and **inherited downwards**: an **interface** uses its own
authentication; if it has none it uses its **area's**; if the area has none it uses the **instance's**.
So you can set one authentication on the instance, override it for an area, and override it again on a
single interface.

The plugin checks that the pieces agree: an interface cannot go without authentication, or use a
different type, in an area that requires one; an area's authentication is checked against its
interfaces; and the instance default is checked against the interfaces of the areas that use it. The
three types (null, simple, cryptographic) cannot be mixed within an area, because routers need the
same type to talk. Virtual links must agree with the backbone's type.

## Redistribution

**OSPF → Redistribution**

Redistribution imports routes learned some other way into OSPF as **external routes**, turning the
router into an ASBR.

| Field | Meaning |
| --- | --- |
| Protocol | **Connected**, **Static**, **EIGRP**, **BGP**, **OSPF** or **IS-IS**. |
| Source | The process to take routes from, for EIGRP, BGP, OSPF and IS-IS. It must be on the **same device** as the instance. Connected and static have no source. |
| Metric | Metric of the redistributed routes. |
| Metric type | **E1** or **E2**. With **E2** (the default) the metric stays the same across the OSPF domain; with **E1** the internal cost to reach the ASBR is added, which makes routers prefer the closer ASBR ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) §16.4.1). |
| Subnets | Redistribute subnets, not only classful networks. On by default. |
| Route tag | A tag set on the routes, to filter them later (RFC 2328 external route tag). |
| Route policy | Optional [route policy](../routing-objects.md#route-policies) applied to the redistributed routes (Cisco `redistribute … route-map`). A policy used here **cannot be deleted**. |
| OSPF route types | When the source is OSPF, which kinds of routes to redistribute. |

Rules: each protocol (and each source) can be redistributed once per instance; an OSPF instance cannot
be redistributed into itself; a BGP source must be a router of the same device.

## Virtual links

**OSPF → Virtual Links**

Every area must touch the backbone. When one cannot, a **virtual link** ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)
§15) tunnels the backbone through a **transit area** to the remote ABR.

| Field | Meaning |
| --- | --- |
| Transit area | The area the link crosses. It must be a **standard** area of the same instance, and cannot be deleted while a link crosses it. |
| Remote router ID | Router ID of the ABR at the other end. One link per transit area and remote router. |
| Timers, TTL security, authentication | The same as an [interface](#interfaces). Authentication falls back to the backbone's, then the instance's, and its type must agree with the backbone's. |

## Summary addresses

**OSPF → Summary Addresses**

Summarization of the **external routes** an ASBR redistributes: one LSA for the prefix replaces many.
It reduces the size of the routing table and of the database.

| Field | Meaning |
| --- | --- |
| Prefix | IPv4 prefix without host bits set (`10.0.0.0/8`, not `10.0.0.1/8`). One summary per prefix per instance. |
| Not advertise | Suppress the routes covered by the prefix instead of summarizing them. |
| Route tag | Tag set on the summary route. |

## Area ranges

**OSPF → Area Ranges**

An **area range** is summarization at an **area border router** ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)
appendix C.2): the ABR advertises one summary for all the area's routes inside the range to the other
areas.

| Field | Meaning |
| --- | --- |
| Area | The area whose routes are summarized. |
| Prefix | IPv4 range without host bits. One per area. |
| Range type | **Summary** of intra-area routes, or on an NSSA **NSSA external**: the addresses of the type 7 LSAs translated into type 5 ([RFC 3101](https://www.rfc-editor.org/rfc/rfc3101) §3.2). NSSA external ranges only exist on NSSA areas; the same prefix can be both a summary and an NSSA range. |
| Advertise | **Advertise** the range as one route, or **DoNotAdvertise** to hide the routes of the range. |

## Neighbors

**OSPF → Neighbors**

On **non-broadcast (NBMA)** and **point-to-multipoint** networks routers cannot find each other with
multicast Hellos, so the neighbors are configured by hand ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328)
appendices C.5 and C.6). A neighbor is identified by its IP address on the network.

| Field | Meaning |
| --- | --- |
| OSPF interface | The interface the neighbor is reached through. Its network type must be Non Broadcast or one of the Point to Multipoint types; other types have no configured neighbors. |
| IP address | The neighbor's interface address: a unicast IPv4 address on a network of the interface, and not the interface's own. One entry per address per interface. |
| Priority | Eligibility of the neighbor to become DR, 0 to 255 (0 = not eligible). Required on non-broadcast networks, where a DR is elected; not used on point-to-multipoint ones. |
| Poll interval | Seconds between Hellos while the neighbor is down, much larger than the hello interval. Non-broadcast only. |

## Prefix SIDs

**OSPF → Prefix SIDs**

With **segment routing** the router advertises a *Segment Identifier* for each prefix, and traffic is
steered by stacks of labels ([RFC 8665](https://www.rfc-editor.org/rfc/rfc8665), using the extended
prefix LSA of [RFC 7684](https://www.rfc-editor.org/rfc/rfc7684)). It needs segment routing and opaque LSAs on the instance.

| Field | Meaning |
| --- | --- |
| Prefix | The IPv4 prefix the SID is for (no host bits). |
| SID type | **Index into the SRGB** (the label is the block's start plus the index) or **Absolute label** (a local MPLS label, 16 to 1048575). An index must fit the SRGB. |
| Algorithm | **SPF** (0) or **Strict SPF** (1). |
| Node SID | The prefix identifies the router itself (N flag, RFC 7684). It must be a host prefix (/32). |
| No PHP | The penultimate hop must not remove the label (NP flag, RFC 8665). |
| Explicit null | Upstream neighbors replace the SID with an explicit null label (E flag, RFC 8665). |

One SID per prefix and algorithm. You cannot disable segment routing while SIDs exist, nor shrink the
SRGB below an existing index.

## Bulk import (CSV)

Every OSPF object can be imported from a CSV file (**Import** button of each menu entry). The first
column is always the **device** (its name), because the names of instances and the area IDs are only
unique inside a device: the other columns are looked up on that device. Columns with a default can be
left out. Choices are written as in the forms (`point_to_point`, `static`, ...); a list such as the OSPF
route types is separated by commas.

| Import | Columns that identify the row (besides the fields of the object) |
| --- | --- |
| Instance | `device`, `name`, `router_id`, `vrf` (optional), `address_family` (`ipv4` by default) |
| Area | `device`, `instance` (name), `area_id` |
| Interface | `device`, `instance`, `area` (the area ID), `interface` (name), `network_type` |
| Network | `device`, `ospf_interface` (name of the interface), `ip_address` (with its mask) |
| Neighbor | `device`, `ospf_interface`, `ip_address`, `priority`, `poll_interval` |
| Redistribution | `device`, `instance`, `protocol`, and the source: `ospf_source`, `eigrp_source`, `bgp_source` or `isis_source` (names); `route_policy` (name) |
| Virtual link | `device`, `instance`, `transit_area` (the area ID), `remote_router_id` |
| Summary address | `device`, `instance`, `prefix` |
| Area range | `device`, `instance`, `area` (the area ID), `prefix`, `range_type` |
| Prefix SID | `device`, `instance`, `prefix`, `sid`, `sid_type`, `algorithm` |

The same validations as in the forms apply, row by row.

## Changes that would break OSPF objects

OSPF objects are checked when they are saved, and the objects they depend on are checked when *they*
change:

- An **area** cannot change to a stub or NSSA type while virtual links cross it, nor leave the NSSA type
  while it has type 7 to type 5 ranges.
- The **router ID** of an instance cannot be the remote router of one of its virtual links.
- A NetBox **interface** with an OSPF interface cannot move to another device or VRF so that it no
  longer matches the instance, and an **IP address** used by an OSPF network cannot be moved to another
  interface or changed so that the network stops being valid. The change is refused and the message
  names the OSPF objects it would break.

In lists and selects, an OSPF interface is shown as `device interface` and an area as
`area (instance)`, so equal names on different devices or instances can be told apart.

## What happens when you delete things

| Delete | Result |
| --- | --- |
| A route policy | Refused while an OSPF instance uses it as its import or export policy, or a redistribution uses it. |
| An OSPF instance | Refused while it has interfaces. Its unused areas, redistributions, virtual links, summary addresses and Prefix SIDs go with it. |
| An area | Refused while it has interfaces; its ranges go with it. |
| An OSPF interface | Its networks and neighbors go with it. |
| A device | Its OSPF interfaces go with it. |
| An IP address in IPAM | The OSPF network that used it is removed. |

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices. The **Authentication** group is the same in the instance, the area, the interface and the virtual link, and is written out in each.

```text
OSPF instance
├─ Identity: name · device → Device · vrf → VRF · address_family {IPv4 (OSPFv2) | IPv6 (OSPFv3)} · router_id · ospf_instance_id
├─ Authentication: authentication {Simple Password | Message Digest | Authentication Trailer | Key Chain | Null Authentication}
│     · passphrase · authentication_key_id · show_md5?
│     · message_digest_algorithm {MD5 | HMAC-SHA-1 | HMAC-SHA-256 | HMAC-SHA-384 | HMAC-SHA-512}
│     · key_chain
├─ Default route: default_originate? · default_originate_always? · default_originate_metric
│     · default_originate_metric_type {Type 1 (E1) | Type 2 (E2)}
├─ Route policies: import_policy → Route policy · export_policy → Route policy
├─ Timers: spf_initial_delay · spf_short_delay · spf_long_delay · spf_time_to_learn · spf_holddown
│     · lsa_min_interval · lsa_min_arrival
├─ Maintenance: max_metric_router_lsa? · max_metric_on_startup
│     · graceful_restart {Disabled | Planned restarts only | Planned and unplanned restart}
│     · graceful_restart_period · graceful_restart_helper?
│     · graceful_restart_helper_strict_lsa_checking?
├─ Limits: max_lsa · max_lsa_threshold · max_lsa_warning_only?
│     · external_lsdb_limit · exit_overflow_interval
├─ Routing: reference_bandwidth · maximum_paths · default_metric · rfc1583_compatibility?
│     · distance_intra_area · distance_inter_area · distance_external
├─ Operation: log_adjacency_changes? · log_adjacency_changes_detail?
│     · bfd_all_interfaces? · passive_interface_default?
├─ Extensions: opaque_capability? · te_router_address · segment_routing?
│     · srgb_start · srgb_size · ldp_sync? · ldp_sync_holddown
│
├─ Area
│   ├─ instance → OSPF instance · area_id
│   ├─ area_type {Standard Area | Backbone Area | Stub Area | Totally Stubby Area
│   │             | Not-So-Stubby Area | Totally Not-So-Stubby Area}
│   ├─ default_cost · traffic_engineering? · fast_reroute?
│   ├─ NSSA: nssa_translate_always? · nssa_no_redistribution? · nssa_default_originate?
│   ├─ Authentication: authentication · passphrase · authentication_key_id · show_md5?
│   │     · message_digest_algorithm · key_chain
│   ├─ Area range
│   │     area → Area · prefix · advertise?
│   │     · range_type {Summary of intra-area routes | NSSA external (type 7 to type 5)}
│   └─ Interface
│       ├─ instance → OSPF instance · area → Area · interface → Interface
│       ├─ Basics: passive? · priority · bfd? · cost
│       │     · network_type {Broadcast | Non Broadcast | Point to Point | Point to Multipoint
│       │                     | Point to Multipoint Non Broadcast | Loopback}
│       ├─ Timers: hello_interval · dead_interval · retransmit_interval · transmit_delay
│       ├─ Security: ttl_security? · ttl_security_hops
│       ├─ Authentication: authentication · passphrase · authentication_key_id · show_md5?
│       │     · message_digest_algorithm · key_chain
│       ├─ Options: prefix_suppression? · database_filter_all_out? · flood_reduction?
│       │     · demand_circuit? · unnumbered? · mtu_ignore? · ldp_sync?
│       ├─ Traffic engineering: te_metric · te_max_reservable_bandwidth · te_admin_group
│       │     · adjacency_sid
│       ├─ Fast reroute: fast_reroute {Loop-Free Alternate (RFC 5286) | Remote LFA (RFC 7490)}
│       ├─ Network: ospf_interface → OSPF interface · ip_address → IP address
│       └─ Neighbor: ospf_interface → OSPF interface · ip_address · priority · poll_interval
├─ Redistribution
│     instance → OSPF instance · protocol {Connected | Static | EIGRP | BGP | OSPF | IS-IS}
│     · ospf_source → OSPF instance · eigrp_source → EIGRP router · bgp_source → BGP router
│     · isis_source → IS-IS instance · metric · metric_type {Type 1 (E1) | Type 2 (E2)}
│     · subnets? · route_tag · route_policy → Route policy · ospf_match
├─ Summary address: instance → OSPF instance · prefix · not_advertise? · route_tag
├─ Virtual link
│     instance → OSPF instance · transit_area → Area · remote_router_id
│     ├─ Timers: hello_interval · dead_interval · retransmit_interval · transmit_delay
│     ├─ Security: ttl_security? · ttl_security_hops
│     └─ Authentication: authentication · passphrase · authentication_key_id · show_md5?
│           · message_digest_algorithm · key_chain
└─ Prefix SID
      instance → OSPF instance · prefix · sid_type {Index into the SRGB | Absolute label (local)}
      · sid · algorithm {SPF | Strict SPF} · node_sid? · no_php? · explicit_null?
```

## Standards behind OSPF

| RFC | What it gives the plugin |
| --- | --- |
| [RFC 5340](https://www.rfc-editor.org/rfc/rfc5340) | OSPFv3: IPv6 instances (no networks, link-local neighbors) |
| [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) | The protocol: router ID, areas, interface types and timers, authentication, virtual links, ranges, external route types |
| [RFC 3101](https://www.rfc-editor.org/rfc/rfc3101) | NSSA areas |
| [RFC 3623](https://www.rfc-editor.org/rfc/rfc3623) | Graceful restart |
| [RFC 3630](https://www.rfc-editor.org/rfc/rfc3630) | Traffic engineering extensions |
| [RFC 4136](https://www.rfc-editor.org/rfc/rfc4136), [RFC 1793](https://www.rfc-editor.org/rfc/rfc1793) | Flood reduction, demand circuits |
| [RFC 5082](https://www.rfc-editor.org/rfc/rfc5082) | TTL security |
| [RFC 5250](https://www.rfc-editor.org/rfc/rfc5250) | Opaque LSAs |
| [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286), [RFC 7490](https://www.rfc-editor.org/rfc/rfc7490) | Loop-free alternates, remote LFA |
| [RFC 5443](https://www.rfc-editor.org/rfc/rfc5443) | LDP/IGP synchronization |
| [RFC 5709](https://www.rfc-editor.org/rfc/rfc5709) | HMAC-SHA authentication |
| [RFC 7166](https://www.rfc-editor.org/rfc/rfc7166) | Authentication trailer of OSPFv3 |
| [RFC 6549](https://www.rfc-editor.org/rfc/rfc6549) | Multi-instance OSPFv2 |
| [RFC 6860](https://www.rfc-editor.org/rfc/rfc6860) | Hiding transit-only networks |
| [RFC 6987](https://www.rfc-editor.org/rfc/rfc6987) | Max-metric router LSA |
| [RFC 7684](https://www.rfc-editor.org/rfc/rfc7684), [RFC 8665](https://www.rfc-editor.org/rfc/rfc8665) | Extended prefix/link LSAs and segment routing |
| [RFC 8405](https://www.rfc-editor.org/rfc/rfc8405) | SPF back-off |
| [RFC 1765](https://www.rfc-editor.org/rfc/rfc1765) | Database overflow |
