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
| Action | Permit (the default in the form) or Deny. The action belongs to the entry, as on routers; the route maps and BGP policies that use the list only decide *where* it is applied. |
| Prefix | A prefix from NetBox IPAM (**IPAM → Prefixes**). It must be of the family of the list. |
| Any | Matches the all-zeros prefix of the family (`0.0.0.0/0` or `::/0`). NetBox IPAM cannot hold that prefix, so this checkbox stands for it. With *LE* set to the longest length (32 or 128) it matches *every* prefix. Leave *Prefix* empty when you use it. |
| GE / LE | The length range of the match, as on routers. *GE* ("greater than or equal") and *LE* ("less than or equal") are lengths, not counts. Both are inclusive. |
| Exact | Form only: tick it to match the prefix itself, with no length range. GE and LE are disabled while it is ticked and the form refuses them if both come in. It is the same as leaving GE and LE empty. |

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

### Using the API

The REST API (`/api/plugins/routing/objects/prefix-list-entry/`) follows the same rules as the form:

- **`sequence`** can be left out; the entry gets the next multiple of 10 after the highest one in the list. Any value from 1 to 4294967294 is accepted when you send it.
- **Any:** send `"any_prefix": true` and no prefix, or send the prefix as `"any"`, `"0.0.0.0/0"` or `"::/0"`; all three store the same entry.
- **`eq`** (write only, not in the form) sets GE and LE to the same length.
- **`exact`** (write only) is the *Exact* checkbox of the form: `true` matches the prefix itself, so `ge`, `le` and `eq` must be empty (an error otherwise); with `any` it is only the all-zeros prefix.
- The response of a create or update carries a **`warnings`** list with the overlaps described below, so scripts can show them. The entry is saved anyway.

### Importing lists and entries

**Prefix Lists** and **Prefix List Entries** have an *Import* button in the menu (CSV, JSON or YAML, like any NetBox object). Import the lists first, then their entries.

Prefix lists:

```
name,family,description
EDGE-IN,4,Routes accepted from the edge
EDGE-IN-V6,6,
```

`family` is 4 or 6 (4 when empty).

Entries:

```
prefix_list,action,prefix,sequence,ge,le,eq,vrf
EDGE-IN,permit,10.0.0.0/8,,16,24,,
EDGE-IN,deny,192.0.2.0/24,,,,,
EDGE-IN,permit,any,,,,,
```

| Column | Meaning |
| --- | --- |
| `prefix_list` | Name of an existing list. |
| `action` | `permit` or `deny`. |
| `prefix` | A prefix that **already exists in IPAM**, written as a CIDR, or `any`. Nothing is created in IPAM: a prefix that does not exist is an error. |
| `vrf` | Name of the VRF of the IPAM prefix. Only needed when the same CIDR exists in several VRFs; without it that is an error. |
| `sequence` | Empty takes the next free one of the list (steps of 10, consecutive inside one import). |
| `ge`, `le`, `eq` | As in the form. `eq` sets GE and LE to one length, and cannot be combined with them. Leave all three empty to match the prefix itself (with `any`, every prefix). |

The whole import is rolled back if one row is wrong, and the rows are checked with the same rules as the form (family, lengths, sequence). The entries are saved even if they overlap (see below); after the import you get **a summary per list** with how many overlaps of each kind involve the imported entries (each pair counted once, including the entries the list already had) and the first examples.

### Resequencing a list

When the gaps between the sequence numbers are used up, the **Resequence** button on the page of the list renumbers its entries **keeping their order**: it asks for the first number (10 by default) and the step (10 by default), and the entries get the first number and then each next one the step above. The order does not change, so neither does what the list does; the overlap results are the same. Entries that already have their number are left alone, and it refuses to run, changing nothing, if the last number would go over 4294967294. You need the permission to change prefix list entries.

Over the API: `PATCH /api/plugins/routing/objects/prefix-list/<id>/resequence/` with optional `start` and `step`; it answers `{"changed": <number of entries renumbered>}`.

### Duplicating a prefix list

The **Duplicate** button on the page of a list makes a copy **with all its entries**: a form asks for the name of the copy (it suggests *name copy*) and its description, and the copy keeps the family, comments, tags and owner. Every entry is copied as it is (sequence, action, prefix or Any, GE/LE, description, tags) and keeps pointing to the same IPAM prefixes. The copy has the same address family: the entries of an IPv4 list cannot be copied into an IPv6 one. You need the permission to add prefix lists and prefix list entries.

### Deleting a prefix list in use

A prefix list that other objects use can be deleted. Before you confirm, the dialog (and the bulk delete page) lists **every object that refers to it, whatever the protocol**: BGP policy templates and peer address families, route map entries, and anything that points to a prefix list in the future, grouped by type with links. Deleting the list leaves the reference empty in those objects (and removes the list from the route map entries), so their filtering stops applying until you choose another list. The list's own entries are deleted with it.

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

### Adding entries from the list

The page of a prefix list shows its entries in a table at the bottom, with an **Add entry** button that opens the entry form with the list already chosen and the next sequence number suggested. After saving, you come back to the list's page.

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
| Action | Permit (the default in the form) or Deny. The action belongs to the entry, as on routers; the route maps and BGP policies that use the list only decide *where* it is applied. |
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

## Field reference

Every object also has `description`, `comments`, tags and custom fields, which are not repeated below. Names are the ones used by the REST API and the CSV import; the web form shows the same words with spaces. `?` marks a yes/no field, `→` a link to another object and `{a | b}` the allowed choices.

```text
Prefix list
├─ name · family {IPv4 | IPv6}
└─ Entry
    ├─ prefix_list → Prefix list
    ├─ Match: prefix → Prefix · any_prefix? · ge · le
    └─ Result: sequence · action {Permit | Deny}

Community list
├─ name · tenant → Tenant
└─ Entry: community_list → Community list · community → Community · action {Permit | Deny}

Community
└─ name · community · status {Active | Reserved | Deprecated} · role → Role · tenant → Tenant

AS path
├─ name
└─ Entry: aspath → AS path · sequence · action {Permit | Deny} · pattern

Route map
├─ name
└─ Entry
    ├─ route_map → Route map
    ├─ Result: sequence · action {Permit | Deny} · flow_control
    ├─ Match: match · match_prefix_list → Prefix list · match_community_list → Community list
    │         · match_community → Community · match_aspath → AS path
    └─ Set: set
```
