# IS-IS

**Routing → IS-IS**

IS-IS (Intermediate System to Intermediate System) is a link-state interior routing protocol like
OSPF, popular in service-provider and data-center backbones. It was defined by ISO for OSI networks
(ISO/IEC 10589) and adapted to carry IP in
[RFC 1195](https://www.rfc-editor.org/rfc/rfc1195); IPv6 support is
[RFC 5308](https://www.rfc-editor.org/rfc/rfc5308). The plugin models the instances that run on your
devices, their levels and interfaces, authentication, and the modern segment-routing extensions.

## Concepts in two minutes

* **Levels.** IS-IS has two: **Level 1** routes inside an area, **Level 2** routes between areas (the
  backbone). A router can be Level-1, Level-2 only, or **Level-1-2** (both).
* **NET (Network Entity Title).** The address of the router in the form `49.0001.0000.0000.0001.00`:
  an authority/format part, the **area** (`49.0001`), a 6-byte **system ID** (`0000.0000.0001`, unique
  per router) and a final `00`.
* **Metric style.** *Narrow* metrics are limited to 63 per link; *wide* metrics are 24 bits and are
  required for traffic engineering and segment routing ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305)).

## How it is organized

```
IS-IS instance (a process on a device, optionally in a VRF)
 ├─ Level (Level-1 / Level-2 settings of the instance)
 ├─ Segment routing (SR-MPLS, SRv6, SRGB/SRLB)
 ├─ Flex-Algo        ├─ SRv6 locator        └─ Settings
 ├─ Redistribution   ├─ Summary address     └─ Route leak
 ├─ Area address (more NETs for migrations and area merges)
 └─ Interface (device interface + address family)
     ├─ Interface level (per-level metric and hello settings)
     ├─ Prefix-SID
     └─ Settings
```

Every list can be filtered by the attributes of its model (for instances: metric style, fast reroute, overload bit, traffic engineering, authentication type, distance and so on; for interfaces: BFD, FRR, mesh group, timers) and **every object type can be edited in bulk**, not only instances and interfaces.

## Instances

**IS-IS → Instances**

| Field | Meaning |
| --- | --- |
| Device, VRF | Where the process runs. IS-IS can run once per VRF. |
| Process tag | The name of the process (`router isis <tag>`); empty for the unnamed process. Unique per device. |
| NET | The Network Entity Title: hex bytes with optional dots, an area address (1-13 bytes, starting with the AFI), a 6-byte system ID and an N-selector that must be `00`, at most 20 bytes in all (ISO 10589, RFC 1195). Empty is allowed while you are drafting. |
| IS type | **Level-1**, **Level-2 only** or **Level-1-2**. Empty means the platform default (Level-1-2). |
| Metric style | **Wide**, **Narrow** or **Transition** (both, for migrating between the two). Empty means the platform default. |
| Overload bit | Set the *overload bit*: other routers stop using this router for **transit** traffic, while still reaching its own prefixes (ISO 10589). Used for maintenance. |
| Overload on startup, timeout | Set it for a number of seconds after boot so the router joins the network gradually. |
| Suppress / ignore attached bit | The *attached bit* tells Level-1 routers that this Level-1-2 router reaches other areas, so they use it as a default route. *Suppress* stops the router from setting it; *ignore* stops it from installing the default route toward routers that do (ISO 10589). |
| Distance | Administrative distance, 1-255. |
| Maximum paths | Equal-cost paths installed (ECMP), at least 1. |
| Reference bandwidth | Mbps used to derive default interface metrics. |
| Traffic engineering | Enable IS-IS TE extensions ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305)). |

Ranges that are checked when you save: the maximum wait cannot be less than the initial wait, the LSP refresh interval must be less than the LSP lifetime (both 1-65535 s), the LSP MTU is at least 512 bytes, and the overload timeout needs *overload on startup*. Metrics are 1-63 with the narrow style and 1-16777214 otherwise ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305)); hello interval, CSNP and retransmit intervals are 1-65535 s, the hello multiplier 2-1000 and the DIS priority 0-127.

### Route policies

| Field | Meaning |
| --- | --- |
| Import policy | Optional [route policy](../routing-objects.md#route-policies) that filters the routes IS-IS **installs** in the routing table. |
| Export policy | Optional route policy that filters the routes IS-IS **advertises or takes from other sources** (redistribution into IS-IS). |

A route policy that an instance uses **cannot be deleted**: choose another one, or clear the field, first. The policy is per instance; the leaking of routes between levels ([RFC 5302](https://www.rfc-editor.org/rfc/rfc5302)) is modelled by [Route leaking](#route-leaking), and the redistribution of other protocols by [Redistribution](#redistribution).

### Timers

| Field | Meaning |
| --- | --- |
| SPF initial / maximum wait | Delay before recomputing paths after a change, and the longest back-off (ms), see [RFC 8405](https://www.rfc-editor.org/rfc/rfc8405). |
| LSP initial / maximum wait | The same for generating a new LSP (ms). |
| LSP lifetime, refresh interval, MTU | How long a LSP lives, how often it is refreshed (seconds) and the size limit of a LSP (bytes). |

### Fast reroute and micro-loops

| Field | Meaning | Standard |
| --- | --- | --- |
| Fast reroute | Precompute a backup for every route: **LFA**, **Remote LFA** or **TI-LFA**. Turn on per interface with *FRR* below. | [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286), [RFC 7490](https://www.rfc-editor.org/rfc/rfc7490); TI-LFA is an IETF draft for segment routing |
| Micro-loop avoidance | Delay forwarding after a change to avoid short-lived loops while routers converge. | [RFC 8333](https://www.rfc-editor.org/rfc/rfc8333) |

### Authentication

IS-IS has authentication in four places (the interface hello exists both on the interface and, per level, on the interface level); each takes a **type** and a **key**, and one without the
other is refused:

| Where | Protects |
| --- | --- |
| **Area** password (instance) | LSPs and SNPs of Level 1. |
| **Domain** password (instance) | LSPs and SNPs of Level 2. |
| **Level** | LSPs of that level, set on the [Level](#levels) object. |
| **Hello** (interface) | The hello PDUs of one interface, so only trusted routers become neighbors. |

Types: **Cleartext** (the original ISO 10589 password, weak), **MD5**
([RFC 5304](https://www.rfc-editor.org/rfc/rfc5304)), **HMAC-SHA-1, 224, 256, 384 and 512**
([RFC 5310](https://www.rfc-editor.org/rfc/rfc5310), which lists exactly these) and **Key chain**.
Keys are stored as plain text, as in OSPF.

Every place has, besides the type and the key, three more fields that start with the same name
(for the hello of an interface: `hello_auth_key_id`, `hello_auth_key_chain` and `hello_auth_send_only`):

| Field | Meaning |
| --- | --- |
| **Key ID** | The number that identifies the key in the PDU, 0 to 65535 (RFC 5310). Only for the HMAC-SHA types. |
| **Key chain** | The name of a key chain defined on the device, with the **Key chain** type: the device takes the keys, their IDs and their lifetimes from it (this is how keys are rolled over without a break), so the key and the key ID stay empty. Only the name is stored, as OSPF does. |
| **Send only** | Sign the PDUs that are sent but do not check the ones received. It is used while authentication is being enabled network-wide (Cisco `send-only`, Junos `no-authentication-check`). It needs a type. |

## Levels

**IS-IS → Levels**

The settings of the instance **for one level**: one record per instance and level.

| Field | Meaning |
| --- | --- |
| Level | Level-1 or Level-2. |
| Default metric | Metric for interfaces in this level that have none. |
| Wide metrics only | Use only the wide metric TLVs in this level. |
| Preference, labeled preference | Route preference of this level, and of paths that use segment-routing labels. |
| Disabled | Switch the level off on this instance. |
| Authentication type / key | Level authentication, see above. |

The level must be one the instance's IS type runs (a Level-1-only instance has no Level-2 record unless it is marked *Disabled*), and *Wide metrics only* cannot be used with the narrow metric style.

## Interfaces

**IS-IS → Interfaces**

A device interface that takes part in IS-IS, **one record per address family**: an interface that
runs IPv4 and IPv6 has two. The interface must be on the instance's device and in the instance's VRF (or both in the global table). The circuit type must share a level with the instance's IS type (RFC 1195, ISO 10589). Changing the device, VRF or IS type later is refused while it would leave interfaces or levels that break these rules.

| Field | Meaning |
| --- | --- |
| Instance, Interface | The process and the device interface. |
| Address family | **IPv4** or **IPv6**. |
| Circuit type | The levels the interface takes part in: Level-1, Level-2 only or Level-1-2. |
| Network type | **Point-to-point** or **Broadcast**. On broadcast networks a **DIS** (designated intermediate system) is elected, like the OSPF DR; point-to-point links have no election and form adjacencies faster. |
| Metric | The cost of the link. |
| Passive | Advertise the interface's prefix but form no adjacency. |
| Hello authentication | See above. |
| BFD | Use [BFD](../bfd.md) for fast failure detection ([RFC 5882](https://www.rfc-editor.org/rfc/rfc5882)). |
| FRR, FRR protection | Include the interface in fast reroute (or exclude it), and whether to protect against **link** failure or **node** failure too. |
| CSNP interval, retransmit interval, LSP interval | Protocol pacing: how often the DIS sends the complete sequence number PDU (s), the LSP retransmission interval (s) and the pacing between LSPs (ms). |
| Hello padding | Pad hello PDUs to the full MTU so an MTU mismatch prevents the adjacency instead of breaking it later ([RFC 3787](https://www.rfc-editor.org/rfc/rfc3787)). |
| LDP-IGP sync | Do not use the link for traffic until LDP is up ([RFC 5443](https://www.rfc-editor.org/rfc/rfc5443)). |
| Prefix suppression | Do not advertise the prefixes of the link ([RFC 6860](https://www.rfc-editor.org/rfc/rfc6860)). |
| Route tag | Administrative tag (1 to 4294967295) added to the prefixes of the interface ([RFC 5130](https://www.rfc-editor.org/rfc/rfc5130)). |
| Three-way handshake | Point-to-point adjacency handshake, on by default; *no* disables it ([RFC 5303](https://www.rfc-editor.org/rfc/rfc5303)). |
| Mesh group | Limit LSP flooding on dense meshes, or `blocked` to stop flooding on the interface ([RFC 2973](https://www.rfc-editor.org/rfc/rfc2973)). |

### Interface levels

Open an interface and use its *Levels* tab (there is no menu entry for this object).

Settings that differ **per level on one interface** (only for levels the interface's circuit type runs): metric, hello interval, hello multiplier (how
many hellos can be missed), **priority** for the DIS election (higher wins), passive, and the **hello authentication** of that level (it overrides the one of the interface).

## Segment routing

**IS-IS → Segment Routing**

Segment routing steers traffic with a list of labels or addresses carried in the packet, without
per-flow state in the core. IS-IS advertises the segments: [RFC 8667](https://www.rfc-editor.org/rfc/rfc8667)
for SR-MPLS. One record per instance.

| Field | Meaning |
| --- | --- |
| Enabled | SR-MPLS on this instance. |
| SRv6 enabled | SRv6 on this instance; the locators are separate objects (below). |
| Prefix-SID range | `global` or a named/explicit range. |
| SRGB start / range | The *Segment Routing Global Block*: the labels reserved for prefix SIDs, which should be the same on every router. Start and range go **together**. |
| SRLB start / range | The *Segment Routing Local Block*, for local SIDs such as adjacency SIDs. Also together. |
| Maximum SID depth | How many labels the router can push. |
| Tunnel table preference | Preference of SR tunnels against other tunnel types. |

### Prefix-SIDs

**IS-IS → Prefix-SIDs**

The SID of an interface's prefix. Exactly one of **SID index** (an index into the SRGB) or **SID
label** (an absolute label) is set, never both. *Algorithm* is 0 (SPF) or a Flex-Algo (128 to 255).
Flags: **Node SID** (the prefix identifies a single node, a /32 or /128), **No PHP** (do not pop the
label at the penultimate hop), **Explicit null** (use explicit null instead), **Readvertise** (the
SID is leaked from another level or protocol). One SID per interface and algorithm.

Checked when you save ([RFC 8667](https://www.rfc-editor.org/rfc/rfc8667)): *No PHP* and *Explicit null* cannot both be set; an absolute label is 16 to 1048575 (20 bits, 0-15 are reserved); an index must fit in the instance's SRGB; a Flex-Algo SID needs that Flex-Algo defined on the instance; the *Node SID* flag needs a /32 (IPv4) or /128 (IPv6) address when the interface has addresses of that family. The SRGB and SRLB must be within 16 to 1048575 and cannot overlap.

### Flex-Algo

**IS-IS → Flex-Algos**

*Flexible Algorithm* lets the network compute its own constrained paths, for example "lowest delay,
avoiding links of colour red" ([RFC 9350](https://www.rfc-editor.org/rfc/rfc9350)).

| Field | Meaning |
| --- | --- |
| Algorithm ID | 128 to 255. |
| Metric type | IGP metric, minimum unidirectional delay or TE metric, the three types of RFC 9350 (`igp-metric`, `delay-metric`, `te-metric`). |
| Priority | 0 to 255. Used when routers define the same algorithm differently; the highest priority wins (RFC 9350 default is 128 when empty). |
| Admin groups: exclude / include any / include all | The affinities (link colours) the paths must avoid or use. Comma-separated names. |

### SRv6 locators

**IS-IS → SRv6 Locators**

With **SRv6** the segments are IPv6 addresses ([RFC 8986](https://www.rfc-editor.org/rfc/rfc8986); IS-IS
advertisement in [RFC 9352](https://www.rfc-editor.org/rfc/rfc9352)). A **locator** is the IPv6 prefix of
the router, split into *block* and *node* parts (`LOC = Block:Node` in RFC 8986).

| Field | Meaning |
| --- | --- |
| Name, prefix | The locator and its IPv6 prefix (IPv4 is refused). Unique name per instance. When block and node length are set, they add up to the prefix length. |
| Algorithm | 0 (SPF) or a Flex-Algo (128 to 255) that is defined on the instance. |
| Anycast | The locator is shared by several nodes. |
| Micro-segment (uSID) | A compressed-SID locator. |
| Flavor | The END behaviour flavours, for example `psp usd`. |
| Block / node / function / argument length | The sizes in bits of the parts (RFC 8986). The total cannot exceed 128. Empty derives them from the prefix. |
| IS-IS level | Advertise in one level only; empty means both. |
| Enabled | The instance advertises the locator. |
| Vendor extensions | JSON for vendor details with no cross-vendor equivalent. |

## Area addresses

**IS-IS → Area Addresses**

A router can belong to **up to three areas at once** (ISO 10589 7.1.4). This is what is done while two areas are merged or a router is moved from one area to another: it keeps its old area and gets the new one, and the old one is removed once everything has converged. The **NET** of the instance is the first area address; each entry here adds another NET.

| Field | Meaning |
| --- | --- |
| Instance | The IS-IS instance. |
| NET | Network Entity Title with the new area, for example `49.0002.0001.0001.0001.00`. The area and system ID are shown split in the list. |

Rules:

- All the NETs of an instance have the **same system ID** (the 6 bytes before the last one): only the area changes. Changing the system ID of the instance while it has area addresses is rejected.
- The area cannot be one the instance already has, and an instance has at most **three** (the NET plus two more).
- The last byte (selector) must be `00`, as in the NET of the instance.

**Duplicate system IDs.** Two routers with the same system ID in the same area cannot form adjacencies. The page of an instance shows **Same System ID In** with the other instances that share a system ID and an area (counting their added area addresses too); `—` means there are none. It is a warning, nothing is blocked.

## Redistribution

**IS-IS → Redistribution**

Routes of another protocol that the instance advertises, for one address family and level ([RFC 1195](https://www.rfc-editor.org/rfc/rfc1195) section 3.3 defines the external routes). It mirrors OSPF redistribution.

| Field | Meaning |
| --- | --- |
| Instance, Address family | The IS-IS instance and the family (IPv4 or IPv6) of the routes. |
| Protocol | Connected, static, OSPF, EIGRP, BGP or another IS-IS instance. Connected and static need no source. |
| Source | The process the routes come from. It is **required** for OSPF, EIGRP, BGP and IS-IS, only the source of the chosen protocol is allowed, it must be **on the same device** as the instance, and an instance cannot be redistributed into itself. |
| Level | Level-1, Level-2 or both. The instance must run the level. |
| Metric | Metric of the routes: 1 to 63 with a narrow metric style, 1 to 16777214 otherwise ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305)). Empty uses the platform default. |
| Metric type | Internal or external, as defined in RFC 1195. |
| Route tag | Administrative tag set on the routes, 1 to 4294967295 ([RFC 5130](https://www.rfc-editor.org/rfc/rfc5130)). |
| Route policy | Name of the policy applied to the routes. |

A source is redistributed once per address family and level.

## Summary addresses

**IS-IS → Summary Addresses**

One prefix advertised **instead of the routes it covers**, per level ([RFC 1195](https://www.rfc-editor.org/rfc/rfc1195), [RFC 5302](https://www.rfc-editor.org/rfc/rfc5302)). The prefix may be IPv4 or IPv6 and cannot have host bits set.

| Field | Meaning |
| --- | --- |
| Prefix | The summary prefix. |
| Level | Level the summary is advertised into; the instance must run it. |
| Do not advertise | Suppress the covered routes instead of summarizing them. |
| Metric | Metric of the summary (same range as in redistribution). Empty takes the best covered route. |
| Route tag | Administrative tag set on the summary route. |

A prefix is summarized once per instance and level.

## Route leaking

**IS-IS → Route Leaking**

Leaking of **Level-2 routes into Level 1** for an address family ([RFC 5302](https://www.rfc-editor.org/rfc/rfc5302) section 3): the routes are advertised with the up/down bit set so they are not looped back. Routes of Level 1 are always advertised into Level 2, so only this direction is configured. Only an instance that runs **both levels** can leak. The optional **route policy** selects the routes; empty leaks all of them. There is one entry per instance and address family.

## Settings

**IS-IS → Settings**

A **key and value** assigned to an instance or interface for the options that do not need their own
field. The value must match the type of the key (yes/no, number or address).

| Key | Meaning |
| --- | --- |
| SPF Second Wait, SPF Rapid Runs, LSP-Gen Second Wait | Extra SPF and LSP generation back-off controls (vendor-specific). |
| TE IPv4 / IPv6 Router-ID | Stable address used in traffic-engineering advertisements ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305), [RFC 6119](https://www.rfc-editor.org/rfc/rfc6119)). |
| Graceful Restart, T3, Helper | Keep forwarding while IS-IS restarts, the overall restart timer T3 (s), and whether this router helps neighbours that restart ([RFC 8706](https://www.rfc-editor.org/rfc/rfc8706)). |
| LDP-IGP Sync, Hold-down | Do not use a link for traffic until LDP is up, and the longest wait (s) before using it anyway ([RFC 5443](https://www.rfc-editor.org/rfc/rfc5443)). |
| Overload Until BGP Converges, Overload with High Metrics | Conditions of the overload bit on startup: wait for BGP, or advertise maximum metrics instead of setting the bit. |
| Maximum Area Addresses | How many area addresses the router accepts (0 to 254, the default is 3, ISO 10589). |
| Default Route Origination | Originate a default route into IS-IS. |
| Adjacency Protocol Check | Check that neighbours support the same IP protocols before forming an adjacency ([RFC 1195](https://www.rfc-editor.org/rfc/rfc1195)). |
| Purge Originator Identification | Add the originator to purged LSPs to find who purged them ([RFC 6232](https://www.rfc-editor.org/rfc/rfc6232)). |
| Prefix Suppression | Do not advertise transit-only link prefixes ([RFC 6860](https://www.rfc-editor.org/rfc/rfc6860)). |
| Multi-Topology | A checkbox. IPv4 and IPv6 each get their own topology and path calculation ([RFC 5120](https://www.rfc-editor.org/rfc/rfc5120)), so a link that lacks one family is not used for it. Without it both families share one topology. |
| Log Adjacency Changes, Advertise Passive Only, Default Route Tag, IGP Shortcut, Hello Padding, RIB Priority | Vendor features without an RFC. |

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

```text
IS-IS instance
├─ Identity: device → Device · vrf → VRF · process_tag · net
├─ Route policies: import_policy → Route policy · export_policy → Route policy
├─ Type: is_type {Level-1 | Level-2 Only | Level-1-2}
│     · metric_style {Wide | Narrow | Transition}
├─ Authentication
│     · area_auth_type {MD5 | Cleartext | HMAC-SHA-1/224/256/384/512 | Key chain} · area_auth_key · area_auth_key_id · area_auth_key_chain · area_auth_send_only
│     · domain_auth_type {MD5 | Cleartext | HMAC-SHA-1/224/256/384/512 | Key chain} · domain_auth_key · domain_auth_key_id · domain_auth_key_chain · domain_auth_send_only
├─ Timers: spf_initial_wait · spf_max_wait · lsp_initial_wait · lsp_max_wait
│     · lsp_lifetime · lsp_refresh_interval · lsp_mtu
├─ Overload: overload_bit? · overload_on_startup? · overload_timeout
│     · suppress_attached_bit? · ignore_attached_bit?
├─ Routing: distance · maximum_paths · reference_bandwidth · te_enabled?
├─ Fast reroute: fast_reroute {LFA | Remote LFA | TI-LFA} · microloop_avoidance?
├─ Settings (key / value; the key is one of): SPF Second Wait (ms) · SPF Rapid Runs
│     · LSP-Gen Second Wait (ms) · TE IPv4 Router-ID · TE IPv6 Router-ID · Graceful Restart
│     · LDP-IGP Sync · Prefix Suppression · Log Adjacency Changes · Advertise Passive Only
│     · Default Route Tag · Multi-Topology · IGP Shortcut · Hello Padding · RIB Priority
    │     · Graceful Restart T3 · Graceful Restart Helper · LDP-IGP Sync Hold-down
    │     · Overload Until BGP Converges · Overload with High Metrics · Maximum Area Addresses
    │     · Default Route Origination · Adjacency Protocol Check · Purge Originator Identification
│
├─ Level
│     instance → IS-IS instance · level {Level-1 | Level-2} · disabled?
│     · default_metric · wide_metrics_only? · preference · labeled_preference
│     · auth_type {MD5 | Cleartext | HMAC-SHA-1/224/256/384/512 | Key chain} · auth_key · auth_key_id · auth_key_chain · auth_send_only
├─ Segment routing
│     instance → IS-IS instance · enabled? · srv6_enabled? · prefix_sid_range
│     · srgb_start · srgb_range · srlb_start · srlb_range · maximum_sid_depth · tunnel_table_pref
├─ Flex-Algo
│     instance → IS-IS instance · algo_id · metric_type · priority
│     · admin_group_exclude · admin_group_include_any · admin_group_include_all
├─ Area address
│     instance → IS-IS instance · net (the area and system_id are read-only, derived from it)
├─ Redistribution
│     instance → IS-IS instance · address_family {IPv4 | IPv6}
│     · protocol {Connected | Static | EIGRP | BGP | OSPF | IS-IS}
│     · ospf_source → OSPF instance · eigrp_source → EIGRP router · bgp_source → BGP router
│     · isis_source → IS-IS instance · level {Level-1 | Level-2 | Level-1-2}
│     · metric · metric_type {Internal | External} · route_tag · route_policy
├─ Summary address
│     instance → IS-IS instance · prefix · level {Level-1 | Level-2 | Level-1-2}
│     · not_advertise? · metric · route_tag
├─ Route leak
│     instance → IS-IS instance · address_family {IPv4 | IPv6} · route_policy
├─ SRv6 locator
│     instance → IS-IS instance · name · prefix · algorithm · enabled?
│     · isis_level {Level-1 | Level-2} · is_anycast? · is_micro_segment? · flavor
│     · block_length · node_length · function_length · argument_length · vendor_ext
└─ Interface
    ├─ instance → IS-IS instance · interface → Interface · address_family {IPv4 | IPv6}
    ├─ Basics: circuit_type {Level-1 | Level-2 Only | Level-1-2}
    │     · network_type {Point-to-Point | Broadcast} · metric · passive? · bfd_enabled?
    ├─ Authentication: hello_auth_type {MD5 | Cleartext | HMAC-SHA-1/224/256/384/512 | Key chain}
    │     · hello_auth_key · hello_auth_key_id · hello_auth_key_chain · hello_auth_send_only
    ├─ Fast reroute: frr_enabled? · frr_protection {Link protection | Node protection}
    ├─ Timers: csnp_interval · retransmit_interval · lsp_interval · mesh_group
    ├─ Options: hello_padding? · ldp_sync? · prefix_suppression? · three_way_handshake?
    │     · route_tag
    ├─ Settings (key / value; the key is one of): SPF Second Wait (ms) · SPF Rapid Runs
    │     · LSP-Gen Second Wait (ms) · TE IPv4 Router-ID · TE IPv6 Router-ID · Graceful Restart
    │     · LDP-IGP Sync · Prefix Suppression · Log Adjacency Changes · Advertise Passive Only
    │     · Default Route Tag · Multi-Topology · IGP Shortcut · Hello Padding · RIB Priority
    │     · Graceful Restart T3 · Graceful Restart Helper · LDP-IGP Sync Hold-down
    │     · Overload Until BGP Converges · Overload with High Metrics · Maximum Area Addresses
    │     · Default Route Origination · Adjacency Protocol Check · Purge Originator Identification
    ├─ Interface level
    │     interface → IS-IS interface · level {Level-1 | Level-2} · metric
    │     · hello_interval · hello_multiplier · priority · passive?
    │     · hello_auth_type {MD5 | Cleartext | HMAC-SHA-1/224/256/384/512 | Key chain} · hello_auth_key · hello_auth_key_id · hello_auth_key_chain · hello_auth_send_only
    └─ Prefix SID
          interface → IS-IS interface · algorithm · sid_index · sid_label
          · n_flag? · no_php? · explicit_null? · readvertise?
```

## Standards behind IS-IS

| Standard | What it gives the plugin |
| --- | --- |
| ISO/IEC 10589 | The protocol: levels, NET, overload and attached bits, cleartext authentication |
| [RFC 1195](https://www.rfc-editor.org/rfc/rfc1195), [RFC 5308](https://www.rfc-editor.org/rfc/rfc5308) | IS-IS for IPv4 and for IPv6 |
| [RFC 5304](https://www.rfc-editor.org/rfc/rfc5304), [RFC 5310](https://www.rfc-editor.org/rfc/rfc5310) | MD5 and HMAC-SHA authentication |
| [RFC 5305](https://www.rfc-editor.org/rfc/rfc5305), [RFC 6119](https://www.rfc-editor.org/rfc/rfc6119) | Wide metrics and traffic engineering (IPv4 / IPv6) |
| [RFC 5120](https://www.rfc-editor.org/rfc/rfc5120) | Multi-topology |
| [RFC 2973](https://www.rfc-editor.org/rfc/rfc2973) | Mesh groups |
| [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286), [RFC 7490](https://www.rfc-editor.org/rfc/rfc7490), [RFC 8333](https://www.rfc-editor.org/rfc/rfc8333) | Fast reroute and micro-loop avoidance |
| [RFC 8405](https://www.rfc-editor.org/rfc/rfc8405) | SPF back-off |
| [RFC 8667](https://www.rfc-editor.org/rfc/rfc8667), [RFC 9350](https://www.rfc-editor.org/rfc/rfc9350) | Segment routing and Flex-Algo |
| [RFC 8986](https://www.rfc-editor.org/rfc/rfc8986), [RFC 9352](https://www.rfc-editor.org/rfc/rfc9352) | SRv6 |
| [RFC 8706](https://www.rfc-editor.org/rfc/rfc8706), [RFC 5443](https://www.rfc-editor.org/rfc/rfc5443), [RFC 6860](https://www.rfc-editor.org/rfc/rfc6860), [RFC 5882](https://www.rfc-editor.org/rfc/rfc5882) | Graceful restart, LDP sync, prefix suppression, BFD |
