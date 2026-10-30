# BGP

**Routing → BGP**

BGP-4 ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)) is the protocol that carries routes between
autonomous systems and, inside a network, between routers (iBGP). The plugin models a BGP
configuration with the same layers a router has, and the same shape as [OSPF](ospf.md): an
**instance** per device and VRF, the **address families** it negotiates, the **peers** (neighbors)
and **peer groups** that share their configuration.

## How it is organized

```
BGP instance (device, VRF or global table, ASN)
 ├─ Address family (IPv4 unicast, VPNv4, EVPN, ...)
 ├─ Peer group ── session options · Peer address family (policy)
 └─ Peer (neighbor IP address) ── session options · Peer address family (policy)
```

Build it in this order: **ASN** (NetBox IPAM) → **Instance** → **Address family** → **Peer group**
(optional) → **Peer** → **Peer address family**.

## Instances

**BGP → Instances**

An instance is "this AS, on this device, in this routing table". A device has **one instance per VRF**
(one for the global table and one for each VRF that runs BGP, as used by VPN services,
[RFC 4364](https://www.rfc-editor.org/rfc/rfc4364)).

| Field | Meaning |
| --- | --- |
| Name | A label of the instance. |
| Device | The device the BGP process runs on. |
| VRF | Empty for the global routing table. |
| ASN | A NetBox ASN (**IPAM → ASNs**). Four-octet ASNs are fine ([RFC 6793](https://www.rfc-editor.org/rfc/rfc6793)). |
| Router ID | The BGP identifier, a 32-bit value written as an IPv4 address and never `0.0.0.0` ([RFC 6286](https://www.rfc-editor.org/rfc/rfc6286)). |
| AS dot notation | Write four-octet ASNs as `high.low` ([RFC 5396](https://www.rfc-editor.org/rfc/rfc5396)). |
| Graceful restart | Keep forwarding while the neighbor's BGP restarts ([RFC 4724](https://www.rfc-editor.org/rfc/rfc4724)). |
| Restart time, Stale paths time, Helper only | The timers of graceful restart (they need *Graceful restart*): the restart time is advertised to the neighbors (0 to 4095 seconds, 12 bits), the stale paths time is how long the routes of a restarting neighbor are kept, *helper only* helps the neighbors to restart without restarting gracefully itself. |
| Import policy, Export policy | A [route policy](../routing-objects.md#route-policies) for every neighbor of the instance, see [Route policy](#route-policy). |
| Tenant | Optional owner. |

## Address families

**BGP → Address Families**

The kinds of routes the instance exchanges. BGP carries more than IPv4 thanks to the
multiprotocol extensions ([RFC 4760](https://www.rfc-editor.org/rfc/rfc4760)); each *address family*
is negotiated separately between the peers. The plugin offers:

| Family | Used for | Standard |
| --- | --- | --- |
| IPv4 Unicast, IPv6 Unicast | Normal internet and internal routing | RFC 4271, RFC 4760 |
| IPv4 / IPv6 Multicast | Multicast routing information | RFC 4760 |
| VPNv4 / VPNv6 (Unicast and Multicast) | L3VPN: customer routes with route distinguishers | [RFC 4364](https://www.rfc-editor.org/rfc/rfc4364) (VPNv4), [RFC 4659](https://www.rfc-editor.org/rfc/rfc4659) (VPNv6) |
| IPv4 / IPv6 / VPNv4 / VPNv6 Flowspec | Distributing traffic filtering rules | [RFC 8955](https://www.rfc-editor.org/rfc/rfc8955), [RFC 8956](https://www.rfc-editor.org/rfc/rfc8956) |
| L2VPN VPLS | Layer 2 VPN over BGP | [RFC 4761](https://www.rfc-editor.org/rfc/rfc4761) |
| L2VPN EVPN | Ethernet VPN, data-center overlays | [RFC 7432](https://www.rfc-editor.org/rfc/rfc7432) |
| RTFILTER | Route-target constrained distribution, to send VPN routes only where wanted | [RFC 4684](https://www.rfc-editor.org/rfc/rfc4684) |
| LINK-STATE | Topology information for controllers | [RFC 7752](https://www.rfc-editor.org/rfc/rfc7752) |
| NSAP | Legacy OSI addresses | RFC 4760 (address family registry) |

An instance can have each family once. Options of the family:

| Field | Meaning |
| --- | --- |
| Maximum paths | Equal-cost multipath: how many paths are installed (vendor feature). |
| Default metric | The metric (MED, [RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)) given to redistributed routes. |
| Default originate | Advertise a default route to the neighbors (vendor feature). |
| Auto summary | Summarize routes at classful boundaries (legacy; disabled on modern platforms). |
| eBGP / iBGP distance | Administrative distance of the routes learned from each kind of session (vendor feature). |
| Additional paths (send / receive / install) | Advertise or accept more than one path per prefix ([RFC 7911](https://www.rfc-editor.org/rfc/rfc7911)). |
| Long-lived stale time | Seconds the routes of a neighbor that went down are kept, marked `LLGR_STALE` (long-lived graceful restart, [RFC 9494](https://www.rfc-editor.org/rfc/rfc9494), up to 16777215; it needs *Graceful restart* on the instance). |

## Peer groups

**BGP → Peer Groups**

A peer group is a **group of neighbors that share their configuration** (the same as the *peer
group* of FRR, Junos, Arista or IOS). It belongs to one instance and has the same session options as a
peer (below) plus its own [peer address families](#peer-address-families) with the filtering of the group.
A peer that points at a group takes its options from it; whatever the peer sets itself wins.

> **Note.** The plugin records which group each peer uses and what each group contains; a peer shows its
> own values. `BGPPeer.effective(field)` (used by the validation) gives the value the peer ends up
> with. Your configuration templates or automation combine them.

## Peers

**BGP → Peers**

A peer is one BGP neighbor. A neighbor address can be used once per instance
([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271): one session per neighbor).

| Field | Meaning |
| --- | --- |
| Instance | The instance (device and VRF) the session belongs to. |
| Peer | The neighbor's IP address (a NetBox IP address in the VRF of the instance). |
| Source | The local address to open the session from, usually a loopback of the device. |
| Peer group | Inherit the options of a [peer group](#peer-groups) of the same instance. |
| Status | **Active**, **Planned**, **Offline** or **Failed**: the lifecycle of the session in your documentation (it is not read from the network). |
| Tenant | Optional owner. |

Session options, on a peer and on a peer group (the peer needs a remote AS, its own or its group's):

| Field | Meaning |
| --- | --- |
| Remote AS | The neighbor's ASN. Same as the instance's ASN means iBGP, different means eBGP. |
| Local AS | Optional, a different ASN to present to this neighbor (used in AS migrations; a vendor feature). |
| Enabled | Administratively enable or disable the session. |
| BFD profile | Detect failure fast, see [BFD](../bfd.md). |
| eBGP multihop | Maximum hops to a neighbor that is not directly connected (an eBGP neighbor is expected one hop away). |
| TTL security hops | *Generalized TTL Security Mechanism*, [RFC 5082](https://www.rfc-editor.org/rfc/rfc5082): the neighbor is at most this many hops away and packets with a lower TTL are dropped. It cannot be used together with *eBGP multihop*. |
| Passive | Wait for the neighbor to open the TCP connection instead of opening it ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271) section 8). |
| Import policy, Export policy | See [Route policy](#route-policy). |
| Password | The shared secret of the TCP session, stored as plain text. The TCP MD5 option, [RFC 2385](https://www.rfc-editor.org/rfc/rfc2385), is superseded by TCP-AO ([RFC 5925](https://www.rfc-editor.org/rfc/rfc5925)). |
| Keepalive time, Hold time | Seconds. The hold time is negotiated in the OPEN message: zero (no keepalives) or at least 3; keepalives are sent about every third of it ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)). |

## Peer address families

**BGP → Peer Address Families**

What a neighbor (or a peer group) exchanges in each address family and under which **policy**: an
address family of the instance (for example IPv4 unicast) plus the filters applied in that family.

| Field | Meaning |
| --- | --- |
| Peer / Peer group | The peer or the peer group it applies to (one of the two). |
| Address family | One of the instance's address families. |
| Enabled | Activate the family for the neighbor. |
| Prefix list in / out | Prefix lists ([routing objects](../routing-objects.md#prefix-lists)) that filter what is received from and sent to the neighbor. Their family (IPv4 or IPv6) must match the address family; families that carry no IP prefixes (EVPN, VPLS, link-state...) take none. |
| Import policy, Export policy | Route policies that filter or modify the routes received from and sent to the neighbor, see [Route policy](#route-policy). |
| Send community | Which communities are sent to the neighbor: standard ([RFC 1997](https://www.rfc-editor.org/rfc/rfc1997)), extended ([RFC 4360](https://www.rfc-editor.org/rfc/rfc4360)) and/or large ([RFC 8092](https://www.rfc-editor.org/rfc/rfc8092)). Cisco, Arista and FRR send none unless it is configured; Juniper sends them all. Empty uses the one of the peer group, else the platform default. |
| Next hop self, Remove private AS, Allow AS in | Advertise this router as the next hop; remove private ASNs from the AS path; accept routes with the local AS in the AS path up to that many times (vendor features). |
| Maximum prefixes | The number of prefixes accepted from the neighbor in this family. When exceeded the session is ceased ([RFC 4486](https://www.rfc-editor.org/rfc/rfc4486), subcode *Maximum Number of Prefixes Reached*). *Warning* is the percentage of the limit that logs a warning; *Action* is **Cease, restart after a time** (with the minutes to wait), **Cease, until cleared** or **Warning only**. |
## Route policy

A [route policy](../routing-objects.md#route-policies) can be set at five levels: the **instance** (for every
neighbor), the **peer group**, the **peer**, the **peer group's address family** and the **peer's address family**.
*Import* is what is accepted from the neighbor and *export* what is advertised to it
([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271) section 9). The **most specific wins**: the peer address
family, then the same family of the peer's group, then the peer, then its peer group, then the instance. The page
of a peer address family shows the *effective* policy and the level it comes from. A route policy in use cannot be
deleted.

**eBGP without policy (RFC 8212).** An eBGP speaker must not accept or advertise any route on a session that has
no explicit import and export policy ([RFC 8212](https://www.rfc-editor.org/rfc/rfc8212)). The page of a peer
or a peer group whose remote AS differs from the instance's lists, in a warning, the enabled address families
with no policy at any level. Nothing is blocked: the plugin only documents.

## Migrating from netbox-bgp

`manage.py migrate-netbox-bgp` creates one instance per device (every session needs a device and a
local ASN), its IPv4 and IPv6 unicast families, the peers and, where a session used a peer group, a copy
of that group in the instance of the device.

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a field that can be left empty (it then inherits, or is not set).

```text
BGP instance
├─ name · device → Device · vrf → VRF · asn → ASN · tenant → Tenant
├─ router_id · asdot? · graceful_restart? · graceful_restart_time · graceful_restart_stale_time
│     · graceful_restart_helper_only? · import_policy → Route policy · export_policy → Route policy
│
├─ Address family
│     instance → BGP instance · tenant → Tenant
│     · address_family {IPv4 | IPv6 | VPNv4 | VPNv6} Unicast / Multicast / Flowspec
│                      · NSAP · L2VPN VPLS · L2VPN EVPN · LINK-STATE · RTFILTER
│     · maximum_paths · default_metric · default_originate? · auto_summary?
│     · distance_ebgp · distance_ibgp
│     · additional_paths_send? · additional_paths_receive? · additional_paths_install?
│     · long_lived_stale_time
│
├─ Peer group
│     name · instance → BGP instance · tenant → Tenant
│     · remote_as → ASN · local_as → ASN · enabled? · bfd → BFD profile · password
│     · ebgp_multihop · ttl_security_hops · passive? · keepalive · hold_time
│     · import_policy → Route policy · export_policy → Route policy
│     └─ Peer address family (see below)
│
└─ Peer
      name · instance → BGP instance · tenant → Tenant
      · peer → IP address · source → IP address · peer_group → Peer group
      · status {Active | Planned | Offline | Failed}
      · remote_as → ASN · local_as → ASN · enabled? · bfd → BFD profile · password
      · ebgp_multihop · ttl_security_hops · passive? · keepalive · hold_time
      · import_policy → Route policy · export_policy → Route policy
      └─ Peer address family
            peer → Peer, or peer_group → Peer group · address_family → Address family
            · enabled? · tenant → Tenant
            · prefixlist_in → Prefix list · prefixlist_out → Prefix list
            · import_policy → Route policy · export_policy → Route policy
            · send_community {Standard | Extended | Large} · next_hop_self? · remove_private_as? · allowas_in
            · maximum_prefix · maximum_prefix_warning · maximum_prefix_action {Cease, restart | Cease, until cleared | Warning only}
            · maximum_prefix_restart
```
