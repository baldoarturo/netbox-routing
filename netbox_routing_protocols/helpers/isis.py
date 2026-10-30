# SPDX-License-Identifier: Apache-2.0

import re

import netaddr

from django.utils.translation import gettext_lazy as _

__all__ = (
    'metric_errors',
    'net_error',
    'net_parts',
    'range_errors',
    'router_id_error',
    'auth_pair_errors',
    'type_levels',
)


def scope_levels(value):
    """The levels a level scope (level-1, level-2, level-1-2) covers."""
    return {'level-1': {1}, 'level-2': {2}}.get(value, {1, 2})


def type_levels(value):
    """The IS-IS levels an IS type or circuit type runs; an empty value is the
    default level-1-2 (ISO 10589 / RFC 1195)."""
    return {'level-1': {1}, 'level-2-only': {2}}.get(value, {1, 2})


# A NET (Network Entity Title) is a string of whole bytes written in hex with optional dots: the
# area address (1-13 bytes, the first one is the AFI), a 6-byte system ID and a 1-byte N-selector
# that is 00 on a router (ISO 10589, RFC 1195). 20 bytes at most (ISO 8348).
NET_MAX_BYTES = 20
NET_MIN_BYTES = 8
SYSTEM_ID_BYTES = 6
WIDE_METRIC_MAX = 16777214  # RFC 5305: 24-bit interface metric, all ones is reserved
NARROW_METRIC_MAX = 63  # ISO 10589: 6-bit metric


def net_error(value):
    """Return why a NET is not valid, or None."""
    digits = value.replace('.', '')
    if not digits or not re.fullmatch(r'[0-9A-Fa-f]+', digits) or len(digits) % 2:
        return _('Enter a NET made of hex bytes, e.g. 49.0001.0000.0000.0001.00.')
    size = len(digits) // 2
    if not NET_MIN_BYTES <= size <= NET_MAX_BYTES:
        return _(
            'A NET is %(min)s to %(max)s bytes: area address, 6-byte system ID and selector.'
        ) % {'min': NET_MIN_BYTES, 'max': NET_MAX_BYTES}
    if digits[-2:] != '00':
        return _('The N-selector (last byte) of a router NET must be 00.')
    return None


def net_parts(value):
    """The (area address, system ID) of a valid NET as lowercase dotted hex, or None.
    The last byte is the selector and the 6 bytes before it the system ID
    (ISO 10589), whatever the length of the area address."""
    if not value or net_error(value):
        return None
    digits = value.replace('.', '').lower()
    area, system_id = digits[:-14], digits[-14:-2]
    # the AFI is the first byte, then groups of two bytes
    area = '.'.join([area[:2], *(area[i : i + 4] for i in range(2, len(area), 4))])
    return (
        area,
        '.'.join(system_id[i : i + 4] for i in range(0, 12, 4)),
    )


def range_errors(obj, rules):
    """Field-keyed errors for the (field, minimum, maximum) rules whose value is set;
    a None bound is open."""
    errors = {}
    for field, low, high in rules:
        value = getattr(obj, field)
        if value is None:
            continue
        if (low is not None and value < low) or (high is not None and value > high):
            if high is None:
                msg = _('Ensure this value is at least %(min)s.') % {'min': low}
            else:
                msg = _('Ensure this value is between %(min)s and %(max)s.') % {
                    'min': low,
                    'max': high,
                }
            errors[field] = msg
    return errors


def metric_errors(obj, fields, metric_style):
    """A narrow metric is 1-63 (ISO 10589); wide metrics are 1-16777214 (RFC 5305)."""
    high = NARROW_METRIC_MAX if metric_style == 'narrow' else WIDE_METRIC_MAX
    return range_errors(obj, [(field, 1, high) for field in fields])


def router_id_error(value, version):
    """The TE router ID is an IP address of the family, or on Cisco an interface name."""
    if not value or not re.fullmatch(r'[0-9.]+|[0-9A-Fa-f:]+', value):
        return None  # an interface reference
    try:
        address = netaddr.IPAddress(value)
    except (netaddr.AddrFormatError, ValueError):
        return _('Enter a valid IP address or an interface name.')
    if address.version != version:
        return _('Enter an IPv%(version)s address.') % {'version': version}
    return None


def auth_pair_errors(type_value, key_value, type_field, key_field):
    """An IS-IS auth (type, key) pair is only meaningful together; return the
    field-keyed error(s) for a half-configured pair (shared by every IS-IS clean())."""
    if type_value and not key_value:
        return {
            key_field: _(
                'An authentication key is required when an authentication type is set.'
            )
        }
    if key_value and not type_value:
        return {
            type_field: _(
                'An authentication type is required when an authentication key is set.'
            )
        }
    return {}
