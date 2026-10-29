# AS numbers are 32 bits (RFC 6793); the asdot notation writes them as high.low,
# two 16 bit halves (RFC 5396).
MAX_ASN = 4294967295
MAX_ASDOT_PART = 65535

_PAIRS = {')': '(', ']': '['}


def validate_pattern(pattern):
    """
    Check an AS-path regular expression without choosing a vendor dialect.

    Returns a list of error messages (empty when the pattern is acceptable). The
    pattern must not be blank, its groups and bracket expressions must be balanced,
    and every AS number written in it must fit the 32 bit AS_PATH (RFC 6793), in
    asplain (``65000``) or asdot (``1.10``, RFC 5396) form. Digits inside a bracket
    expression (``[0-9]``) and in a repetition (``{2,3}``) are not AS numbers.
    """
    errors = []
    if not pattern or not pattern.strip():
        return ['The pattern cannot be empty.']

    stack = []
    in_bracket = False
    in_brace = False
    token = ''
    tokens = []
    escaped = False
    for char in pattern + '\0':
        if escaped:
            escaped = False
            token = ''
            continue
        if char.isdigit() or (
            char == '.' and token and not in_bracket and not in_brace
        ):
            token += char
            continue
        if token:
            if not in_bracket and not in_brace:
                tokens.append(token.rstrip('.'))
            token = ''
        if char == '\\':
            escaped = True
        elif in_bracket:
            if char == ']':
                in_bracket = False
                stack.pop()
        elif in_brace:
            if char == '}':
                in_brace = False
        elif char == '[':
            in_bracket = True
            stack.append('[')
        elif char == '{':
            in_brace = True
        elif char == '(':
            stack.append('(')
        elif char == ')':
            if not stack or stack[-1] != _PAIRS[char]:
                errors.append('Unbalanced parenthesis: unexpected ")".')
                break
            stack.pop()
    else:
        if in_bracket:
            errors.append('Unterminated bracket expression: missing "]".')
        elif stack:
            errors.append('Unbalanced parenthesis: missing ")".')
        if in_brace:
            errors.append('Unterminated repetition: missing "}".')

    for value in tokens:
        if '.' in value:
            parts = value.split('.')
            if (
                len(parts) != 2
                or not all(parts)
                or any(int(part) > MAX_ASDOT_PART for part in parts)
            ):
                errors.append(
                    f'"{value}" is not a valid asdot AS number (high.low, each part 0..65535).'
                )
        elif int(value) > MAX_ASN:
            errors.append(f'AS number {value} is above {MAX_ASN} (32 bits, RFC 6793).')

    return errors
