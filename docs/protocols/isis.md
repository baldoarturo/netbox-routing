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
 └─ Interface (device interface + address family)
     ├─ Interface level (per-level metric and hello settings)
     ├─ Prefix-SID
     └─ Settings
```

## Instances

**IS-IS → Instances**

| Field | Meaning |
| --- | --- |
| Device, VRF | Where the process runs. IS-IS can run once per VRF. |
| Process tag | The name of the process (`router isis <tag>`); empty for the unnamed process. Unique per device. |
| NET | The Network Entity Title, validated against the format above. Empty is allowed while you are drafting. |
| IS type | **Level-1**, **Level-2 only** or **Level-1-2**. Empty means the platform default (Level-1-2). |
| Metric style | **Wide**, **Narrow** or **Transition** (both, for migrating between the two). Empty means the platform default. |
| Overload bit | Set the *overload bit*: other routers stop using this router for **transit** traffic, while still reaching its own prefixes (ISO 10589). Used for maintenance. |
| Overload on startup, timeout | Set it for a number of seconds after boot so the router joins the network gradually. |
| Suppress / ignore attached bit | The *attached bit* tells Level-1 routers that this Level-1-2 router reaches other areas, so they use it as a default route. *Suppress* stops the router from setting it; *ignore* stops it from installing the default route toward routers that do (ISO 10589). |
| Distance | Administrative distance. |
| Maximum paths | Equal-cost paths installed (ECMP). |
| Reference bandwidth | Mbps used to derive default interface metrics. |
| Traffic engineering | Enable IS-IS TE extensions ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305)). |

### Route policies

| Field | Meaning |
| --- | --- |
| Import policy | Optional [route policy](../routing-objects.md#route-policies) that filters the routes IS-IS **installs** in the routing table. |
| Export policy | Optional route policy that filters the routes IS-IS **advertises or takes from other sources** (redistribution into IS-IS). |

A route policy that an instance uses **cannot be deleted**: choose another one, or clear the field, first. The policy is per instance; the leaking of routes between levels ([RFC 5302](https://www.rfc-editor.org/rfc/rfc5302)) is not modelled yet.

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

IS-IS has authentication in four places; each takes a **type** and a **key**, and one without the
other is refused:

| Where | Protects |
| --- | --- |
| **Area** password (instance) | LSPs and SNPs of Level 1. |
| **Domain** password (instance) | LSPs and SNPs of Level 2. |
| **Level** | LSPs of that level, set on the [Level](#levels) object. |
| **Hello** (interface) | The hello PDUs of one interface, so only trusted routers become neighbors. |

Types: **Cleartext** (the original ISO 10589 password, weak), **MD5**
([RFC 5304](https://www.rfc-editor.org/rfc/rfc5304)) and **HMAC-SHA-1 / HMAC-SHA-256**
([RFC 5310](https://www.rfc-editor.org/rfc/rfc5310)). Keys are stored as plain text.

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

## Interfaces

**IS-IS → Interfaces**

A device interface that takes part in IS-IS, **one record per address family**: an interface that
runs IPv4 and IPv6 has two. The interface must be on the instance's device.

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
| Mesh group | Limit LSP flooding on dense meshes, or `blocked` to stop flooding on the interface ([RFC 2973](https://www.rfc-editor.org/rfc/rfc2973)). |

### Interface levels

Open an interface and use its *Levels* tab (there is no menu entry for this object).

Settings that differ **per level on one interface**: metric, hello interval, hello multiplier (how
many hellos can be missed), **priority** for the DIS election (higher wins) and passive.

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

### Flex-Algo

**IS-IS → Flex-Algos**

*Flexible Algorithm* lets the network compute its own constrained paths, for example "lowest delay,
avoiding links of colour red" ([RFC 9350](https://www.rfc-editor.org/rfc/rfc9350)).

| Field | Meaning |
| --- | --- |
| Algorithm ID | 128 to 255. |
| Metric type | `igp-metric`, `delay-metric` or `te-metric`. |
| Priority | Used when routers define the same algorithm differently; the highest priority wins. |
| Admin groups: exclude / include any / include all | The affinities (link colours) the paths must avoid or use. Comma-separated names. |

### SRv6 locators

**IS-IS → SRv6 Locators**

With **SRv6** the segments are IPv6 addresses ([RFC 8986](https://www.rfc-editor.org/rfc/rfc8986); IS-IS
advertisement in [RFC 9352](https://www.rfc-editor.org/rfc/rfc9352)). A **locator** is the IPv6 prefix of
the router, split into *block* and *node* parts (`LOC = Block:Node` in RFC 8986).

| Field | Meaning |
| --- | --- |
| Name, prefix | The locator and its IPv6 prefix. Unique name per instance. |
| Algorithm | 0 (SPF) or a Flex-Algo (128 to 255). |
| Anycast | The locator is shared by several nodes. |
| Micro-segment (uSID) | A compressed-SID locator. |
| Flavor | The END behaviour flavours, for example `psp usd`. |
| Block / node / function / argument length | The sizes in bits of the parts (RFC 8986). The total cannot exceed 128. Empty derives them from the prefix. |
| IS-IS level | Advertise in one level only; empty means both. |
| Enabled | The instance advertises the locator. |
| Vendor extensions | JSON for vendor details with no cross-vendor equivalent. |

## Settings

**IS-IS → Settings**

A **key and value** assigned to an instance or interface for the options that do not need their own
field. The value must match the type of the key (yes/no, number or address).

| Key | Meaning |
| --- | --- |
| SPF Second Wait, SPF Rapid Runs, LSP-Gen Second Wait | Extra SPF and LSP generation back-off controls (vendor-specific). |
| TE IPv4 / IPv6 Router-ID | Stable address used in traffic-engineering advertisements ([RFC 5305](https://www.rfc-editor.org/rfc/rfc5305), [RFC 6119](https://www.rfc-editor.org/rfc/rfc6119)). |
| Graceful Restart | Keep forwarding while IS-IS restarts ([RFC 8706](https://www.rfc-editor.org/rfc/rfc8706)). |
| LDP-IGP Sync | Do not use a link for traffic until LDP is up ([RFC 5443](https://www.rfc-editor.org/rfc/rfc5443)). |
| Prefix Suppression | Do not advertise transit-only link prefixes ([RFC 6860](https://www.rfc-editor.org/rfc/rfc6860)). |
| Multi-Topology | Separate topologies per address family ([RFC 5120](https://www.rfc-editor.org/rfc/rfc5120)). |
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
│     · area_auth_type {MD5 | Cleartext | HMAC-SHA-1 | HMAC-SHA-256} · area_auth_key
│     · domain_auth_type {MD5 | Cleartext | HMAC-SHA-1 | HMAC-SHA-256} · domain_auth_key
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
│
├─ Level
│     instance → IS-IS instance · level {Level-1 | Level-2} · disabled?
│     · default_metric · wide_metrics_only? · preference · labeled_preference
│     · auth_type {MD5 | Cleartext | HMAC-SHA-1 | HMAC-SHA-256} · auth_key
├─ Segment routing
│     instance → IS-IS instance · enabled? · srv6_enabled? · prefix_sid_range
│     · srgb_start · srgb_range · srlb_start · srlb_range · maximum_sid_depth · tunnel_table_pref
├─ Flex-Algo
│     instance → IS-IS instance · algo_id · metric_type · priority
│     · admin_group_exclude · admin_group_include_any · admin_group_include_all
├─ SRv6 locator
│     instance → IS-IS instance · name · prefix · algorithm · enabled?
│     · isis_level {Level-1 | Level-2} · is_anycast? · is_micro_segment? · flavor
│     · block_length · node_length · function_length · argument_length · vendor_ext
└─ Interface
    ├─ instance → IS-IS instance · interface → Interface · address_family {IPv4 | IPv6}
    ├─ Basics: circuit_type {Level-1 | Level-2 Only | Level-1-2}
    │     · network_type {Point-to-Point | Broadcast} · metric · passive? · bfd_enabled?
    ├─ Authentication: hello_auth_type {MD5 | Cleartext | HMAC-SHA-1 | HMAC-SHA-256}
    │     · hello_auth_key
    ├─ Fast reroute: frr_enabled? · frr_protection {Link protection | Node protection}
    ├─ Timers: csnp_interval · retransmit_interval · lsp_interval · mesh_group
    ├─ Settings (key / value; the key is one of): SPF Second Wait (ms) · SPF Rapid Runs
    │     · LSP-Gen Second Wait (ms) · TE IPv4 Router-ID · TE IPv6 Router-ID · Graceful Restart
    │     · LDP-IGP Sync · Prefix Suppression · Log Adjacency Changes · Advertise Passive Only
    │     · Default Route Tag · Multi-Topology · IGP Shortcut · Hello Padding · RIB Priority
    ├─ Interface level
    │     interface → IS-IS interface · level {Level-1 | Level-2} · metric
    │     · hello_interval · hello_multiplier · priority · passive?
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
