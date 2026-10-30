from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from dcim.models import Interface
from ipam.models import IPAddress, Prefix
from utilities.exceptions import AbortRequest

from netbox_routing_protocols.models import OSPFInterface

__all__ = ('validate_prefix_list_entries', 'validate_isis_interfaces')

# How many invalid entries are named in the error message
MAX_REPORTED = 5


@receiver(pre_save, sender=Prefix)
def validate_prefix_list_entries(sender, instance, raw=False, **kwargs):
    """
    Refuse to save a Prefix when the new value would leave a prefix list entry that uses it
    invalid (a different address family, or ge/le now less than the prefix length).
    AbortRequest is reported as an error by the UI forms and the API.
    """
    if raw or instance.pk is None:
        return

    problems = []
    for entry in instance.prefix_list_entries.select_related('prefix_list'):
        entry.prefix = instance
        try:
            entry.clean()
        except ValidationError as e:
            problems.append(f'{entry} ({"; ".join(e.messages)})')
    if problems:
        shown = ', '.join(problems[:MAX_REPORTED])
        if len(problems) > MAX_REPORTED:
            shown += f' and {len(problems) - MAX_REPORTED} more'
        raise AbortRequest(
            f'Cannot change {instance}: it would make prefix list entries invalid: {shown}.'
        )


@receiver(pre_save, sender=Interface)
def validate_isis_interfaces(sender, instance, raw=False, **kwargs):
    """
    Refuse to move an Interface to another device or VRF while an IS-IS interface uses it
    with an instance that no longer matches (same rule as ISISInterface.clean).
    """
    if raw or instance.pk is None:
        return

    problems = []
    for entry in instance.isis_interfaces.select_related('instance'):
        entry.interface = instance
        try:
            entry.clean()
        except ValidationError as e:
            problems.append(f'{entry} ({"; ".join(e.messages)})')
    if problems:
        raise AbortRequest(
            f'Cannot change {instance}: it would make IS-IS interfaces invalid: '
            f'{", ".join(problems[:MAX_REPORTED])}.'
        )


def _abort_if_invalid(instance, entries, what):
    problems = []
    for entry in entries:
        try:
            entry.clean()
        except ValidationError as e:
            problems.append(f'{entry} ({"; ".join(e.messages)})')
    if problems:
        shown = ', '.join(problems[:MAX_REPORTED])
        if len(problems) > MAX_REPORTED:
            shown += f' and {len(problems) - MAX_REPORTED} more'
        raise AbortRequest(
            f'Cannot change {instance}: it would make {what} invalid: {shown}.'
        )


@receiver(pre_save, sender=Interface)
def validate_ospf_interfaces(sender, instance, raw=False, **kwargs):
    """
    Refuse to move an Interface to another device or VRF while an OSPF interface uses it
    with an instance that no longer matches (same rule as OSPFInterface.clean).
    """
    if raw or instance.pk is None:
        return

    entries = list(
        OSPFInterface.objects.filter(interface=instance).select_related(
            'instance', 'area'
        )
    )
    for entry in entries:
        entry.interface = instance
    _abort_if_invalid(instance, entries, 'OSPF interfaces')


@receiver(pre_save, sender=IPAddress)
def validate_ospf_networks(sender, instance, raw=False, **kwargs):
    """
    Refuse to move or change an IPAddress while an OSPF network uses it and the new value
    would break the network (assigned to another interface, or not an IPv4 address).
    """
    if raw or instance.pk is None:
        return

    entries = list(instance.ospf_networks.select_related('ospf_interface__instance'))
    for entry in entries:
        entry.ip_address = instance
    _abort_if_invalid(instance, entries, 'OSPF networks')
