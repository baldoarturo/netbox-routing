from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_protocols.helpers.prefix_list import (
    MAX_SEQUENCE,
    SEQUENCE_STEP,
    resequence_entries,
)


def next_sequence(route_policy, after=0):
    """
    The sequence number for a new entry of the route policy: the next multiple of the step
    above the last one (10 for an empty policy). `after` is the last one assigned in the
    same request and not saved yet.
    """
    last = (
        route_policy.route_policy_entries.aggregate(last=Max('sequence'))['last'] or 0
    )
    sequence = (max(last, after) // SEQUENCE_STEP + 1) * SEQUENCE_STEP
    if sequence > MAX_SEQUENCE:
        raise ValidationError(_('The route policy has no sequence number left.'))
    return sequence


def resequence(route_policy, start=SEQUENCE_STEP, step=SEQUENCE_STEP):
    """
    Renumber the entries of the route policy keeping their order, see resequence_entries.
    The continue of an entry (`flow_control`) names the sequence of another entry, so it
    follows the entry it points to: a continue to 30 that becomes 20 is rewritten to 20.
    Returns how many entries changed their sequence.
    """
    with transaction.atomic():
        entries = route_policy.route_policy_entries
        order = list(entries.order_by('sequence').values_list('sequence', flat=True))
        new = {old: start + step * index for index, old in enumerate(order)}
        changed = resequence_entries(entries, start, step)
        if changed:
            # 0 means "next entry", not a sequence; a target that does not exist is kept
            for entry in entries.filter(flow_control__in=[o for o in new if o != 0]):
                if new[entry.flow_control] != entry.flow_control:
                    entry.flow_control = new[entry.flow_control]
                    entry.save()
    return changed
