from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_plugin.helpers import aspath as aspath_helpers
from netbox_routing_plugin.helpers import prefix_list as prefix_list_helpers
from netbox_routing_plugin.helpers.prefix_list import (
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


#
# Evaluation of a route: which entry of a route policy decides it
#
class Route:
    """
    The attributes of a route to evaluate. Every one is optional: a condition on an
    attribute that was not given cannot be met.
    """

    def __init__(
        self,
        prefix=None,
        as_path=None,
        communities=None,
        next_hop=None,
        metric=None,
        origin=None,
        tag=None,
        weight=None,
    ):
        self.prefix = prefix  # netaddr.IPNetwork
        self.as_path = as_path  # text, see aspath.parse_as_path
        self.communities = (
            communities  # normalised values, see community.parse_communities
        )
        self.next_hop = next_hop  # netaddr.IPAddress
        self.metric = metric
        self.origin = origin
        self.tag = tag
        self.weight = weight


def prefix_list_permits(prefix_list, prefix):
    """A prefix list matches when its first matching entry permits; no entry is a deny"""
    for entry in prefix_list.prefix_list_entries.order_by('sequence'):
        if prefix_list_helpers.entry_matches(entry, prefix):
            return entry.action == 'permit'
    return False


def aspath_permits(aspath, path):
    """The same for an AS-path; None when a pattern took too long"""
    for entry in aspath.aspath_entries.order_by('sequence'):
        found = aspath_helpers.entry_matches(entry, path)
        if found is None:
            return None
        if found:
            return entry.action == 'permit'
    return False


def community_list_carried(community_list, carried):
    """
    The condition of a community list is match all: the route carries all the communities
    of the permit entries of the list (a list without permit entries is never met).
    """
    wanted = {
        entry.community.community
        for entry in community_list.communitylistentries.filter(
            action='permit'
        ).select_related('community')
    }
    return bool(wanted) and wanted <= set(carried)


def entry_checks(entry, route):
    """
    The conditions of an entry against a route: a list of (label, ok, detail). An entry
    without conditions has none and matches every route.
    """
    checks = []

    def add(label, ok, detail=''):
        checks.append((label, bool(ok), detail))

    given = _('not given')
    lists = list(entry.match_prefix_list.all())
    if lists:
        if route.prefix is None:
            add(_('Prefix list'), False, given)
        else:
            met = [pl for pl in lists if prefix_list_permits(pl, route.prefix)]
            add(_('Prefix list'), met, ', '.join(pl.name for pl in (met or lists)))
    paths = list(entry.match_aspath.all())
    if paths:
        if route.as_path is None:
            add(_('AS path'), False, given)
        else:
            met = [p for p in paths if aspath_permits(p, route.as_path)]
            add(_('AS path'), met, ', '.join(p.name for p in (met or paths)))
    community_lists = list(entry.match_community_list.all())
    if community_lists:
        if route.communities is None:
            add(_('Community list'), False, given)
        else:
            met = [
                cl
                for cl in community_lists
                if community_list_carried(cl, route.communities)
            ]
            add(
                _('Community list'),
                met,
                ', '.join(cl.name for cl in (met or community_lists)),
            )
    if entry.match_next_hop_id:
        wanted = entry.match_next_hop.address.ip
        add(
            _('Next hop'),
            route.next_hop is not None and route.next_hop == wanted,
            f'{wanted}' if route.next_hop is not None else given,
        )
    for label, wanted, value in (
        (_('Metric'), entry.match_metric, route.metric),
        (_('Origin'), entry.match_origin or None, route.origin),
        (_('Tag'), entry.match_tag, route.tag),
        (_('Weight'), entry.match_weight, route.weight),
    ):
        if wanted is not None:
            add(
                label,
                value is not None and value == wanted,
                f'{wanted}' if value is not None else given,
            )
    return checks


def describe_settings(entry):
    """What a permit entry sets, as a list of texts"""
    texts = []
    if entry.set_local_preference is not None:
        texts.append(f'local-preference {entry.set_local_preference}')
    if entry.set_next_hop_id:
        texts.append(f'next-hop {entry.set_next_hop.address.ip}')
    if entry.set_aspath_prepend:
        texts.append(f'as-path prepend {entry.aspath_prepend_text}')
    if entry.set_community_list_id:
        texts.append(
            f'community {entry.set_community_mode or "replace"} '
            f'{entry.set_community_list.name}'
        )
    if entry.set_metric is not None:
        texts.append(f'metric {entry.set_metric_mode or "set"} {entry.set_metric}')
    if entry.set_origin:
        texts.append(f'origin {entry.set_origin}')
    if entry.set_tag is not None:
        texts.append(f'tag {entry.set_tag}')
    if entry.set_weight is not None:
        texts.append(f'weight {entry.set_weight}')
    return texts


def evaluate(route_policy, route, visited=()):
    """
    Walk the route policy as a router does: the entries in order, the first one that
    matches decides. A permit entry that jumps goes on in the other policy and does not
    come back. Returns {'steps', 'result'}: the steps are dicts (policy, entry, checks,
    matched, settings) up to and including the deciding one; the result is `permit` or
    `deny`. The final deny of the policy decides what no entry matched.
    """
    steps = []
    visited = (*visited, route_policy.pk)
    entries = route_policy.route_policy_entries.select_related(
        'match_next_hop', 'set_next_hop', 'set_community_list', 'jump_policy'
    ).prefetch_related('match_prefix_list', 'match_aspath', 'match_community_list')
    for entry in entries.order_by('sequence'):
        checks = entry_checks(entry, route)
        matched = all(ok for _label, ok, _detail in checks)
        step = {
            'policy': route_policy,
            'entry': entry,
            'checks': checks,
            'matched': matched,
            'settings': describe_settings(entry) if matched else [],
        }
        steps.append(step)
        if not matched:
            continue
        if entry.action == 'deny':
            return {'steps': steps, 'result': 'deny'}
        jump = entry.jump_policy
        if jump is not None and jump.pk not in visited:
            outcome = evaluate(jump, route, visited)
            return {'steps': steps + outcome['steps'], 'result': outcome['result']}
        return {'steps': steps, 'result': 'permit'}
    # Cannot happen while the policy has its final deny, but a policy made by a bulk create may not
    return {'steps': steps, 'result': 'deny'}
