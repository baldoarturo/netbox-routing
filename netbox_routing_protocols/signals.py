from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from dcim.models import Interface
from ipam.models import Prefix
from utilities.exceptions import AbortRequest

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
