from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.apps import apps
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel
from utilities.querysets import RestrictedQuerySet

from netbox_routing_protocols.choices import (
    ActionChoices,
    CommunityStatusChoices,
    CommunityTypeChoices,
)
from netbox_routing_protocols.helpers import community as community_helpers

__all__ = (
    'CommunityList',
    'Community',
    'CommunityListEntry',
)


class CommunityList(PrimaryModel):
    """
    A named, ordered list of standard communities (exact values, not regular expressions)
    that route policy entries match routes against. Its entries are evaluated by sequence,
    first match wins.
    """

    name = models.CharField(
        verbose_name=_('List'),
        max_length=100,
    )
    # Vendors keep a list per kind of community: it only accepts communities of its type
    type = models.CharField(
        verbose_name=_('Type'),
        max_length=20,
        choices=CommunityTypeChoices,
        default=CommunityTypeChoices.TYPE_STANDARD,
        help_text=_('The kind of communities the list holds'),
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='community_lists',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Community List')
        verbose_name_plural = 'Community Lists'
        ordering = ['name', 'pk']
        constraints = (
            models.UniqueConstraint(
                Lower('name'),
                name='%(app_label)s_%(class)s_unique_name',
                violation_error_message='Name must be unique.',
            ),
        )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('plugins:netbox_routing_protocols:communitylist', args=[self.pk])

    def get_type_color(self):
        return CommunityTypeChoices.colors.get(self.type)

    def clean(self):
        super().clean()
        if self.pk:
            others = self.communitylistentries.exclude(community__type=self.type)
            if others.exists():
                raise ValidationError(
                    {
                        'type': _(
                            'The list has entries of other types (%(count)s): remove them '
                            'or move them before changing the type.'
                        )
                        % {'count': others.count()}
                    }
                )


# How many route policy entries are named in the error of a delete
MAX_REPORTED = 5


def protect_communities_in_use(communities):
    """
    Refuse to delete communities matched by route policy entries: the many to many would
    drop the link silently and change what the policy matches (the entries of a community
    list are protected by their foreign key). It is checked here and not in a pre_delete
    signal because raising inside the delete would leave the transaction unusable.
    """
    RoutePolicyEntry = apps.get_model('netbox_routing_protocols', 'RoutePolicyEntry')
    entries = RoutePolicyEntry.objects.filter(
        match_community__in=communities
    ).select_related('route_policy')
    shown = list(entries.distinct()[:MAX_REPORTED])
    if shown:
        raise models.ProtectedError(
            'Cannot delete the community: it is matched by route policy entries.',
            set(shown),
        )


class CommunityQuerySet(RestrictedQuerySet):
    def delete(self):
        protect_communities_in_use(self)
        return super().delete()


class Community(PrimaryModel):
    name = models.CharField(
        verbose_name=_('Name'),
        max_length=100,
        blank=True,
    )
    community = models.CharField(
        verbose_name=_('Community'),
        max_length=255,
        help_text=community_helpers.FORMATS_HELP,
    )
    # Derived from the value (standard, extended or large), never edited
    type = models.CharField(
        max_length=20,
        choices=CommunityTypeChoices,
        default=CommunityTypeChoices.TYPE_STANDARD,
        editable=False,
    )

    status = models.CharField(
        max_length=50,
        choices=CommunityStatusChoices,
        default=CommunityStatusChoices.STATUS_ACTIVE,
    )
    role = models.ForeignKey(
        verbose_name=_('Role'),
        to='ipam.Role',
        on_delete=models.SET_NULL,
        related_name='communities',
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='communities',
        null=True,
        blank=True,
    )

    objects = CommunityQuerySet.as_manager()

    class Meta:
        verbose_name = _('Community')
        verbose_name_plural = 'Communities'
        ordering = ['community']
        constraints = [
            models.UniqueConstraint(
                fields=('community',),
                name='%(app_label)s_%(class)s_community',
            ),
        ]

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.community})'
        return f'{self.community}'

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('plugins:netbox_routing_protocols:community', args=[self.pk])

    def get_status_color(self):
        return CommunityStatusChoices.colors.get(self.status)

    def get_type_color(self):
        return CommunityTypeChoices.colors.get(self.type)

    @property
    def well_known(self):
        """`NAME (RFC)` when the value is a well-known community, else None"""
        if self.type != CommunityTypeChoices.TYPE_STANDARD:
            return None
        if found := community_helpers.well_known_name(self.community):
            return f'{found[0]} ({found[1]})'
        return None

    def clean(self):
        super().clean()
        # The value is stored in its normal form so 65000:100 and 65000:0100 (or the
        # name no-export and 65535:65281) are the same community
        try:
            self.type, self.community = community_helpers.parse(self.community)
        except ValidationError as e:
            raise ValidationError({'community': e.messages})

    def delete(self, *args, **kwargs):
        protect_communities_in_use([self])
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        try:
            self.type, self.community = community_helpers.parse(self.community)
        except ValidationError:
            pass  # not valid: full_clean reports it, a raw save keeps the text
        super().save(*args, **kwargs)


class CommunityListEntry(PrimaryModel):
    """
    One rule of a standard community list: a permit or deny on a community, in a sequence
    from 1 to 4294967294. Entries are evaluated in that order, first match wins.
    Expanded (regular expression) lists are not modelled.
    """

    community_list = models.ForeignKey(
        to=CommunityList, on_delete=models.CASCADE, related_name='communitylistentries'
    )
    sequence = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4294967294)],
    )
    action = models.CharField(max_length=30, choices=ActionChoices)
    # A community in use cannot be deleted (it would change what the list matches)
    community = models.ForeignKey(
        to=Community,
        related_name='communitylistentries',
        on_delete=models.PROTECT,
    )

    clone_fields = ('community_list', 'action')
    prerequisite_models = (
        'netbox_routing_protocols.CommunityList',
        'netbox_routing_protocols.Community',
    )

    class Meta:
        verbose_name = _('Community List Entry')
        verbose_name_plural = _('Community List Entries')
        ordering = ('community_list', 'sequence')
        constraints = (
            models.UniqueConstraint(
                fields=('community_list', 'sequence'),
                name='%(app_label)s_%(class)s_unique_communitylist_sequence',
                violation_error_message='Community list sequence must be unique.',
            ),
        )

    def clean(self):
        super().clean()
        # (while a form is being validated the list or the community may be missing)
        if hasattr(self, 'community_list') and hasattr(self, 'community'):
            if self.community.type != self.community_list.type:
                raise ValidationError(
                    {
                        'community': _(
                            '%(community)s is a %(kind)s community and the list holds '
                            '%(expected)s communities.'
                        )
                        % {
                            'community': self.community,
                            'kind': self.community.get_type_display().lower(),
                            'expected': self.community_list.get_type_display().lower(),
                        }
                    }
                )

    def __str__(self):
        # The list is missing while the form of a new entry is being validated
        if hasattr(self, 'community_list') and hasattr(self, 'community'):
            return (
                f'{self.community_list}: {self.sequence} {self.action} {self.community}'
            )
        return super().__str__()

    def get_action_color(self):
        return ActionChoices.colors.get(self.action)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse(
            'plugins:netbox_routing_protocols:communitylistentry', args=[self.pk]
        )
