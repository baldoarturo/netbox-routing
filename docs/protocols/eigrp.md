# EIGRP

**Routing → EIGRP**

EIGRP (Enhanced Interior Gateway Routing Protocol) is documented in
[RFC 7868](https://www.rfc-editor.org/rfc/rfc7868) (informational: it was a Cisco protocol before it
was published). The plugin models the configuration of an EIGRP process: which devices run it, in
which address families, on which networks and interfaces.

## How it is organized

```
EIGRP router (device, mode) ─┬─ Address family (IPv4 / IPv6, optional VRF)
                             ├─ Network (a NetBox prefix, optional address family)
                             └─ Interface (a device interface, optional address family)
```

## Routers

**EIGRP → Routers**

One record per EIGRP process on a device.

| Field | Meaning |
| --- | --- |
| Device | The device that runs the process. |
| Mode | **Classic Router** (a numbered *autonomous system* process, the original configuration style) or **Named Router** (the newer *named mode*, where the process has a name and address families live inside it). |
| Name | The name, for named mode. Unique per device. |
| Process ID | The autonomous system number, for classic mode. |
| Router ID | Optional, the 32-bit identifier written like an IPv4 address; it has to be unique in the network. |

## Address families

**EIGRP → Address Families**

The protocol runs one instance per address family. A family record belongs to a router and sets
**IPv4** or **IPv6**, an optional **VRF** (so the same router can run EIGRP in several VRFs) and an
optional router ID that overrides the router's. A router cannot have the same family twice in the same
VRF.

## Networks

**EIGRP → Networks**

The `network` statements: the NetBox **prefix** whose interfaces take part in EIGRP. Choose the
router and, in named mode, the address family.

## Interfaces

**EIGRP → Interfaces**

Per-interface settings.

| Field | Meaning |
| --- | --- |
| Interface | A device interface. |
| Passive | The interface is advertised in EIGRP but sends no hellos and forms no neighbors; the usual setting for user-facing ports. |
| BFD | Use BFD ([RFC 5880](https://www.rfc-editor.org/rfc/rfc5880)) for fast neighbor failure detection. |
| Authentication | **Message Digest**, **Key Chain** or **Null** (none). RFC 7868 defines the packet authentication. |
| Passphrase | The key, stored as plain text. |

## Standards behind it

| Feature | Standard |
| --- | --- |
| The protocol, router ID, passive interfaces, authentication | [RFC 7868](https://www.rfc-editor.org/rfc/rfc7868) |
| BFD | [RFC 5880](https://www.rfc-editor.org/rfc/rfc5880) |
| Classic and named modes, VRF address families | Cisco configuration styles; RFC 7868 describes the protocol, not the CLI |
