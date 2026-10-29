import netaddr
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from django.db import models
from django.core.exceptions import ValidationError

from ipam.choices import IPAddressFamilyChoices
from netbox.models import PrimaryModel

from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.helpers.aspath import validate_pattern

__all__ = (
    'ASPath',
    'ASPathEntry',
    'PrefixList',
    'PrefixListEntry',
    'RoutePolicy',
    'RoutePolicyEntry',
)


class PermitDenyChoiceMixin:
    def get_action_color(self):
        return ActionChoices.colors.get(self.action)


class ASPath(PrimaryModel):
    """
    A named, ordered list of AS_PATH patterns (RFC 4271 section 5.1.2) that route policy
    entries match routes against. Its entries are evaluated by sequence, first match wins.
    """

    name = models.CharField(max_length=100)

    clone_fields = ()
    prerequisite_models = ()

    class Meta:
        verbose_name = _('AS Path')
        verbose_name_plural = _('AS Paths')
        ordering = [
            'name',
            'pk',
        ]
        constraints = (
            models.UniqueConstraint(
                Lower('name'),
                name='%(app_label)s_%(class)s_unique_name',
                violation_error_message="Name must be unique.",
            ),
        )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:aspath', args=[self.pk])


class ASPathEntry(PermitDenyChoiceMixin, PrimaryModel):
    """
    One rule of an AS-path: a permit or deny on a regular expression, in a
    sequence from 1 to 4294967294. The pattern is validated, not evaluated; see
    helpers/aspath.validate_pattern. A pattern cannot be repeated in the same AS-path (the
    second entry would never be reached): the constraint is checked by full_clean() too.
    """

    aspath = models.ForeignKey(
        to=ASPath,
        on_delete=models.CASCADE,
        related_name='aspath_entries',
        verbose_name=_('AS-Path'),
    )
    sequence = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4294967294)],
    )
    action = models.CharField(max_length=6, choices=ActionChoices)
    pattern = models.CharField(
        max_length=200,
    )

    clone_fields = (
        'aspath',
        'action',
    )
    prerequisite_models = ('netbox_routing_protocols.ASPath',)

    class Meta:
        verbose_name = _('AS Path Entry')
        verbose_name_plural = _('AS Path Entries')
        ordering = ['aspath', 'sequence']
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'aspath',
                    'sequence',
                ),
                name='%(app_label)s_%(class)s_unique_aspath_sequence',
                violation_error_message="AS-Path sequence must be unique.",
            ),
            models.UniqueConstraint(
                fields=(
                    'aspath',
                    'pattern',
                ),
                name='%(app_label)s_%(class)s_unique_aspath_pattern',
                violation_error_message="This AS-Path already has an entry with this pattern.",
            ),
        )

    def __str__(self):
        # Workaround for bug with nulled aspath entry (the required field is missing
        # while the form of a new entry is being validated).
        if hasattr(self, 'aspath'):
            return f'{self.aspath.name} {self.action} {self.sequence}'
        return super().__str__()

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:aspathentry', args=[self.pk])

    def clean(self):
        super().clean()
        if self.pattern is not None:
            if errors := validate_pattern(self.pattern):
                raise ValidationError({'pattern': errors})


class PrefixList(PrimaryModel):
    """
    An ordered list of prefix rules of one address family, which cannot change once set.
    """

    name = models.CharField(max_length=100)
    family = models.PositiveSmallIntegerField(choices=IPAddressFamilyChoices, default=4)

    clone_fields = ()
    prerequisite_models = ()

    class Meta:
        verbose_name = _('Prefix List')
        verbose_name_plural = _('Prefix Lists')
        ordering = [
            'name',
            'pk',
        ]
        constraints = (
            models.UniqueConstraint(
                Lower('name'),
                name='%(app_label)s_%(class)s_unique_name',
                violation_error_message="Name must be unique.",
            ),
        )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:prefixlist', args=[self.pk])

    def clean(self):
        super().clean()
        # The family is fixed when the list is created: its entries are of that family
        if self.pk:
            current = (
                PrefixList.objects.filter(pk=self.pk)
                .values_list('family', flat=True)
                .first()
            )
            if current is not None and current != self.family:
                raise ValidationError(
                    {'family': _('The address family cannot be changed once defined.')}
                )


class PrefixListEntry(PermitDenyChoiceMixin, PrimaryModel):
    """
    A rule of a prefix list: permit or deny the prefixes inside an IPAM prefix (or Any, the
    all zeros prefix IPAM cannot hold) whose length is within ge..le, both inclusive.
    Lists are evaluated by sequence, first match wins; see helpers/prefix_list.match_range.
    """

    prefix_list = models.ForeignKey(
        to=PrefixList,
        on_delete=models.CASCADE,
        related_name='prefix_list_entries',
        verbose_name='Prefix List',
    )
    prefix = models.ForeignKey(
        to='ipam.Prefix',
        on_delete=models.PROTECT,
        related_name='prefix_list_entries',
        verbose_name=_('Prefix'),
        blank=True,
        null=True,
    )
    any_prefix = models.BooleanField(
        verbose_name=_('Any'),
        default=False,
        help_text=_(
            'The all zeros prefix of the address family of the list (0.0.0.0/0 or '
            '::/0), which IPAM cannot hold. With LE set to the longest length it '
            'matches any prefix. Leave the prefix empty.'
        ),
    )
    sequence = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4294967294)],
    )
    action = models.CharField(max_length=6, choices=ActionChoices)
    ge = models.PositiveSmallIntegerField(
        verbose_name='GE',
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(128)],
    )
    le = models.PositiveSmallIntegerField(
        verbose_name='LE',
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(128)],
    )

    clone_fields = (
        'prefix_list',
        'action',
    )
    prerequisite_models = ('netbox_routing_protocols.PrefixList',)

    class Meta:
        verbose_name = _('Prefix List Entry')
        verbose_name_plural = _('Prefix List Entries')
        ordering = ['prefix_list', 'sequence']
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'prefix_list',
                    'sequence',
                ),
                name='%(app_label)s_%(class)s_unique_prefixlist_sequence',
                violation_error_message="Prefix List sequence must be unique.",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(any_prefix=True, prefix__isnull=True)
                    | models.Q(any_prefix=False, prefix__isnull=False)
                ),
                name='%(app_label)s_%(class)s_prefix_or_any',
                violation_error_message='Set a prefix, or Any without a prefix.',
            ),
        )

    def __str__(self):
        return f'{self.prefix_list.name} {self.action} {self.sequence}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:prefixlistentry', args=[self.pk]
        )

    def clean(self):
        super().clean()
        if not hasattr(self, 'prefix_list'):
            return  # the required field reports its own error
        family = self.prefix_list.family

        if self.any_prefix:
            if self.prefix_id is not None:
                raise ValidationError(
                    {'prefix': 'An entry that matches Any has no prefix.'}
                )
            length = 0
        else:
            if self.prefix_id is None:
                raise ValidationError(
                    {'prefix': 'A prefix is required, or select Any.'}
                )
            prefix = self.prefix.prefix
            if isinstance(prefix, str):
                prefix = netaddr.IPNetwork(prefix)
            if prefix.version != family:
                raise ValidationError(
                    f'{prefix} is an IPv{prefix.version} prefix and cannot be added '
                    f'to the IPv{family} prefix list {self.prefix_list}.'
                )
            length = prefix.prefixlen

        boundary = 32 if family == 4 else 128
        if self.le is not None and self.le > boundary:
            raise ValidationError(
                {
                    'le': f'LE value cannot be greater than {boundary} for an IPv{family} list'
                }
            )
        if self.ge is not None and self.ge > boundary:
            raise ValidationError(
                {
                    'ge': f'GE value cannot be greater than {boundary} for an IPv{family} list'
                }
            )
        if self.ge is not None and self.le is not None and self.ge > self.le:
            raise ValidationError(
                {
                    'ge': 'GE cannot be greater than LE',
                    'le': 'LE cannot be less than GE',
                }
            )
        # ge is "greater than or equal" and le "less than or equal" to the length of
        # the matched prefix: both accept a value equal to the prefix length
        if self.ge is not None and self.ge < length:
            raise ValidationError({'ge': 'GE cannot be less than the prefix length'})
        if self.le is not None and self.le < length:
            raise ValidationError({'le': 'LE cannot be less than the prefix length'})


class RoutePolicy(PrimaryModel):
    name = models.CharField(max_length=100)

    clone_fields = ()
    prerequisite_models = ()

    class Meta:
        verbose_name = _('Route Policy')
        verbose_name_plural = _('Route Policies')
        ordering = [
            'name',
            'pk',
        ]
        constraints = (
            models.UniqueConstraint(
                Lower('name'),
                name='%(app_label)s_%(class)s_unique_name',
                violation_error_message="Name must be unique.",
            ),
        )

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:routepolicy', kwargs={'pk': self.pk}
        )


class RoutePolicyEntry(PermitDenyChoiceMixin, PrimaryModel):
    route_policy = models.ForeignKey(
        to=RoutePolicy,
        on_delete=models.CASCADE,
        related_name='route_policy_entries',
        verbose_name='Route Policy',
    )
    action = models.CharField(max_length=6, choices=ActionChoices)
    sequence = models.PositiveSmallIntegerField()
    flow_control = models.PositiveSmallIntegerField(
        verbose_name=_('Flow Control (Continue)'), null=True, blank=True
    )
    match_community_list = models.ManyToManyField(
        to=CommunityList,
        blank=True,
        related_name='route_policy_entries',
    )
    match_community = models.ManyToManyField(
        to=Community,
        blank=True,
        related_name='route_policy_entries',
    )
    match_aspath = models.ManyToManyField(
        to=ASPath,
        blank=True,
        related_name='route_policy_entries',
    )
    match_prefix_list = models.ManyToManyField(
        to=PrefixList,
        blank=True,
        related_name='route_policy_entries',
    )
    match = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Match parameters'),
        help_text=_("JSON blob of options to match "),
    )
    set = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Set parameters'),
        help_text=_("JSON blob of options to set "),
    )

    clone_fields = (
        'route_policy',
        'action',
    )
    prerequisite_models = ('netbox_routing_protocols.RoutePolicy',)

    class Meta:
        verbose_name = _('Route Policy Entry')
        verbose_name_plural = _('Route Policy Entries')
        ordering = ['route_policy', 'sequence']
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'route_policy',
                    'sequence',
                ),
                name='%(app_label)s_%(class)s_unique_routepolicy_sequence',
                violation_error_message="Route Policy sequence must be unique.",
            ),
        )

    def __str__(self):
        return f'{self.route_policy.name} {self.action} {self.sequence}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:routepolicyentry', args=[self.pk]
        )
