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
