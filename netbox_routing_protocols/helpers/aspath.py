import re

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
    Check an AS-path pattern as a POSIX extended regular expression (the ERE of POSIX.1-2017,
    the family of the Cisco, Arista and FRR AS-path filters) with the ``_`` delimiter those
    platforms add, which is an ordinary character here. The plugin stores and shows the
    pattern; it does not run it, so no vendor dialect is checked beyond POSIX.

    Returns a list of error messages (empty when the pattern is valid). Besides the grammar
    (balanced groups, valid bracket expressions and repetitions, nothing to repeat, empty
    alternatives), every AS number written in it must fit the 32 bit AS_PATH (RFC 6793), in
    asplain (``65000``) or asdot (``1.10``, RFC 5396) notation. Digits inside a bracket
    expression (``[0-9]``) and in a repetition (``{2,3}``) are not AS numbers.
    """
    if not pattern or not pattern.strip():
        return ['The pattern cannot be empty.']

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
