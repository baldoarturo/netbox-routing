from utilities.choices import ChoiceSet


class OSPFAreaTypeChoices(ChoiceSet):
    STANDARD = 'standard'
    BACKBONE = 'backbone'
    STUB = 'stub'
    TSA = 'tsa'
    NSSA = 'nssa'
    TNSSA = 'tnssa'

    CHOICES = [
        (STANDARD, 'Standard Area'),
        (BACKBONE, 'Backbone Area'),
        (STUB, 'Stub Area'),
        (TSA, 'Totally Stubby Area'),
        (NSSA, 'Not-So-Stubby Area'),
        (TNSSA, 'Totally Not-So-Stubby Area'),
    ]


class OSPFNetworkTypeChoices(ChoiceSet):
    BROADCAST = 'broadcast'
    NON_BROADCAST = 'non_broadcast'
    POINT_TO_POINT = 'point_to_point'
    POINT_TO_MULTIPOINT = 'point_to_multipoint'
    POINT_TO_MULTIPOINT_NON_BROADCAST = 'point_to_multipoint_non_broadcast'
    LOOPBACK = 'loopback'

    CHOICES = [
        (BROADCAST, 'Broadcast'),
        (NON_BROADCAST, 'Non Broadcast'),
        (POINT_TO_POINT, 'Point to Point'),
        (POINT_TO_MULTIPOINT, 'Point to Multipoint'),
        (POINT_TO_MULTIPOINT_NON_BROADCAST, 'Point to Multipoint Non Broadcast'),
        (LOOPBACK, 'Loopback'),
    ]


class OSPFExternalMetricTypeChoices(ChoiceSet):
    TYPE_1 = '1'
    TYPE_2 = '2'

    CHOICES = [
        (TYPE_1, 'Type 1 (E1)'),
        (TYPE_2, 'Type 2 (E2)'),
    ]


class OSPFRedistributionProtocolChoices(ChoiceSet):
    CONNECTED = 'connected'
    STATIC = 'static'
    EIGRP = 'eigrp'
    BGP = 'bgp'
    OSPF = 'ospf'
    ISIS = 'isis'

    CHOICES = [
        (CONNECTED, 'Connected'),
        (STATIC, 'Static'),
        (EIGRP, 'EIGRP'),
        (BGP, 'BGP'),
        (OSPF, 'OSPF'),
        (ISIS, 'IS-IS'),
    ]


class OSPFGracefulRestartChoices(ChoiceSet):
    """RestartSupport values of RFC 3623 appendix B.1."""

    DISABLED = 'disabled'
    PLANNED = 'planned'
    PLANNED_UNPLANNED = 'planned-unplanned'

    CHOICES = [
        (DISABLED, 'Disabled'),
        (PLANNED, 'Planned restarts only'),
        (PLANNED_UNPLANNED, 'Planned and unplanned restarts'),
    ]


class OSPFMessageDigestAlgorithmChoices(ChoiceSet):
    """Cryptographic authentication: MD5 (RFC 2328 D.3), HMAC-SHA (RFC 5709)."""

    MD5 = 'md5'
    HMAC_SHA_1 = 'hmac-sha-1'
    HMAC_SHA_256 = 'hmac-sha-256'
    HMAC_SHA_384 = 'hmac-sha-384'
    HMAC_SHA_512 = 'hmac-sha-512'

    CHOICES = [
        (MD5, 'MD5'),
        (HMAC_SHA_1, 'HMAC-SHA-1'),
        (HMAC_SHA_256, 'HMAC-SHA-256'),
        (HMAC_SHA_384, 'HMAC-SHA-384'),
        (HMAC_SHA_512, 'HMAC-SHA-512'),
    ]


class OSPFAuthenticationChoices(ChoiceSet):
    """
    Authentication types of OSPFv2 (RFC 2328 appendix D): null (0), simple
    password (1) and cryptographic (2), the latter with the key given directly
    (message digest) or through a key chain.
    """

    NULL = 'null'
    SIMPLE = 'simple'
    MESSAGE_DIGEST = 'message-digest'
    KEYCHAIN = 'key-chain'

    CHOICES = [
        (SIMPLE, 'Simple Password'),
        (MESSAGE_DIGEST, 'Message Digest'),
        (KEYCHAIN, 'Key Chain'),
        (NULL, 'Null Authentication'),
    ]


class OSPFRouteTypeChoices(ChoiceSet):
    """Types of OSPF routes: intra/inter-area, AS-external and NSSA external."""

    INTERNAL = 'internal'
    EXTERNAL_1 = 'external-1'
    EXTERNAL_2 = 'external-2'
    NSSA_EXTERNAL_1 = 'nssa-external-1'
    NSSA_EXTERNAL_2 = 'nssa-external-2'

    CHOICES = [
        (INTERNAL, 'Internal'),
        (EXTERNAL_1, 'External Type 1'),
        (EXTERNAL_2, 'External Type 2'),
        (NSSA_EXTERNAL_1, 'NSSA External Type 1'),
        (NSSA_EXTERNAL_2, 'NSSA External Type 2'),
    ]


class OSPFRangeTypeChoices(ChoiceSet):
    """Kinds of address range of an area."""

    SUMMARY = 'summary'
    NSSA_EXTERNAL = 'nssa-external'

    CHOICES = [
        (SUMMARY, 'Summary of intra-area routes'),
        (NSSA_EXTERNAL, 'NSSA external (type 7 to type 5)'),
    ]


class OSPFSegmentIdentifierChoices(ChoiceSet):
    """How the value of a segment identifier is read (V and L flags, RFC 8665)."""

    INDEX = 'index'
    ABSOLUTE = 'absolute'

    CHOICES = [
        (INDEX, 'Index into the SRGB'),
        (ABSOLUTE, 'Absolute label (local)'),
    ]


class OSPFSRAlgorithmChoices(ChoiceSet):
    """SR-Algorithm values defined by RFC 8665."""

    SPF = 0
    STRICT_SPF = 1

    CHOICES = [
        (SPF, 'SPF'),
        (STRICT_SPF, 'Strict SPF'),
    ]


class OSPFFastRerouteChoices(ChoiceSet):
    """IP fast reroute modes: loop-free alternates (RFC 5286) and remote LFA (RFC 7490)."""

    LFA = 'lfa'
    REMOTE_LFA = 'remote-lfa'

    CHOICES = [
        (LFA, 'Loop-Free Alternate (RFC 5286)'),
        (REMOTE_LFA, 'Remote LFA (RFC 7490)'),
    ]
