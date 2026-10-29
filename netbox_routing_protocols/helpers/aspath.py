import re
from collections import Counter

from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_protocols.helpers.prefix_list import (
    MAX_SEQUENCE,
    SEQUENCE_STEP,
    Overlap,
    resequence_entries,
)

# AS numbers are 32 bits (RFC 6793); the asdot notation writes them as high.low,
# two 16 bit halves (RFC 5396).
MAX_ASN = 4294967295
MAX_ASDOT_PART = 65535

_NUMBER = re.compile(r'\d+(?:\.\d+)?')
_CLASS = re.compile(
    r'\[:(alnum|alpha|blank|cntrl|digit|graph|lower|print|punct|space|upper|xdigit):\]'
)
_REPEAT = re.compile(r'\{(\d+)(?:(,)(\d*))?\}')
_ESCAPABLE = set('.[]\\()*+?{}|^$_-')


def validate_pattern(pattern):
    """
    Check an AS-path pattern as a POSIX extended regular expression (the ERE of POSIX.1-2017).
    The plugin stores and shows the pattern, it does not run it, and it does not support any
    vendor dialect: ``_`` is an ordinary character.

    Returns a list of error messages (empty when the pattern is valid). Only printable ASCII
    is accepted (Unicode digits are not AS numbers). Besides the grammar (balanced groups,
    valid bracket expressions and repetitions, nothing to repeat, empty alternatives), every
    AS number written in it must fit the 32 bit AS_PATH (RFC 6793), in asplain (``65000``)
    or asdot (``1.10``, RFC 5396) notation. Digits inside a bracket expression (``[0-9]``)
    and in a repetition (``{2,3}``) are not AS numbers.
    """
    if not pattern or not pattern.strip():
        return ['The pattern cannot be empty.']

    if any(ord(char) < 32 or ord(char) > 126 for char in pattern):
        return ['The pattern can only have printable ASCII characters.']

    errors = []
    numbers = []
    # one entry per open group: whether its current alternative has something in it
    filled = [False]
    atom = False  # the last item can be repeated
    i = 0
    n = len(pattern)
    while i < n and not errors:
        char = pattern[i]
        if char == '\\':
            if i + 1 >= n:
                errors.append('The pattern cannot end with a backslash.')
            elif pattern[i + 1] not in _ESCAPABLE:
                errors.append(
                    f'"\\{pattern[i + 1]}" is not part of POSIX extended regular '
                    'expressions: a backslash only escapes a special character.'
                )
            i += 2
            atom = filled[-1] = True
        elif char == '[':
            j = i + 1
            if j < n and pattern[j] == '^':
                j += 1
            start = j
            while j < n and (pattern[j] != ']' or j == start):
                if pattern[j] == '[' and pattern[j + 1 : j + 2] == ':':
                    match = _CLASS.match(pattern, j)
                    if not match:
                        errors.append(
                            'Invalid character class in a bracket expression.'
                        )
                        break
                    j = match.end()
                    continue
                if (
                    pattern[j] == '-'
                    and j > start
                    and pattern[j + 1 : j + 2] not in ('', ']')
                    and pattern[j - 1] > pattern[j + 1]
                ):
                    errors.append('Invalid range in a bracket expression.')
                    break
                j += 1
            else:
                if j >= n:
                    errors.append('Unterminated bracket expression: missing "]".')
            i = j + 1
            atom = filled[-1] = True
        elif char == '(':
            filled.append(False)
            atom = False
            i += 1
        elif char == ')':
            if len(filled) == 1:
                errors.append('Unbalanced parenthesis: unexpected ")".')
            elif not filled[-1]:
                errors.append('Empty group or alternative.')
            else:
                filled.pop()
                atom = filled[-1] = True
            i += 1
        elif char == '|':
            if not filled[-1]:
                errors.append('Empty alternative around "|".')
            filled[-1] = False
            atom = False
            i += 1
        elif char in '*+?':
            if not atom:
                errors.append(f'Nothing to repeat before "{char}".')
            i += 1
        elif char == '{':
            match = _REPEAT.match(pattern, i)
            if not match:
                errors.append('Invalid repetition: expected {m}, {m,} or {m,n}.')
            elif not atom:
                errors.append('Nothing to repeat before "{".')
            elif match.group(3) and int(match.group(1)) > int(match.group(3)):
                errors.append('Invalid repetition: the minimum is above the maximum.')
            elif max(int(match.group(1)), int(match.group(3) or 0)) > 255:
                errors.append('Invalid repetition: the limit is 255.')
            i = match.end() if match else n
        elif char == '}':
            errors.append('Unbalanced "}": use "\\}" for a literal brace.')
        elif char in '^$':
            atom = False
            filled[-1] = True
            i += 1
        elif char.isdigit():
            match = _NUMBER.match(pattern, i)
            numbers.append(match.group())
            i = match.end()
            atom = filled[-1] = True
        else:
            i += 1
            atom = filled[-1] = True

    if not errors:
        if len(filled) > 1:
            errors.append('Unbalanced parenthesis: missing ")".')
        elif not filled[-1]:
            errors.append('Empty alternative at the end of the pattern.')

    for value in numbers:
        if '.' in value:
            parts = [int(part) for part in value.split('.')]
            if any(part > MAX_ASDOT_PART for part in parts):
                errors.append(
                    f'"{value}" is not a valid asdot AS number (high.low, each part 0..65535).'
                )
        elif int(value) > MAX_ASN:
            errors.append(f'AS number {value} is above {MAX_ASN} (32 bits, RFC 6793).')
    return errors


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


_MESSAGES = {
    'shadowed': 'is never reached: {other} comes first with the same pattern',
    'shadows': 'comes first and makes {other} unreachable: it has the same pattern',
}


def find_duplicates(entry, others=None):
    """
    The other entries of the AS-path of `entry` with the same pattern, as a list of
    Overlap(kind, entry, message), by sequence. Entries are evaluated by sequence and the
    first match wins, so of two with the same pattern the later one is never reached
    ('shadowed') and the earlier one makes the later unreachable ('shadows'). Whether two
    different regular expressions overlap is not decidable in general, so only identical
    patterns (ignoring surrounding spaces) are reported. `others` can be given to avoid the query.
    """
    if others is None:
        others = entry.aspath.aspath_entries.exclude(pk=entry.pk).order_by('sequence')
    pattern = (entry.pattern or '').strip()
    duplicates = []
    for other in others:
        if other.pk == entry.pk and entry.pk is not None:
            continue
        if (other.pattern or '').strip() != pattern:
            continue
        if other.sequence < entry.sequence:
            kind = 'shadowed'
        elif other.sequence > entry.sequence:
            kind = 'shadows'
        else:
            continue
        duplicates.append(
            Overlap(
                kind,
                other,
                f'Entry {describe_entry(entry)} '
                + _MESSAGES[kind].format(other=f'entry {describe_entry(other)}'),
            )
        )
    return duplicates


def duplicate_warnings(entry):
    """The duplicates of an entry as a list of dicts, for the API"""
    return [
        {
            'kind': duplicate.kind,
            'message': duplicate.message,
            'entry': {
                'id': duplicate.entry.pk,
                'sequence': duplicate.entry.sequence,
                'url': duplicate.entry.get_absolute_url(),
            },
        }
        for duplicate in find_duplicates(entry)
    ]


def resequence(aspath, start=SEQUENCE_STEP, step=SEQUENCE_STEP):
    """Renumber the entries of the AS-path keeping their order, see resequence_entries"""
    return resequence_entries(aspath.aspath_entries, start, step)


def import_duplicates(entries):
    """
    The entries with the same pattern that involve the entries saved by an import, one
    summary per AS-path: a list of (aspath, Counter of kinds, [first messages]), ordered by
    name. Each pair is counted once, from the perspective of the first entry found.
    """
    by_aspath = {}
    for entry in entries:
        by_aspath.setdefault(entry.aspath_id, []).append(entry)

    summaries = []
    for imported in by_aspath.values():
        aspath = imported[0].aspath
        # one query per AS-path: the entries it has now, imported or not
        saved = list(aspath.aspath_entries.all())
        seen = set()
        kinds, examples = Counter(), []
        for entry in imported:
            for duplicate in find_duplicates(entry, others=saved):
                pair = frozenset((entry.pk, duplicate.entry.pk))
                if pair in seen:
                    continue
                seen.add(pair)
                kinds[duplicate.kind] += 1
                examples.append(duplicate.message)
        if kinds:
            summaries.append((aspath, kinds, examples))
    return sorted(summaries, key=lambda summary: summary[0].name.lower())


#
# Which entries match an AS_PATH
#

_POSIX_CLASSES = {
    'alnum': 'a-zA-Z0-9',
    'alpha': 'a-zA-Z',
    'blank': ' \\t',
    'cntrl': '\\x00-\\x1f\\x7f',
    'digit': '0-9',
    'graph': '!-~',
    'lower': 'a-z',
    'print': ' -~',
    'punct': '!-/:-@\\[-`{-~',
    'space': ' \\t\\n\\r\\f\\v',
    'upper': 'A-Z',
    'xdigit': '0-9A-Fa-f',
}


def parse_as_path(text):
    """
    The AS_PATH a user typed, as the text the patterns are matched against: AS numbers
    separated by one space. Each one must be a valid AS number (asplain or asdot, see
    validate_pattern), optionally written with the usual ``AS`` prefix (``AS65001``), which
    is dropped: nothing stores it, the patterns are over the bare numbers. Raises
    ValidationError otherwise.
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
        if validate_pattern(token) != []:
            raise ValidationError(
                _('"%(token)s" is not a valid AS number.') % {'token': token}
            )
    return ' '.join(tokens)


def posix_to_python(pattern):
    """
    The pattern (a POSIX extended regular expression that validate_pattern accepts) as a
    Python regular expression. Only the bracket expressions differ: a backslash is an
    ordinary character inside them and the POSIX classes ([:digit:]) are named.
    """
    out = []
    i, n = 0, len(pattern)
    while i < n:
        char = pattern[i]
        if char == '\\':
            out.append(pattern[i : i + 2])
            i += 2
        elif char == '[':
            i += 1
            negate = pattern[i : i + 1] == '^'
            i += negate
            items = []
            first = True
            while i < n and (pattern[i] != ']' or first):
                first = False
                if pattern.startswith('[:', i):
                    end = pattern.index(':]', i)
                    items.append(_POSIX_CLASSES[pattern[i + 2 : end]])
                    i = end + 2
                elif (
                    pattern[i] == '-'
                    and items
                    and pattern[i + 1 : i + 2] not in ('', ']')
                    and not items[-1].endswith('-')
                ):
                    items.append('-')
                    i += 1
                else:
                    items.append(re.escape(pattern[i]))
                    i += 1
            i += 1
            out.append('[' + ('^' if negate else '') + ''.join(items) + ']')
        else:
            out.append(char)
            i += 1
    return ''.join(out)


def entry_matches(entry, path):
    """Whether the pattern of the entry matches the AS_PATH text (see parse_as_path)"""
    try:
        return re.search(posix_to_python(entry.pattern), path) is not None
    except (re.error, ValueError, KeyError, IndexError):
        # a pattern saved before it was validated, that the engine does not read
        return False


def evaluate_path(path, entries):
    """
    Evaluate an AS_PATH text against entries of any number of AS-paths: a list of
    (aspath, [(entry, effective)]) by name, with the entries that match it by sequence. The
    first one of each AS-path is the effective: the action of the AS-path for that path.
    AS-paths with no matching entry are not returned.
    """
    results = {}
    for entry in sorted(entries, key=lambda e: (e.aspath.name.lower(), e.sequence)):
        if entry_matches(entry, path):
            results.setdefault(entry.aspath, []).append(entry)
    return [
        (aspath, [(entry, index == 0) for index, entry in enumerate(matches)])
        for aspath, matches in results.items()
    ]
