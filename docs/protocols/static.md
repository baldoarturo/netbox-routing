# Static routes

**Routing → Static → Static Routes**

A static route is a route you configure by hand instead of learning it from a routing protocol. It is
the simplest object in the plugin: one record describes the route, and you assign it to the devices
that carry it.

> **Standards.** Static routes are not a protocol, but [RFC 8349](https://www.rfc-editor.org/rfc/rfc8349) (YANG data
> model for routing management) defines what a static route is: a destination prefix, a next hop (an address, an
> outgoing interface, both, or a *special next hop*: `blackhole`, `unreachable`, `prohibit` or `receive`), a
> `route-preference` (the *Distance* here) and a `tag`. Addressing rules come from RFC 4291 (IPv6 link-local
> addresses are only valid on one link) and RFC 4861.

## Fields

| Field | Meaning |
| --- | --- |
| Name | Optional label ("default via ISP A"). |
| Prefix | The destination, IPv4 or IPv6 with its mask (`0.0.0.0/0`, `2001:db8::/32`). |
| VRF | Optional. Leave empty for the global routing table. |
| Next hop | The IP address to forward to. |
| Next hop type | *Forward* (default) sends the traffic to the next hop address and/or interface. The special types come from RFC 8349 and have no next hop: *Blackhole* drops silently (`Null0`, Junos `discard`), *Unreachable* drops and answers ICMP unreachable (Junos `reject`), *Prohibit* answers ICMP administratively prohibited, *Receive* delivers to the device itself. |
| Interface next hop | The outgoing interface, a real NetBox interface, for routes without an IP next hop (a point-to-point link, for example). An interface belongs to one device, so a route with an interface is carried by that device only. |
| Next hop VRF / Next hop in the global table | Route leaking: resolve the next hop in another VRF (`nexthop-vrf` on Arista, `next-table` on Junos) or in the global table (`global` on Cisco). Needs an IP next hop; use one or the other. |
| Distance | The administrative distance (Cisco IOS/NX-OS/EOS) or *preference* (Junos); RFC 8349 calls it `route-preference`. When several routes to the same prefix exist, the lowest wins. 1 to 255, default 1. It was called *Metric* before; the REST API field is now `distance`. |
| Permanent | Marks a route that stays installed even if its next hop becomes unreachable (the `permanent` keyword on some platforms). |
| Tag | Optional number (0 to 4294967295) to match the route in policies, for example when redistributing static routes into OSPF. |
| Devices | The devices that have this route configured. |

**A *Forward* route needs a next hop**: either an IP next hop, an interface next hop, or both. The special types
refuse any next hop, interface or next hop VRF.

## What the plugin checks

* The **prefix** has no host bits (`10.0.0.1/24` is refused, use `10.0.0.0/24`), as on Cisco, Junos and Arista.
* The **next hop** is an address of the same family as the prefix (an IPv4 prefix through an IPv6 next hop is refused),
  and it is not `0.0.0.0`/`::`, a loopback or a multicast address.
* An IPv6 **link-local** next hop (`fe80::/10`, RFC 4291) needs the *Interface next hop*: the address is only
  meaningful on one link (RFC 4861).
* A device cannot carry two routes with the same VRF, prefix, next hop type, next hop, interface and next hop table. The form, the CSV
  import and the REST API name the devices that already have it.

## Typical uses

* **A default route on many devices.** Create the route once and select all the devices it applies
  to, instead of one record per device.
* **Floating static routes.** Create the backup route with a higher *Distance* than the primary.
* **Summary or black-hole route.** Choose *Blackhole* instead of pointing at `Null0` by hand.
* **Leak a route between VRFs.** Set the *VRF* of the route and the *Next hop VRF* where the next hop lives.
* **Route in a VRF.** Select the *VRF*; the same prefix can then exist in several VRFs.
* **Seeing a device's routes.** Open the device and use the **Routing** tab: its *Static routes* section lists
  the routes assigned to it, next to the protocols of the device.

## Finding routes

The list filters by device, VRF, prefix, next hop, interface next hop, next hop type, next hop VRF, name, address family, distance, route tag and
*Permanent*. The REST API also takes `within`, `within_include` and `contains` for the prefix, `distance__gte`/`__lte`
and `route_tag` (the route tag; `tag` is NetBox's own tag). The search box and the global search look at the prefix,
next hop, interface next hop, name, description and tag.

## Where static routes connect to other protocols

OSPF can redistribute static routes ([OSPF redistribution](ospf.md#redistribution)); the *Tag* is the
usual way to pick which ones.

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

```text
Static route
├─ Destination: prefix · vrf → VRF
├─ Next hop: next_hop_type {forward | blackhole | unreachable | prohibit | receive} · next_hop · interface → Interface
├─ Route leaking: next_hop_vrf → VRF · next_hop_global?
├─ Attributes: name · distance · tag · permanent?
└─ Applies to: devices → Device (several)
```
