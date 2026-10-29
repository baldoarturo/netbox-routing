import re
import time

import regex
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_protocols.helpers.prefix_list import (
    MAX_SEQUENCE,
    SEQUENCE_STEP,
    resequence_entries,
)

# AS numbers are 32 bits (RFC 6793); the asdot notation writes them as high.low,
# two 16 bit halves (RFC 5396).
MAX_ASN = 4294967295
MAX_ASDOT_PART = 65535

# How long a pattern may take on a path in the match tool, in seconds: a pattern that
# backtracks without end (catastrophic) is cut instead of hanging the server
MATCH_TIMEOUT = 0.2
# ... and how long all the entries of a request may take together, in seconds: the entries
# left when it is over are not evaluated
MATCH_BUDGET = 5.0

# What is not an AS number inside a pattern: escapes (\\1, \\d), bracket expressions
# ([0-9]) and repetitions ({2,3})
_NOT_NUMBERS = re.compile(r'\\.|\[(?:\\.|[^\]\\])*\]|\{\d*,?\d*\}')
_NUMBER = re.compile(r'\d+')


def validate_pattern(pattern):
    """
    Check an AS-path pattern: a regular expression of the ``regex`` module (the engine the
    match tool runs, a superset of the ``re`` of Python that also reads the POSIX classes
    such as ``[[:digit:]]``) over the AS numbers of the path, written as text separated by
    spaces. The plugin does not support any vendor dialect. It returns a list of error
    messages (empty when the pattern is valid): the pattern cannot be empty, only printable
    ASCII is accepted (Unicode digits are not AS numbers), it must compile, and every AS
    number written in it must fit the 32 bit AS_PATH (RFC 6793). Digits in escapes, bracket
    expressions and repetitions are not AS numbers; the dot is the regular expression
    wildcard, so an asdot number (RFC 5396) is written with an escaped dot.
    """
    if not pattern or not pattern.strip():
        return ['The pattern cannot be empty.']
    if any(ord(char) < 32 or ord(char) > 126 for char in pattern):
        return ['The pattern can only have printable ASCII characters.']

    try:
        regex.compile(pattern)
    except (regex.error, RecursionError, OverflowError) as e:
        return [f'Invalid regular expression: {e}.']

    return [
        f'AS number {value} is above {MAX_ASN} (32 bits, RFC 6793).'
        for value in _NUMBER.findall(_NOT_NUMBERS.sub(' ', pattern))
        if int(value) > MAX_ASN
    ]


#
# Sequence numbers and unreachable entries
#


def next_sequence(aspath, after=0):
    """
    The sequence number for a new entry of the AS-path: the next multiple of the step above
    the last one (10 for an empty list). `after` is the last one assigned in the same
    request and not saved yet.
    """
    last = aspath.aspath_entries.aggregate(last=Max('sequence'))['last'] or 0
    sequence = (max(last, after) // SEQUENCE_STEP + 1) * SEQUENCE_STEP
    if sequence > MAX_SEQUENCE:
        raise ValidationError(_('The AS-path has no sequence number left.'))
    return sequence


def describe_entry(entry):
    """E.g. `20 permit ^65001_`"""
    return f'{entry.sequence} {entry.action} {entry.pattern}'


def resequence(aspath, start=SEQUENCE_STEP, step=SEQUENCE_STEP):
    """Renumber the entries of the AS-path keeping their order, see resequence_entries"""
    return resequence_entries(aspath.aspath_entries, start, step)


#
# Which entries match an AS_PATH
#


def parse_as_path(text):
    """
    The AS_PATH a user typed, as the text the patterns are matched against: AS numbers
    separated by one space. Each one must be a valid AS number (asplain or asdot),
    optionally written with the usual ``AS`` prefix (``AS65001``), which is dropped:
    nothing stores it, the patterns are over the bare numbers. Raises ValidationError
    otherwise.
    """
    tokens = [
        token[2:] if token[:2].upper() == 'AS' else token for token in text.split()
    ]
    if not tokens:
        raise ValidationError(_('Type an AS path, for example 65001 65002.'))
    for token in tokens:
        if not re.fullmatch(r'\d+(?:\.\d+)?', token, re.ASCII):
            raise ValidationError(
                _('"%(token)s" is not an AS number: separate the numbers with spaces.')
                % {'token': token}
            )
        if any(
            int(part) > (MAX_ASDOT_PART if '.' in token else MAX_ASN)
            for part in token.split('.')
        ):
            raise ValidationError(
                _('"%(token)s" is not a valid AS number.') % {'token': token}
            )
    return ' '.join(tokens)


def entry_matches(entry, path, timeout=None):
    """
    Whether the pattern of the entry matches the AS_PATH text (see parse_as_path). Returns
    None when the pattern takes longer than the timeout (MATCH_TIMEOUT by default), and
    False when the engine does not read it (a pattern saved before it was validated).
    """
    try:
        return (
            regex.search(entry.pattern, path, timeout=timeout or MATCH_TIMEOUT)
            is not None
        )
    except TimeoutError:
        return None
    except regex.error:
        return False


def evaluate_path(path, entries):
    """
    Evaluate an AS_PATH text against entries of any number of AS-paths. Returns a tuple:
    the list of (aspath, [(entry, effective)]) by name, with the entries that match it by
    sequence (the first matching entry of each AS-path is the effective: the action of the
    AS-path for that path; AS-paths with no matching entry are not returned), the list of
    the entries that took longer than MATCH_TIMEOUT, and the number of entries that were not
    evaluated because the MATCH_BUDGET of the whole request was used up.
    """
    results = {}
    timed_out = []
    not_evaluated = 0
    deadline = time.monotonic() + MATCH_BUDGET
    for entry in sorted(entries, key=lambda e: (e.aspath.name.lower(), e.sequence)):
        left = deadline - time.monotonic()
        if left <= 0:
            not_evaluated += 1
            continue
        matched = entry_matches(entry, path, timeout=min(MATCH_TIMEOUT, left))
        if matched is None:
            timed_out.append(entry)
        elif matched:
            results.setdefault(entry.aspath, []).append(entry)
    return (
        [
            (aspath, [(entry, index == 0) for index, entry in enumerate(matches)])
            for aspath, matches in results.items()
        ],
        timed_out,
        not_evaluated,
    )
