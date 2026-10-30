from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_protocols.helpers.prefix_list import (
    MAX_SEQUENCE,
    SEQUENCE_STEP,
    resequence_entries,
)


def user_entries(route_policy):
    """The entries of the route policy that the user writes: all but the final deny"""
    return route_policy.route_policy_entries.filter(implicit=False)


def next_sequence(route_policy, after=0):
    """
    The sequence number for a new entry of the route policy: the next multiple of the step
    above the last one (10 for an empty policy). `after` is the last one assigned in the
    same request and not saved yet.
    """
    last = user_entries(route_policy).aggregate(last=Max('sequence'))['last'] or 0
    sequence = (max(last, after) // SEQUENCE_STEP + 1) * SEQUENCE_STEP
    if sequence > MAX_SEQUENCE:
        raise ValidationError(_('The route policy has no sequence number left.'))
    return sequence


def resequence(route_policy, start=SEQUENCE_STEP, step=SEQUENCE_STEP):
    """
    Renumber the entries of the route policy keeping their order, see resequence_entries.
    The final deny keeps its place at the end. Returns how many entries changed.
    """
    # the number above the maximum is the one of the final deny
    return resequence_entries(user_entries(route_policy), start, step, reserve=1)
