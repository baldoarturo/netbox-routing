from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from ipam.models import Prefix
from utilities.exceptions import AbortRequest

from netbox_routing_protocols.models.objects import CustomPrefix, PrefixListEntry

__all__ = ('validate_prefix_list_entries',)

# How many invalid entries are named in the error message
MAX_REPORTED = 5


@receiver(pre_save, sender=Prefix)
@receiver(pre_save, sender=CustomPrefix)
def validate_prefix_list_entries(sender, instance, raw=False, **kwargs):
    """
    Refuse to save a Prefix or CustomPrefix when the new value would leave a prefix list
    entry that uses it invalid (a different address family, or ge/le no longer greater than
    the prefix length). AbortRequest is reported as an error by the UI forms and the API.
    """
    if raw or instance.pk is None:
        return
    entries = PrefixListEntry.objects.filter(
        assigned_prefix_type=ContentType.objects.get_for_model(sender),
        assigned_prefix_id=instance.pk,
    ).select_related('prefix_list')

    problems = []
    for entry in entries:
        entry.assigned_prefix = instance
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
