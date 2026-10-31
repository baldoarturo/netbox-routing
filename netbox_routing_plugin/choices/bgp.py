from utilities.choices import ChoiceSet

__all__ = (
    'BGPAddressFamilyChoices',
    'BGPCommunityTypeChoices',
    'BGPRedistributionProtocolChoices',
    'BGPMaximumPrefixActionChoices',
    'BGPStatusChoices',
)


class BGPRedistributionProtocolChoices(ChoiceSet):
    """The routes BGP takes from another protocol into its address family (RFC 4271
    section 9; vendors call it redistribute). BGP itself is not a source."""

    CONNECTED = 'connected'
    STATIC = 'static'
    OSPF = 'ospf'
    ISIS = 'isis'
    EIGRP = 'eigrp'

    CHOICES = [
        (CONNECTED, 'Connected'),
        (STATIC, 'Static'),
        (OSPF, 'OSPF'),
        (ISIS, 'IS-IS'),
        (EIGRP, 'EIGRP'),
    ]


class BGPCommunityTypeChoices(ChoiceSet):
    """The kinds of communities a neighbor is sent (RFC 1997, RFC 4360, RFC 8092)"""

    STANDARD = 'standard'
    EXTENDED = 'extended'
    LARGE = 'large'

    CHOICES = [
        (STANDARD, 'Standard'),
        (EXTENDED, 'Extended'),
        (LARGE, 'Large'),
    ]


class BGPMaximumPrefixActionChoices(ChoiceSet):
    """What happens when a neighbor sends more prefixes than the limit (RFC 4486)"""

    RESTART = 'restart'
    STOP = 'stop'
    WARNING_ONLY = 'warning-only'

    CHOICES = [
        (RESTART, 'Cease, restart after a time'),
        (STOP, 'Cease, until cleared'),
        (WARNING_ONLY, 'Warning only'),
    ]


class BGPAddressFamilyChoices(ChoiceSet):
    IPV4_UNICAST = 'ipv4-unicast'
    IPV6_UNICAST = 'ipv6-unicast'
    VPNV4_UNICAST = 'vpnv4-unicast'
    VPNV6_UNICAST = 'vpnv6-unicast'
    IPV4_MULTICAST = 'ipv4-multicast'
    IPV6_MULTICAST = 'ipv6-multicast'
    VPNV4_MULTICAST = 'vpnv4-multicast'
    VPNV6_MULTICAST = 'vpnv6-multicast'
    IPV4_FLOWSPEC = 'ipv4-flowspec'
    IPV6_FLOWSPEC = 'ipv6-flowspec'
    VPNV4_FLOWSPEC = 'vpnv4-flowspec'
    VPNV6_FLOWSPEC = 'vpnv6-flowspec'
    NSAP = 'nsap'
    L2VPNVPLS = 'l2vpn-vpls'
    L2VPNEVPN = 'l2vpn-evpn'
    LINKSTATE = 'link-state'
    RTFILTER_UNICAST = 'rtfilter-unicast'

    CHOICES = [
        (IPV4_UNICAST, 'IPv4 Unicast'),
        (IPV6_UNICAST, 'IPv6 Unicast'),
        (VPNV4_UNICAST, 'VPNv4 Unicast'),
        (VPNV6_UNICAST, 'VPNv6 Unicast'),
        (IPV4_MULTICAST, 'IPv4 Multicast'),
        (IPV6_MULTICAST, 'IPv6 Multicast'),
        (VPNV4_MULTICAST, 'VPNv4 Multicast'),
        (VPNV6_MULTICAST, 'VPNv6 Multicast'),
        (IPV4_FLOWSPEC, 'IPv4 Flowspec'),
        (IPV6_FLOWSPEC, 'IPv6 Flowspec'),
        (VPNV4_FLOWSPEC, 'VPNv4 Flowspec'),
        (VPNV6_FLOWSPEC, 'VPNv6 Flowspec'),
        (NSAP, 'NSAP'),
        (L2VPNVPLS, 'L2VPN VPLS'),
        (L2VPNEVPN, 'L2VPN EVPN'),
        (LINKSTATE, 'LINK-STATE'),
        (RTFILTER_UNICAST, 'RTFILTER'),
    ]


class BGPStatusChoices(ChoiceSet):
    ACTIVE = 'active'
    PLANNED = 'planned'
    OFFLINE = 'offline'
    FAILED = 'failed'

    CHOICES = [
        (ACTIVE, 'Active'),
        (PLANNED, 'Planned'),
        (OFFLINE, 'Offline'),
        (FAILED, 'Failed'),
    ]
