import netaddr
from django.contrib.postgres.fields import ArrayField
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
from netbox_routing_protocols.choices import (
    ActionChoices,
    CommunityModeChoices,
    MetricModeChoices,
    OriginChoices,
)
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


# Tag and weight are not BGP path attributes: some vendors have them, others do not
TAG_HELP = _(
    'Not a BGP attribute: only some vendors have it (for example Cisco and FRR)'
)
WEIGHT_HELP = _(
    'Not a BGP attribute (0 to 65535): only some vendors have it (for example Cisco '
    'and FRR), and it never leaves the router'
)

# The settings of an entry, which a deny entry cannot have
SET_FIELDS = (
    'set_local_preference',
    'set_next_hop',
    'set_aspath_prepend',
    'set_community_list',
    'set_community_mode',
    'set_metric',
    'set_metric_mode',
    'set_origin',
    'set_tag',
    'set_weight',
)


class RoutePolicyEntry(PermitDenyChoiceMixin, PrimaryModel):
    route_policy = models.ForeignKey(
        to=RoutePolicy,
        on_delete=models.CASCADE,
        related_name='route_policy_entries',
        verbose_name='Route Policy',
    )
    action = models.CharField(max_length=6, choices=ActionChoices)
    sequence = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4294967294)],
    )
    flow_control = models.PositiveBigIntegerField(
        verbose_name=_('Flow Control (Continue)'),
        null=True,
        blank=True,
        validators=[MaxValueValidator(4294967294)],
    )
    # What the entry matches on. Several conditions are an AND; several objects in one list
    # are an OR, as on the routers
    match_prefix_list = models.ManyToManyField(
        to=PrefixList,
        blank=True,
        related_name='route_policy_entries',
    )
    match_aspath = models.ManyToManyField(
        to=ASPath,
        blank=True,
        related_name='route_policy_entries',
    )
    match_community_list = models.ManyToManyField(
        to=CommunityList,
        blank=True,
        related_name='route_policy_entries',
        help_text=_('Communities and extended communities'),
    )
    match_next_hop = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        related_name='route_policy_entries_match_next_hop',
        blank=True,
        null=True,
        verbose_name=_('Match Next Hop'),
        help_text=_('NEXT_HOP of the route, an IPv4 or IPv6 address of IPAM'),
    )
    match_metric = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        verbose_name=_('Match Metric'),
        help_text=_('MULTI_EXIT_DISC of the route'),
    )
    match_origin = models.CharField(
        max_length=10,
        choices=OriginChoices,
        blank=True,
        verbose_name=_('Match Origin'),
    )
    match_tag = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        verbose_name=_('Match Tag'),
        help_text=TAG_HELP,
    )
    match_weight = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(65535)],
        verbose_name=_('Match Weight'),
        help_text=WEIGHT_HELP,
    )

    # What the entry changes in the routes it permits. A deny entry only denies
    set_local_preference = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        verbose_name=_('Set Local Preference'),
    )
    set_next_hop = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        related_name='route_policy_entries_set_next_hop',
        blank=True,
        null=True,
        verbose_name=_('Set Next Hop'),
        help_text=_('An IPv4 or IPv6 address of IPAM'),
    )
    set_aspath_prepend = ArrayField(
        base_field=models.PositiveBigIntegerField(
            validators=[MaxValueValidator(4294967295)]
        ),
        blank=True,
        default=list,
        verbose_name=_('Set AS-Path Prepend'),
        help_text=_(
            'AS numbers added at the start of the AS_PATH, in this order '
            '(repeat a number to prepend it several times)'
        ),
    )
    set_community_list = models.ForeignKey(
        to=CommunityList,
        on_delete=models.SET_NULL,
        related_name='route_policy_entries_set',
        blank=True,
        null=True,
        verbose_name=_('Set Community List'),
        help_text=_(
            'The communities and extended communities that the permit entries of '
            'the list hold'
        ),
    )
    set_community_mode = models.CharField(
        max_length=10,
        choices=CommunityModeChoices,
        blank=True,
        verbose_name=_('Set Community Mode'),
        help_text=_('Replace the communities of the route or add to them'),
    )
    set_metric = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        verbose_name=_('Set Metric'),
    )
    set_metric_mode = models.CharField(
        max_length=10,
        choices=MetricModeChoices,
        blank=True,
        verbose_name=_('Set Metric Mode'),
        help_text=_(
            'Set the metric to the value, or add it to the metric or subtract it'
        ),
    )
    set_origin = models.CharField(
        max_length=10,
        choices=OriginChoices,
        blank=True,
        verbose_name=_('Set Origin'),
    )
    set_tag = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        verbose_name=_('Set Tag'),
        help_text=TAG_HELP,
    )
    set_weight = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(65535)],
        verbose_name=_('Set Weight'),
        help_text=WEIGHT_HELP,
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

    @property
    def aspath_prepend_text(self):
        """E.g. `65001 65001`"""
        return ' '.join(str(asn) for asn in self.set_aspath_prepend)

    def clean(self):
        super().clean()
        errors = {}
        if self.action == ActionChoices.DENY:
            # A deny entry only denies: nothing is set and nothing continues
            for name in (*SET_FIELDS, 'flow_control'):
                value = getattr(self, name)
                if value not in (None, '', []):
                    errors[name] = _(
                        'A deny entry only denies: it cannot set or continue.'
                    )
        else:
            if self.set_community_list and not self.set_community_mode:
                errors['set_community_mode'] = _('Choose replace or additive.')
            if self.set_metric is not None and not self.set_metric_mode:
                self.set_metric_mode = MetricModeChoices.SET
            if self.set_metric is None and self.set_metric_mode:
                errors['set_metric'] = _('The metric mode needs a metric.')
        if errors:
            raise ValidationError(errors)
