# BGP

**Routing → BGP**

BGP-4 ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)) is the protocol that carries routes between
autonomous systems and, inside a network, between routers (iBGP). The plugin models a BGP
configuration with the same layers a router has: the **router** (your AS), the **scopes** (global
table or a VRF), the **address families** negotiated in each scope, and the **peers**, plus
**templates** so you do not repeat yourself.

## How it is organized

```
BGP router (ASN, assigned to a device / site / region / cluster / VM)
 ├─ Settings (router-wide options)
 ├─ Templates available to its peers: session, peer, policy
 └─ Scope (global table, or one VRF)
     ├─ Settings
     ├─ Address family (IPv4 unicast, VPNv4, EVPN, ...)
     │   └─ Peer address family ── policy (prefix lists, route maps)
     └─ Peer (neighbor IP address)
         ├─ Settings
         └─ Peer address families
```

Build it in this order: **ASN** (NetBox IPAM) → **Router** → **Scope** → **Address family** →
**Peer** → **Peer address family**. Templates can be created at any time and attached later.

## Routers

**BGP → Routers**

A router is "this AS, on this device (or site, region, cluster...)".

| Field | Meaning |
| --- | --- |
| ASN | A NetBox ASN (**IPAM → ASNs**). Four-octet ASNs are fine ([RFC 6793](https://www.rfc-editor.org/rfc/rfc6793)). |
| Name | Optional label. |
| Assigned to | What the BGP process runs on: a device, virtual machine, site, location, region, site group, cluster or cluster group. Assign it to a *site* or *region* when the same BGP configuration applies to all the devices there. |
| Tenant | Optional owner. |
| Session / Peer / Policy templates | The templates peers of this router may use. |

## Scopes

**BGP → Scopes**

A scope selects **where** the BGP configuration applies: the **global routing table** (no VRF) or a
single **VRF**. Per-VRF BGP, as used by VPN services ([RFC 4364](https://www.rfc-editor.org/rfc/rfc4364)),
has one scope per VRF.

## Address families

**BGP → Address Families**

The kinds of routes the router exchanges in a scope. BGP carries more than IPv4 thanks to the
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

A scope can have each family once.

## Peers

**BGP → Peers**

A peer is one BGP neighbor.

| Field | Meaning |
| --- | --- |
| Scope | The router scope the session belongs to (global or a VRF). |
| Peer | The neighbor's IP address (a NetBox IP address). |
| Source | The local address to open the session from, usually a loopback. |
| Remote AS | The neighbor's ASN. Same as the router's ASN means iBGP, different means eBGP. |
| Local AS | Optional, a different ASN to present to this neighbor (used in AS migrations; a vendor feature). |
| Enabled | Administratively enable or disable the session. |
| Status | **Active**, **Planned**, **Offline** or **Failed**: the lifecycle of the session in your documentation (it is not read from the network). |
| BFD profile | Detect failure fast, see [BFD](../bfd.md). |
| TTL | The TTL of the session's packets. For directly connected eBGP set **255** and the expected hop count so the router drops spoofed packets: this is the *Generalized TTL Security Mechanism*, [RFC 5082](https://www.rfc-editor.org/rfc/rfc5082). |
| Password | The shared secret of the TCP session, stored as plain text. BGP session protection with a password is the TCP MD5 option, [RFC 2385](https://www.rfc-editor.org/rfc/rfc2385) (superseded in the standards by TCP-AO, [RFC 5925](https://www.rfc-editor.org/rfc/rfc5925)). |
| Peer template / Session template | Inherit settings, see [Templates](#templates). |
| Tenant | Optional owner. |

## Peer address families

**BGP → Peer Address Families**

What a neighbor exchanges in each address family and under which **policy**: an address family of the
scope (for example IPv4 unicast) plus the filters applied to that peer in that family.

| Field | Meaning |
| --- | --- |
| Assigned to | A peer or a peer template. |
| Address family | One of the scope's address families. |
| Enabled | Activate the family for the neighbor. |
| Prefix list in / out | Prefix lists ([routing objects](../routing-objects.md#prefix-lists)) that filter what is received from and sent to the neighbor. |
| Route map in / out | Route maps that filter or modify routes in each direction. |
| Policy template | Apply a [policy template](#policy-templates). |

## Templates

Templates remove repetition: define the shared part once and make peers point at it. There are three
kinds because they inherit different things.

### Session templates

**BGP → Session Templates**: the properties of the **TCP session**. They can inherit from a *parent*
session template, so you can build a base "all eBGP peers" template and refine it per customer type.

Fields: parent, enabled, local AS, remote AS, TTL, BFD profile, password, tenant.

### Policy templates

**BGP → Policy Templates**: the **filters** (prefix lists in/out, route maps in/out). A policy template
can have several *parents*; a peer address family points at one.

### Peer templates

**BGP → Peer Templates**: a **group of neighbors** that share a remote AS and per-address-family
settings (the equivalent of a *peer group*). A peer points at one with *Peer template*.

> **Note.** The plugin records which template each peer uses and what each template contains. It does not
> compute the final effective configuration of a peer; your configuration templates or automation
> combine them.

## Settings

**BGP → Settings**

Option-by-option settings that do not need their own field. A setting is a **key and a value** assigned
to a router, a scope, an address family or a peer, so you can set an option at the level it applies to.
Values are validated by type (yes/no, number or IP address).

| Key | Type | Meaning |
| --- | --- | --- |
| Router ID | IP address | The BGP identifier, unique in the AS ([RFC 6286](https://www.rfc-editor.org/rfc/rfc6286)). |
| AS Dot Notation | yes/no | Write four-octet ASNs as `high.low` ([RFC 5396](https://www.rfc-editor.org/rfc/rfc5396)). |
| Graceful Restart | yes/no | Keep forwarding while the neighbor's BGP restarts ([RFC 4724](https://www.rfc-editor.org/rfc/rfc4724)). |
| Additional Paths (send / receive / install) | number | Advertise or accept more than one path per prefix ([RFC 7911](https://www.rfc-editor.org/rfc/rfc7911)). |
| Keep Alive, Hold Time | seconds | Session timers: the hold time is negotiated in the OPEN message and keepalives are sent about every third of it ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)). |
| Default Metric | number | The metric (MED, [RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)) given to redistributed routes. |
| Default Originate | yes/no | Advertise a default route to the neighbor (vendor feature). |
| eBGP / iBGP / MP eBGP / MP iBGP Distance | number | Administrative distance of routes learned from each kind of session (vendor feature). |
| Maximum Paths, Maximum Paths (secondary) | number | Equal-cost multipath: how many paths are installed (vendor feature). |
| Auto summary | yes/no | Summarize routes at classful boundaries (legacy; disabled on modern platforms). |

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

The **Settings** (key / value pairs) can be attached to a router, a scope, an address family, a peer or a peer address family. The key is one of: Router ID · Auto summary · Additional Paths (install) · Additional Paths (receive) · Additional Paths (send) · AS Dot Notation · Graceful Restart · Default Originate · Default Metric · eBGP Distance · iBGP Distance · MP eBGP Distance · MP iBGP Distance · Maximum Paths · Maximum Paths (secondary) · Keep Alive · Hold Time.

```text
BGP router
├─ name · asn → ASN · tenant → Tenant
├─ Assigned to: Region | Site | Site group | Location | Device | Cluster | Virtual machine
├─ Templates in use: session_templates → Session template (several)
│     · policy_templates → Policy template (several) · peer_templates → Peer template (several)
├─ Settings: key · value
│
└─ Scope
    ├─ router → BGP router · vrf → VRF · tenant → Tenant
    ├─ Settings: key · value
    ├─ Address family
    │     scope → Scope · tenant → Tenant
    │     · address_family {IPv4 | IPv6 | VPNv4 | VPNv6} Unicast / Multicast / Flowspec
    │                      · NSAP · L2VPN VPLS · L2VPN EVPN · LINK-STATE · RTFILTER
    │     └─ Settings: key · value
    └─ Peer
        ├─ name · scope → Scope · tenant → Tenant
        ├─ Session: peer → IP address · source → IP address · remote_as → ASN · local_as → ASN
        │     · enabled? · status {Active | Planned | Offline | Failed} · ttl · password
        │     · bfd → BFD profile
        ├─ Templates: peer_group → Peer template · peer_session → Session template
        ├─ Settings: key · value
        └─ Peer address family
              assigned to: Peer or Peer template · address_family → Address family
              · peer_policy → Policy template · enabled? · tenant → Tenant
              · prefixlist_in → Prefix list · prefixlist_out → Prefix list
              · routemap_in → Route map · routemap_out → Route map
              └─ Settings: key · value

Session template
└─ name · parent → Session template · enabled? · local_as → ASN · remote_as → ASN · ttl
   · bfd → BFD profile · password · tenant → Tenant

Policy template
└─ name · parents → Policy template (several) · enabled? · tenant → Tenant
   · prefixlist_in → Prefix list · prefixlist_out → Prefix list
   · routemap_in → Route map · routemap_out → Route map

Peer template
└─ name · remote_as → ASN · enabled? · tenant → Tenant
   · address_families → Peer address family (several)
```
