# OSPF

**Routing → OSPF**

OSPF (Open Shortest Path First) is a link-state interior routing protocol: every router floods
descriptions of its links, and each one computes the shortest paths on its own. The plugin models
**OSPF version 2 for IPv4**, defined in [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328), and the
extensions that real networks use on top of it. Defaults and ranges follow the RFC, and each feature
below says which RFC it comes from.

> **Scope.** OSPFv3 (IPv6, [RFC 5340](https://www.rfc-editor.org/rfc/rfc5340)) is not modelled yet. Networks,
> summary addresses and ranges accept IPv4 only, and the router ID is an IPv4-style identifier.

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
| Router ID | The 32-bit identifier of the router in the OSPF domain ([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) §C.1), written like an IPv4 address. It must be a valid IPv4 address, not `0.0.0.0` and without a mask, and it should be unique in the network. |
| Instance ID | Lets several OSPF processes run over the same link: routers form an adjacency only with a neighbor that has the same ID ([RFC 6549](https://www.rfc-editor.org/rfc/rfc6549)). Default 0. |

### Default route

| Field | Meaning |
| --- | --- |
| Default originate | Advertise a default route (`0.0.0.0/0`) into OSPF. By default it is advertised only while the router has a default route itself. |
| Always | Advertise it even when no default route exists locally. |
| Metric, metric type | Metric of the originated route, and whether it is **Type 1 (E1)** or **Type 2 (E2)** (see [redistribution](#redistribution)). These options require *Default originate*. |

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

## Authentication

OSPFv2 can authenticate its packets so that only trusted routers join the domain
([RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) appendix D). The same block of fields appears on
**instances, areas, interfaces and virtual links**:

| Type | Meaning |
| --- | --- |
| Null | No authentication. |
| Simple Password | A clear-text password, up to **8 characters**. Weak: only protects against mistakes. |
| Message Digest | A cryptographic digest with a **key ID (0 to 255)** and a key of up to **16 characters** for MD5. |
| Key Chain | The name of a key chain configured on the device, which rotates keys. No key is stored here. |

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
| Route policy | Name of a route policy/route map applied to the routes. |
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

## What happens when you delete things

| Delete | Result |
| --- | --- |
| An OSPF instance | Refused while it has interfaces. Its unused areas, redistributions, virtual links, summary addresses and Prefix SIDs go with it. |
| An area | Refused while it has interfaces; its ranges go with it. |
| An OSPF interface | Its networks and neighbors go with it. |
| A device | Its OSPF interfaces go with it. |
| An IP address in IPAM | The OSPF network that used it is removed. |

## Standards behind OSPF

| RFC | What it gives the plugin |
| --- | --- |
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
| [RFC 6549](https://www.rfc-editor.org/rfc/rfc6549) | Multi-instance OSPFv2 |
| [RFC 6860](https://www.rfc-editor.org/rfc/rfc6860) | Hiding transit-only networks |
| [RFC 6987](https://www.rfc-editor.org/rfc/rfc6987) | Max-metric router LSA |
| [RFC 7684](https://www.rfc-editor.org/rfc/rfc7684), [RFC 8665](https://www.rfc-editor.org/rfc/rfc8665) | Extended prefix/link LSAs and segment routing |
| [RFC 8405](https://www.rfc-editor.org/rfc/rfc8405) | SPF back-off |
| [RFC 1765](https://www.rfc-editor.org/rfc/rfc1765) | Database overflow |
