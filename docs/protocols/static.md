# Static routes

**Routing → Static → Static Routes**

A static route is a route you configure by hand instead of learning it from a routing protocol. It is
the simplest object in the plugin: one record describes the route, and you assign it to the devices
that carry it.

> **Standards.** Static routes are not a protocol, so there is no RFC behind them. The plugin only checks what a
> route needs to be meaningful: a destination and a way to reach it.

## Fields

| Field | Meaning |
| --- | --- |
| Name | Optional label ("default via ISP A"). |
| Prefix | The destination, IPv4 or IPv6 with its mask (`0.0.0.0/0`, `2001:db8::/32`). |
| VRF | Optional. Leave empty for the global routing table. |
| Next hop | The IP address to forward to. |
| Interface next hop | The outgoing interface name, for routes without an IP next hop (a point-to-point link, for example). |
| Distance | The administrative distance (Cisco IOS/NX-OS/EOS) or *preference* (Junos); RFC 8349 calls it `route-preference`. When several routes to the same prefix exist, the lowest wins. 1 to 255, default 1. It was called *Metric* before; the REST API field is now `distance`. |
| Permanent | Marks a route that stays installed even if its next hop becomes unreachable (the `permanent` keyword on some platforms). |
| Tag | Optional number (0 to 4294967295) to match the route in policies, for example when redistributing static routes into OSPF. |
| Devices | The devices that have this route configured. |

**A route needs a next hop**: either an IP next hop, an interface next hop, or both. The form refuses
a route with neither.

## What the plugin checks

* The **prefix** has no host bits (`10.0.0.1/24` is refused, use `10.0.0.0/24`), as on Cisco, Junos and Arista.
* The **next hop** is an address of the same family as the prefix (an IPv4 prefix through an IPv6 next hop is refused),
  and it is not `0.0.0.0`/`::`, a loopback or a multicast address.
* An IPv6 **link-local** next hop (`fe80::/10`, RFC 4291) needs the *Interface next hop*: the address is only
  meaningful on one link (RFC 4861).
* A device cannot carry two routes with the same VRF, prefix, next hop and interface next hop. The form, the CSV
  import and the REST API name the devices that already have it.

## Typical uses

* **A default route on many devices.** Create the route once and select all the devices it applies
  to, instead of one record per device.
* **Floating static routes.** Create the backup route with a higher *Distance* than the primary.
* **Route in a VRF.** Select the *VRF*; the same prefix can then exist in several VRFs.
* **Seeing a device's routes.** Open the device and use the **Static Routes** tab, which shows the
  routes assigned to it and how many there are.

## Where static routes connect to other protocols

OSPF can redistribute static routes ([OSPF redistribution](ospf.md#redistribution)); the *Tag* is the
usual way to pick which ones.

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

```text
Static route
├─ Destination: prefix · vrf → VRF
├─ Next hop: next_hop · interface_next_hop
├─ Attributes: name · distance · tag · permanent?
└─ Applies to: devices → Device (several)
```
