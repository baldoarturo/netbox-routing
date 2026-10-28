# Routing objects

**Routing → Routing Objects**

Routing objects are the building blocks that policies are made of. They are not tied to one protocol:
today BGP policy templates and peer address families point at prefix lists and route maps.

> **About the standards.** Prefix lists, route maps and AS-path filters are **vendor features**: no RFC defines them, and
> every vendor spells them a little differently. What the RFCs define is what they act on: IP
> prefixes ([RFC 4632](https://www.rfc-editor.org/rfc/rfc4632) for IPv4 CIDR,
> [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291) for IPv6), the BGP `AS_PATH` attribute
> ([RFC 4271](https://www.rfc-editor.org/rfc/rfc4271) §5.1.2) and BGP communities
> ([RFC 1997](https://www.rfc-editor.org/rfc/rfc1997)). Those are the pieces the plugin validates.

## Prefix lists

**Prefix Lists** and **Prefix List Entries**

A prefix list is an ordered list of rules; each rule says *permit* or *deny* the prefixes it matches.
Routers evaluate the entries in sequence order and stop at the first that matches.

### Prefix list

| Field | Meaning |
| --- | --- |
| Name | Name of the list, as used in the device configuration. |
| Family | **IPv4** or **IPv6**. A list holds only one family, and the family **cannot be changed** once the list exists (its entries would stop making sense). |

### Prefix list entry

| Field | Meaning |
| --- | --- |
| Prefix list | The list the entry belongs to. |
| Sequence | Evaluation order, 1 to 4294967294 (the range routers accept). Leave it empty and the form suggests the next free one; the API assigns it automatically. |
| Action | Permit or Deny. |
| Prefix | A prefix from NetBox IPAM (**IPAM → Prefixes**). It must be of the family of the list. |
| Any | Matches the all-zeros prefix of the family (`0.0.0.0/0` or `::/0`). NetBox IPAM cannot hold that prefix, so this checkbox stands for it. With *LE* set to the longest length (32 or 128) it matches *every* prefix. Leave *Prefix* empty when you use it. |
| GE / LE | The length range of the match, as on routers. *GE* ("greater than or equal") and *LE* ("less than or equal") are lengths, not counts. |

How to read GE and LE for a prefix `10.0.0.0/8`:

| GE | LE | Matches |
| --- | --- | --- |
| – | – | exactly `10.0.0.0/8` |
| 16 | – | any prefix inside `10.0.0.0/8` of length 16 or longer, up to /32 |
| – | 24 | `10.0.0.0/8` and everything inside it up to /24 |
| 16 | 24 | prefixes inside `10.0.0.0/8` with a length from 16 to 24 |

The plugin refuses a GE or LE that is shorter than the prefix, longer than the family allows (32 for
IPv4, 128 for IPv6) or when GE is greater than LE.

> **A prefix used by a list is protected.** A NetBox prefix referenced by a prefix list entry **cannot be deleted**, and a change to it that
> would make an entry invalid (for example shortening the prefix below the entry's GE) is refused,
> with a message that names the entries. Remove or edit the entries first.

### Overlap warnings

When you save an entry the plugin compares it with the other entries of the list and warns (it still
saves) about:

| Warning | Meaning |
| --- | --- |
| **Duplicate** | Another entry matches exactly the same prefixes. |
| **Shadowed** | An earlier entry matches everything this one matches, so this entry is never reached. |
| **Shadows** | This entry matches everything a later entry matches, so that later entry is never reached. |
| **Nested** | One covers the other, with the more specific first. This is the normal way to write an exception, so it is shown for information. |
| **Overlaps** | They share some prefixes but neither covers the other. |

The entry's detail page lists the overlapping entries, and a prefix list's page shows where the list
is used.

### Search Prefix Match

**Routing → Routing Objects → Search Prefix Match**

Type a prefix or a plain address (`10.0.0.0/24`, `192.0.2.1`, `2001:db8::/32`) and the page shows,
as you type, which prefix list entries match it, **in which sequence**, and whether the entry permits
or denies it. An address is treated as a host prefix. Tick *Include the lists with no match* to see
the lists that do not match too. It answers "would this prefix get through that filter?" without
logging in to a router. It needs the *view* permission on prefix list entries.

## Route maps

**Route Maps** and **Route Map Entries**

A route map is an ordered list of rules like a prefix list, but each rule can *match* several
attributes and *set* others.

| Field | Meaning |
| --- | --- |
| Route map | Name of the map. |
| Sequence | Evaluation order. |
| Action | Permit or Deny. |
| Flow control (continue) | Sequence to continue evaluating at after this entry matches, for platforms that support `continue`. |
| Match prefix list / community list / community / AS path | Link the entry to the NetBox objects it matches on. |
| Match parameters / Set parameters | Free-form **JSON** for everything the links do not cover (for example a local preference to set). The plugin stores it as written; it does not interpret it. |

## AS paths

**AS Path** and **AS Path Entries**

An AS-path list filters routes by the sequence of autonomous systems they crossed (the BGP `AS_PATH`
attribute, [RFC 4271](https://www.rfc-editor.org/rfc/rfc4271) §5.1.2). Each entry has a **sequence**,
an **action** (permit or deny) and a **pattern**: a regular expression in the syntax of your
platform. The pattern is not validated, because every vendor's regex dialect differs.

## Communities

**Community List**, **Community** and **Community List Entry**

BGP communities ([RFC 1997](https://www.rfc-editor.org/rfc/rfc1997)) are 32-bit tags attached to
routes so that policies can act on groups of routes. By convention they are written `ASN:value`, for
example `65000:100`. Keep the list of the communities you use as **Community** objects, so the
meaning of `65000:100` is documented once:

| Field | Meaning |
| --- | --- |
| Community | The community value, for example `65000:100`. |
| Name | Optional human name ("customer routes"). |
| Status | **Active**, **Reserved** or **Deprecated**, to retire a community without deleting its history. |
| Role | A NetBox IPAM role that classifies the community (for example *blackhole*, *customer*). |
| Tenant | Optional owner. |

A **Community List** groups communities under a name, and its **entries** each have an action
(permit or deny) and a community, evaluated like a prefix list. Route map entries can match on a
community or on a whole community list.
