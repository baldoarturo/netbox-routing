# BFD

**Routing → BFD → BFD Profile**

Bidirectional Forwarding Detection ([RFC 5880](https://www.rfc-editor.org/rfc/rfc5880)) detects a
failed link or neighbor in milliseconds, much faster than the routing protocols' own hello timers.
A **BFD profile** is a named set of timers you define once and reuse, so every peer that should
detect failures in the same time points at the same profile.

| Field | Meaning (RFC 5880 name) |
| --- | --- |
| Name | How the profile is referred to. |
| Min TX interval (ms) | The minimum interval the router wants to send BFD packets at (*Desired Min TX Interval*), in **milliseconds**. |
| Min RX interval (ms) | The minimum interval it can receive them at (*Required Min RX Interval*), in **milliseconds**. |
| Multiplier | How many consecutive packets may be lost before the session is declared down (*Detect Mult*). The detection time is the negotiated interval times this value. |
| Hold | Optional hold time, for platforms that have one. It is not part of the RFC. |
| Tenant | Optional owner. |

Where it is used:

* A [BGP peer or peer group](protocols/bgp.md#peers)
  can point at a BFD profile.
* OSPF, IS-IS and EIGRP interfaces only have a **BFD on/off** switch; they do not use profiles, because
  the timers of those protocols come from the interface configuration of the device.

Profiles can also be imported from CSV (**BFD Profile → Import**): one row per profile, with the tenant given by name.

> **Note.** The plugin does not check the intervals against what your platform supports. Choose values your
> hardware can sustain: a profile with very small intervals on a busy router causes false failures.

> **Units.** The timers are entered in **milliseconds**. RFC 5880 (section 4.1) gives the same intervals in
> **microseconds**, so 300 ms is 300000 in the RFC. The plugin does not convert them: enter milliseconds.

## Not implemented yet

The plugin does not model these parts of RFC 5880 and its companions, so a profile cannot set them:

* authentication (RFC 5880 section 6.7);
* the echo function (RFC 5880 section 6.4);
* demand mode (RFC 5880 section 6.6) and the active/passive role (RFC 5880 section 6.1);
* the choice between single-hop sessions (RFC 5881) and multihop sessions (RFC 5883).

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

```text
BFD profile
├─ name · tenant → Tenant
└─ Timers: min_tx_int · min_rx_int · multiplier · hold
```
