import re
from ipaddress import AddressValueError, IPv4Address, IPv6Address

from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from netbox_routing_protocols.choices import CommunityTypeChoices
from netbox_routing_protocols.helpers.prefix_list import (
    MAX_SEQUENCE,
    SEQUENCE_STEP,
    Overlap,
)

__all__ = (
    'WELL_KNOWN',
    'parse',
    'normalize',
    'well_known_name',
    'next_sequence',
    'find_duplicates',
)

MAX_16 = 0xFFFF
MAX_32 = 0xFFFFFFFF

# Well-known communities (IANA registry), name -> (value, RFC)
WELL_KNOWN = {
    'GRACEFUL_SHUTDOWN': ('65535:0', 'RFC 8326'),
    'ACCEPT_OWN': ('65535:1', 'RFC 7611'),
    'LLGR_STALE': ('65535:6', 'RFC 9494'),
    'NO_LLGR': ('65535:7', 'RFC 9494'),
    'BLACKHOLE': ('65535:666', 'RFC 7999'),
    'NO_EXPORT': ('65535:65281', 'RFC 1997'),
    'NO_ADVERTISE': ('65535:65282', 'RFC 1997'),
    'NO_EXPORT_SUBCONFED': ('65535:65283', 'RFC 1997'),
    'NOPEER': ('65535:65284', 'RFC 3765'),
}
_BY_VALUE = {value: (name, rfc) for name, (value, rfc) in WELL_KNOWN.items()}
# Names are accepted in upper or lower case, with "-" or "_"; "local-AS" is how
# Cisco calls NO_EXPORT_SUBCONFED
_ALIASES = {'LOCAL_AS': 'NO_EXPORT_SUBCONFED'}

_EXTENDED_PREFIXES = {'rt': 'rt', 'target': 'rt', 'soo': 'soo', 'origin': 'soo'}
_EXTENDED = re.compile(r'^(rt|target|soo|origin):(\S+):(\d+)$', re.IGNORECASE)
_STANDARD = re.compile(r'^(\d+):(\d+)$')
_LARGE = re.compile(r'^(\d+):(\d+):(\d+)$')

FORMATS_HELP = _(
    'A standard community "ASN:value" (two 16-bit numbers, RFC 1997) or a 32-bit '
    'number, a well-known name such as no-export, an extended community '
    '"rt:ASN:value" or "soo:ASN:value" (RFC 4360, RFC 5668; with an IPv4 or IPv6 '
    'address instead of the ASN, RFC 4360, RFC 5701) or a large community '
    '"ASN:value1:value2" (three 32-bit numbers, RFC 8092).'
)


def _extended(prefix, admin, number):
    prefix = _EXTENDED_PREFIXES[prefix.lower()]
    number = int(number)
    try:
        # IPv4 address (RFC 4360) or IPv6 address (RFC 5701) administrator, with a
        # 2-octet value
        admin = str(IPv6Address(admin) if ':' in admin else IPv4Address(admin))
        if number > MAX_16:
            raise ValidationError(
                _('With an IP address the value is a 16-bit number (0 to 65535).')
            )
    except AddressValueError:
        if not admin.isdigit():
            raise ValidationError(
                _('"%(admin)s" is neither an AS number nor an IP address.')
                % {'admin': admin}
            )
        admin = int(admin)
        if admin > MAX_32:
            raise ValidationError(_('The AS number is above 4294967295.'))
        # 2-octet ASN + 4-octet value (RFC 4360) or 4-octet ASN + 2-octet value (RFC 5668)
        limit = MAX_32 if admin <= MAX_16 else MAX_16
        if number > limit:
            raise ValidationError(
                _('With AS %(asn)s the value is at most %(limit)s.')
                % {'asn': admin, 'limit': limit}
            )
    return f'{prefix}:{admin}:{number}'


def parse(value):
    """
    The type and the normalised text of a community, or ValidationError. Normal form:
    `ASN:value` for standard (a bare 32-bit number and the well-known names are
    converted), `rt:`/`soo:` for extended, `a:b:c` without leading zeros for large.
    """
    text = (value or '').strip()
    name = text.upper().replace('-', '_')
    name = _ALIASES.get(name, name)
    if name in WELL_KNOWN:
        return CommunityTypeChoices.TYPE_STANDARD, WELL_KNOWN[name][0]

    if text.isdigit():
        number = int(text)
        if number > MAX_32:
            raise ValidationError(_('A standard community is a 32-bit number.'))
        return (
            CommunityTypeChoices.TYPE_STANDARD,
            f'{number >> 16}:{number & MAX_16}',
        )

    if match := _STANDARD.match(text):
        asn, number = map(int, match.groups())
        if asn > MAX_16 or number > MAX_16:
            raise ValidationError(
                _(
                    'A standard community is two 16-bit numbers (0 to 65535). For a '
                    '4-byte AS use an extended ("rt:ASN:value") or large '
                    '("ASN:value1:value2") community.'
                )
            )
        return CommunityTypeChoices.TYPE_STANDARD, f'{asn}:{number}'

    if match := _LARGE.match(text):
        parts = list(map(int, match.groups()))
        if max(parts) > MAX_32:
            raise ValidationError(
                _('The three numbers of a large community are at most 4294967295.')
            )
        return CommunityTypeChoices.TYPE_LARGE, ':'.join(map(str, parts))

    if match := _EXTENDED.match(text):
        return CommunityTypeChoices.TYPE_EXTENDED, _extended(*match.groups())

    raise ValidationError(_('Not a community. ') + FORMATS_HELP)


def normalize(value):
    return parse(value)[1]


def well_known_name(value):
    """`(name, rfc)` when the normalised standard community has a well-known name"""
    return _BY_VALUE.get(value)


def next_sequence(community_list, after=0):
    """
    The sequence number for a new entry of the list: the next multiple of the step above
    the last one (10 for an empty list). `after` is the last one assigned in the same
    request and not saved yet.
    """
    last = community_list.communitylistentries.aggregate(last=Max('sequence'))['last']
    sequence = (max(last or 0, after) // SEQUENCE_STEP + 1) * SEQUENCE_STEP
    if sequence > MAX_SEQUENCE:
        raise ValidationError(_('The community list has no sequence number left.'))
    return sequence


def find_duplicates(entry):
    """
    The other entries of the list of `entry` with the same community, as a list of
    Overlap(kind, entry, message), by sequence. Entries are evaluated by sequence and the
    first match wins, so of two entries with the same community the later one is never
    reached ('shadowed') and the earlier one makes the later unreachable ('shadows').
    """
    duplicates = []
    others = entry.community_list.communitylistentries.filter(
        community_id=entry.community_id
    ).order_by('sequence')
    for other in others:
        if other.pk == entry.pk:
            continue
        if other.sequence < entry.sequence:
            kind, text = 'shadowed', 'is never reached: {} comes first'
        elif other.sequence > entry.sequence:
            kind, text = 'shadows', 'comes first and makes {} unreachable'
        else:
            continue
        duplicates.append(
            Overlap(
                kind,
                other,
                f'Entry {entry.sequence} {entry.action} {entry.community} '
                + text.format(
                    f'entry {other.sequence} {other.action} {other.community}'
                ),
            )
        )
    return duplicates
