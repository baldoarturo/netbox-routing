from django.utils.translation import gettext_lazy as _
from utilities.choices import ChoiceSet


class StaticRouteNextHopTypeChoices(ChoiceSet):
    """
    RFC 8349 `special-next-hop` plus the normal case.
    """

    FORWARD = 'forward'
    BLACKHOLE = 'blackhole'
    UNREACHABLE = 'unreachable'
    PROHIBIT = 'prohibit'
    RECEIVE = 'receive'

    CHOICES = [
        (FORWARD, _('Forward (IP address and/or interface)')),
        (BLACKHOLE, _('Blackhole (silently drop; Null0, discard)')),
        (UNREACHABLE, _('Unreachable (drop, ICMP unreachable; reject)')),
        (PROHIBIT, _('Prohibit (drop, ICMP administratively prohibited)')),
        (RECEIVE, _('Receive (deliver to the local device)')),
    ]
