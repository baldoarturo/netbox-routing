from utilities.choices import ChoiceSet


class ActionChoices(ChoiceSet):
    PERMIT = 'permit'
    DENY = 'deny'

    CHOICES = [(PERMIT, 'Permit', 'blue'), (DENY, 'Deny', 'red')]


class OriginChoices(ChoiceSet):
    """The ORIGIN attribute of a BGP route (RFC 4271 section 5.1.1)"""

    IGP = 'igp'
    EGP = 'egp'
    INCOMPLETE = 'incomplete'

    CHOICES = [(IGP, 'IGP'), (EGP, 'EGP'), (INCOMPLETE, 'Incomplete')]


class MetricModeChoices(ChoiceSet):
    """How a route policy changes the MED: replace it or move it by an amount"""

    SET = 'set'
    ADD = 'add'
    SUBTRACT = 'subtract'

    CHOICES = [(SET, 'Set'), (ADD, 'Add'), (SUBTRACT, 'Subtract')]


class CommunityModeChoices(ChoiceSet):
    """What a route policy does with the communities of a route"""

    REPLACE = 'replace'
    ADDITIVE = 'additive'

    CHOICES = [(REPLACE, 'Replace'), (ADDITIVE, 'Additive')]


class CommunityStatusChoices(ChoiceSet):
    key = "Community.status"

    STATUS_ACTIVE = 'active'
    STATUS_RESERVED = 'reserved'
    STATUS_DEPRECATED = 'deprecated'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'blue'),
        (STATUS_RESERVED, 'Reserved', 'cyan'),
        (STATUS_DEPRECATED, 'Deprecated', 'red'),
    ]


class CommunityTypeChoices(ChoiceSet):
    key = "Community.type"

    TYPE_STANDARD = 'standard'
    TYPE_EXTENDED = 'extended'
    TYPE_LARGE = 'large'

    CHOICES = [
        (TYPE_STANDARD, 'Standard', 'blue'),
        (TYPE_EXTENDED, 'Extended', 'purple'),
        (TYPE_LARGE, 'Large', 'teal'),
    ]
