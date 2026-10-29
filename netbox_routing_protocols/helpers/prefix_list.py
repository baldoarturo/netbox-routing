import netaddr
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from collections import namedtuple

__all__ = (
    'any_prefix_value',
    'any_le',
    'SEQUENCE_STEP',
    'next_sequence',
    'entry_network',
    'match_range',
    'entry_matches',
    'describe_entry',
    'Overlap',
    'find_overlaps',
    'overlap_warnings',
    'evaluate_prefix',
    'prefix_list_references',
)

# Distance between the sequence numbers the module assigns, leaving room to insert
# entries in between
SEQUENCE_STEP = 10
# Highest sequence number of an entry
MAX_SEQUENCE = 4294967294


def any_prefix_value(family):
    """The all zeros prefix of an address family, which IPAM cannot hold (no /0)"""
    return '0.0.0.0/0' if family == 4 else '::/0'


def any_le(family):
    """
    The longest prefix length of an address family. With the all zeros prefix, a LE of
    this length matches any prefix.
    """
    return 32 if family == 4 else 128


def next_sequence(prefix_list, after=0):
    """
    The sequence number for a new entry of the list: the next multiple of the step above
    the last one (10 for an empty list). `after` is the last one assigned in the same
    request and not saved yet.
    """
    last = prefix_list.prefix_list_entries.aggregate(last=Max('sequence'))['last'] or 0
    sequence = (max(last, after) // SEQUENCE_STEP + 1) * SEQUENCE_STEP
    if sequence > MAX_SEQUENCE:
        raise ValidationError(_('The prefix list has no sequence number left.'))
    return sequence


#
# What an entry matches
#


def entry_network(entry):
    """The network of an entry: its IPAM prefix, or the all zeros one for Any"""
    if entry.any_prefix:
        return netaddr.IPNetwork(any_prefix_value(entry.prefix_list.family))
    prefix = entry.prefix.prefix
    return (
        prefix if isinstance(prefix, netaddr.IPNetwork) else netaddr.IPNetwork(prefix)
    )


def match_range(entry, network=None):
    """
    The prefix lengths an entry matches inside its network, as (lowest, highest):
    - neither ge nor le: only the length of the network
    - only le: from the length of the network up to le
    - only ge: from ge up to the longest length of the family
    - both: from ge up to le
    """
    network = network or entry_network(entry)
    lowest = entry.ge if entry.ge is not None else network.prefixlen
    if entry.le is not None:
        highest = entry.le
    elif entry.ge is not None:
        highest = any_le(network.version)
    else:
        highest = network.prefixlen
    return lowest, highest


def entry_matches(entry, prefix):
    """Whether the entry matches the (netaddr) prefix"""
    network = entry_network(entry)
    if prefix.version != network.version or prefix not in network:
        return False
    lowest, highest = match_range(entry, network)
    return lowest <= prefix.prefixlen <= highest


def describe_entry(entry):
    """E.g. `20 permit 10.0.0.0/8 ge 24 le 32`"""
    network = 'any' if entry.any_prefix else str(entry_network(entry))
    text = f'{entry.sequence} {entry.action} {network}'
    if entry.ge is not None:
        text += f' ge {entry.ge}'
    if entry.le is not None:
        text += f' le {entry.le}'
    return text


#
# Overlapping entries of a list
#

Overlap = namedtuple('Overlap', ('kind', 'entry', 'message'))


def _relation(this, other):
    """
    How `other` relates to `this`, both entries of the same list: None when they cannot
    match the same prefix, or one of:
    - duplicate: the same prefixes
    - shadowed: an earlier entry matches all the prefixes of this one, which is never reached
    - shadows: this entry matches all the prefixes of a later one, which is never reached
    - nested: one covers the other, the more specific coming first (the usual exception)
    - overlaps: they share some prefixes but neither covers the other
    """
    net_this, net_other = entry_network(this), entry_network(other)
    this_in_other = net_this in net_other
    other_in_this = net_other in net_this
    if not (this_in_other or other_in_this):
        return None
    lo_this, hi_this = match_range(this, net_this)
    lo_other, hi_other = match_range(other, net_other)
    if max(lo_this, lo_other) > min(hi_this, hi_other):
        return None

    other_covers = this_in_other and lo_other <= lo_this and hi_this <= hi_other
    this_covers = other_in_this and lo_this <= lo_other and hi_other <= hi_this
    if other_covers and this_covers:
        return 'duplicate'
    if other_covers:
        return 'shadowed' if other.sequence < this.sequence else 'nested'
    if this_covers:
        return 'shadows' if this.sequence < other.sequence else 'nested'
    return 'overlaps'


_MESSAGES = {
    'duplicate': 'matches the same prefixes as {other}',
    'shadowed': 'is never reached: {other} comes first and matches all its prefixes',
    'shadows': 'comes first and makes {other} unreachable: it matches all its prefixes',
    'nested': 'is nested with {other}: the more specific entry comes first',
    'overlaps': 'overlaps with {other}: they match some prefixes in common',
}


def find_overlaps(entry, others=None):
    """
    The other entries of the list of `entry` that overlap or are nested with it, as a list
    of Overlap(kind, entry, message), by sequence. `others` can be given to avoid the query.
    """
    if others is None:
        others = (
            entry.prefix_list.prefix_list_entries.exclude(pk=entry.pk)
            .select_related('prefix_list', 'prefix')
            .order_by('sequence')
        )
    overlaps = []
    for other in others:
        if other.pk == entry.pk and entry.pk is not None:
            continue
        kind = _relation(entry, other)
        if kind:
            overlaps.append(
                Overlap(
                    kind,
                    other,
                    f'Entry {describe_entry(entry)} '
                    + _MESSAGES[kind].format(other=f'entry {describe_entry(other)}'),
                )
            )
    return overlaps


def overlap_warnings(entry):
    """The overlaps of an entry as a list of dicts, for the API"""
    return [
        {
            'kind': overlap.kind,
            'message': overlap.message,
            'entry': {
                'id': overlap.entry.pk,
                'sequence': overlap.entry.sequence,
                'url': overlap.entry.get_absolute_url(),
            },
        }
        for overlap in find_overlaps(entry)
    ]


#
# Which entries match a prefix
#


def evaluate_prefix(prefix, entries):
    """
    Evaluate a (netaddr) prefix against entries of any number of lists: a list of
    (prefix_list, [(entry, effective)]) by list name, with the entries that match it by
    sequence. The first one of each list is the effective: the action of the list for the
    prefix. Lists with no matching entry are not returned (their action is the implicit deny).
    """
    results = {}
    for entry in sorted(
        entries, key=lambda e: (e.prefix_list.name.lower(), e.sequence)
    ):
        if entry_matches(entry, prefix):
            results.setdefault(entry.prefix_list, []).append(entry)
    return [
        (prefix_list, [(entry, index == 0) for index, entry in enumerate(matches)])
        for prefix_list, matches in results.items()
    ]


#
# Where a prefix list is used
#


def prefix_list_references(prefix_list):
    """
    The objects that refer to the prefix list, of any model (BGP, route maps, and whatever
    protocol points to a prefix list later): a list of (model, queryset). Found from the
    reverse relations, so a new model is listed without touching this. The entries of the list
    are not references: they go with it.
    """
    references = []
    for relation in prefix_list._meta.related_objects:
        model = relation.related_model
        if model._meta.auto_created or model._meta.model_name == 'prefixlistentry':
            continue
        objects = model._default_manager.filter(**{relation.field.name: prefix_list})
        if objects.exists():
            references.append((model, objects))
    return references
