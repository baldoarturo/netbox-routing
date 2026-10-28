__all__ = ('any_prefix_value', 'any_le')


def any_prefix_value(family):
    """The all zeros prefix of an address family, which IPAM cannot hold (no /0)"""
    return '0.0.0.0/0' if family == 4 else '::/0'


def any_le(family):
    """
    The longest prefix length of an address family. With the all zeros prefix, a LE of
    this length matches any prefix.
    """
    return 32 if family == 4 else 128
