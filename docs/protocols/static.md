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
| Metric | The route's preference when several routes to the same prefix exist; lower wins. Defaults to 1. |
| Permanent | Marks a route that stays installed even if its next hop becomes unreachable (the `permanent` keyword on some platforms). |
| Tag | Optional number to match the route in policies, for example when redistributing static routes into OSPF. |
| Devices | The devices that have this route configured. |

**A route needs a next hop**: either an IP next hop, an interface next hop, or both. The form refuses
a route with neither.

## Typical uses

* **A default route on many devices.** Create the route once and select all the devices it applies
  to, instead of one record per device.
* **Floating static routes.** Create the backup route with a higher *Metric* than the primary.
* **Route in a VRF.** Select the *VRF*; the same prefix can then exist in several VRFs.
* **Seeing a device's routes.** Open the device and use the **Static Routes** tab, which shows the
  routes assigned to it and how many there are.

## Where static routes connect to other protocols

OSPF can redistribute static routes ([OSPF redistribution](ospf.md#redistribution)); the *Tag* is the
usual way to pick which ones.
