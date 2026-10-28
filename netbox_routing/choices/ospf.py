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

    CHOICES = [
        (BROADCAST, 'Broadcast'),
        (NON_BROADCAST, 'Non Broadcast'),
        (POINT_TO_POINT, 'Point to Point'),
        (POINT_TO_MULTIPOINT, 'Point to Multipoint'),
        (POINT_TO_MULTIPOINT_NON_BROADCAST, 'Point to Multipoint Non Broadcast'),
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
