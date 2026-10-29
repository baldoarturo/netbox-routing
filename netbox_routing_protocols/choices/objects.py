from utilities.choices import ChoiceSet


class ActionChoices(ChoiceSet):
    PERMIT = 'permit'
    DENY = 'deny'

    CHOICES = [(PERMIT, 'Permit', 'blue'), (DENY, 'Deny', 'red')]


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
