from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

__all__ = ('any_prefix_value', 'any_le', 'SEQUENCE_STEP', 'next_sequence')

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
