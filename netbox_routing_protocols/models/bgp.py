from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel
from netbox_routing_protocols.choices.bgp import *

__all__ = (
    'BGPInstance',
    'BGPAddressFamily',
    'BGPPeerGroup',
    'BGPPeer',
    'BGPPeerAddressFamily',
    'BFDProfile',
)

# Prefix list family (4 or 6) accepted by each address family. Families that do not
# carry IP prefixes (EVPN, VPLS, link-state, ...) do not take prefix lists.
PREFIX_LIST_FAMILY = {
    BGPAddressFamilyChoices.IPV4_UNICAST: 4,
    BGPAddressFamilyChoices.IPV4_MULTICAST: 4,
    BGPAddressFamilyChoices.IPV4_FLOWSPEC: 4,
    BGPAddressFamilyChoices.VPNV4_UNICAST: 4,
    BGPAddressFamilyChoices.VPNV4_MULTICAST: 4,
    BGPAddressFamilyChoices.VPNV4_FLOWSPEC: 4,
    BGPAddressFamilyChoices.IPV6_UNICAST: 6,
    BGPAddressFamilyChoices.IPV6_MULTICAST: 6,
    BGPAddressFamilyChoices.IPV6_FLOWSPEC: 6,
    BGPAddressFamilyChoices.VPNV6_UNICAST: 6,
    BGPAddressFamilyChoices.VPNV6_MULTICAST: 6,
    BGPAddressFamilyChoices.VPNV6_FLOWSPEC: 6,
}


class BGPPeerConfigMixin(models.Model):
    """Session options shared by a peer and a peer group. A peer left empty
    inherits the value of its group (RFC 4271)."""

    remote_as = models.ForeignKey(
        verbose_name=_('Remote AS'),
        to='ipam.ASN',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    local_as = models.ForeignKey(
        verbose_name=_('Local AS'),
        to='ipam.ASN',
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    enabled = models.BooleanField(verbose_name=_('Enabled'), blank=True, null=True)
    bfd = models.ForeignKey(
        verbose_name=_('BFD Profile'),
        to='netbox_routing_protocols.BFDProfile',
        on_delete=models.PROTECT,
        related_name='%(class)ss',
        blank=True,
        null=True,
    )
    ttl = models.PositiveSmallIntegerField(
        verbose_name=_('TTL'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(255)],
    )
    password = models.CharField(
        verbose_name=_('Password'), max_length=255, blank=True, null=True
    )
    keepalive = models.PositiveIntegerField(
        verbose_name=_('Keepalive Time'),
        blank=True,
        null=True,
        validators=[MaxValueValidator(21845)],
        help_text=_('Seconds. RFC 4271 suggests a third of the hold time'),
    )
    hold_time = models.PositiveIntegerField(
        verbose_name=_('Hold Time'),
        blank=True,
        null=True,
        validators=[MaxValueValidator(65535)],
        help_text=_('Seconds. Zero (no keepalives) or at least 3 (RFC 4271)'),
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        errors = {}
        if self.hold_time is not None and self.hold_time in (1, 2):
            errors['hold_time'] = _(
                'The hold time must be zero or at least 3 seconds (RFC 4271).'
            )
        if self.keepalive is not None and self.hold_time is not None:
            if self.hold_time == 0:
                errors['keepalive'] = _(
                    'A hold time of zero disables the keepalives: do not set a keepalive time.'
                )
            elif self.keepalive * 3 > self.hold_time:
                errors['keepalive'] = _(
                    'The keepalive time must not be more than a third of the hold time.'
                )
        if errors:
            raise ValidationError(errors)


class BGPInstance(PrimaryModel):
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    device = models.ForeignKey(
        verbose_name=_('Device'),
        to='dcim.Device',
        on_delete=models.PROTECT,
        related_name='bgp_instances',
    )
    vrf = models.ForeignKey(
        verbose_name=_('VRF'),
        to='ipam.VRF',
        on_delete=models.PROTECT,
        related_name='bgp_instances',
        blank=True,
        null=True,
    )
    asn = models.ForeignKey(
        verbose_name=_('ASN'),
        to='ipam.ASN',
        on_delete=models.PROTECT,
        related_name='bgp_instances',
    )
    router_id = models.GenericIPAddressField(
        verbose_name=_('Router ID'),
        protocol='IPv4',
        blank=True,
        null=True,
        help_text=_(
            'BGP identifier, a 32-bit value written as an IPv4 address (RFC 6286)'
        ),
    )
    asdot = models.BooleanField(
        verbose_name=_('AS Dot Notation'),
        blank=True,
        null=True,
        help_text=_('Write four-octet ASNs as high.low (RFC 5396)'),
    )
    graceful_restart = models.BooleanField(
        verbose_name=_('Graceful Restart'),
        blank=True,
        null=True,
        help_text=_('RFC 4724'),
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_instances',
        blank=True,
        null=True,
    )

    clone_fields = ('device', 'vrf', 'asn', 'tenant', 'asdot', 'graceful_restart')
    prerequisite_models = (
        'dcim.Device',
        'ipam.ASN',
    )

    class Meta:
        verbose_name = 'BGP Instance'
        verbose_name_plural = 'BGP Instances'
        ordering = ('device', 'vrf', 'name')
        constraints = [
            models.UniqueConstraint(
                fields=('device', 'vrf'),
                name='%(app_label)s_%(class)s_unique_device_vrf',
                nulls_distinct=False,
                violation_error_message=_(
                    'The device already has a BGP instance in this VRF.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:bgpinstance', args=[self.pk])

    def clean(self):
        super().clean()
        if self.router_id == '0.0.0.0':
            raise ValidationError(
                {'router_id': _('The router ID cannot be 0.0.0.0 (RFC 6286).')}
            )


class BGPAddressFamily(PrimaryModel):
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.BGPInstance',
        on_delete=models.PROTECT,
        related_name='address_families',
    )
    address_family = models.CharField(
        verbose_name=_('Address Family'), max_length=50, choices=BGPAddressFamilyChoices
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_address_families',
        blank=True,
        null=True,
    )
    maximum_paths = models.PositiveSmallIntegerField(
        verbose_name=_('Maximum Paths'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_('Equal-cost paths installed (multipath)'),
    )
    default_metric = models.PositiveBigIntegerField(
        verbose_name=_('Default Metric'),
        blank=True,
        null=True,
        validators=[MaxValueValidator(4294967295)],
        help_text=_('MED given to redistributed routes (RFC 4271)'),
    )
    default_originate = models.BooleanField(
        verbose_name=_('Default Originate'), blank=True, null=True
    )
    auto_summary = models.BooleanField(
        verbose_name=_('Auto Summary'), blank=True, null=True
    )
    distance_ebgp = models.PositiveSmallIntegerField(
        verbose_name=_('eBGP Distance'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(255)],
    )
    distance_ibgp = models.PositiveSmallIntegerField(
        verbose_name=_('iBGP Distance'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(255)],
    )
    additional_paths_send = models.BooleanField(
        verbose_name=_('Additional Paths (send)'),
        blank=True,
        null=True,
        help_text=_('RFC 7911'),
    )
    additional_paths_receive = models.BooleanField(
        verbose_name=_('Additional Paths (receive)'),
        blank=True,
        null=True,
        help_text=_('RFC 7911'),
    )
    additional_paths_install = models.BooleanField(
        verbose_name=_('Additional Paths (install)'), blank=True, null=True
    )

    clone_fields = ('instance', 'address_family')
    prerequisite_models = ('netbox_routing_protocols.BGPInstance',)

    class Meta:
        verbose_name = 'BGP Address Family'
        verbose_name_plural = 'BGP Address Families'
        ordering = ('instance', 'address_family')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'address_family'),
                name='%(app_label)s_%(class)s_instance_address_family',
                violation_error_message=_(
                    'The instance already has this address family.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.instance} ({self.get_address_family_display()})'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:bgpaddressfamily', args=[self.pk]
        )


class BGPPeerGroup(BGPPeerConfigMixin, PrimaryModel):
    """A group of neighbors that share their configuration (a peer group)."""

    name = models.CharField(verbose_name=_('Name'), max_length=100)
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.BGPInstance',
        on_delete=models.PROTECT,
        related_name='peer_groups',
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_peer_groups',
        blank=True,
        null=True,
    )

    clone_fields = (
        'instance',
        'remote_as',
        'local_as',
        'enabled',
        'bfd',
        'ttl',
        'keepalive',
        'hold_time',
        'tenant',
    )
    prerequisite_models = ('netbox_routing_protocols.BGPInstance',)

    class Meta:
        verbose_name = 'BGP Peer Group'
        verbose_name_plural = 'BGP Peer Groups'
        ordering = ('instance', 'name')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'name'),
                name='%(app_label)s_%(class)s_instance_name',
                violation_error_message=_(
                    'The instance already has a peer group with this name.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:bgppeergroup', args=[self.pk])


class BGPPeer(BGPPeerConfigMixin, PrimaryModel):
    name = models.CharField(
        verbose_name=_('Name'), max_length=100, blank=True, null=True
    )
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.BGPInstance',
        on_delete=models.PROTECT,
        related_name='peers',
    )
    peer = models.ForeignKey(
        verbose_name=_('Peer Address'),
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        related_name='remote_peers',
    )
    source = models.ForeignKey(
        verbose_name=_('Source Address'),
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        related_name='source_peers',
        blank=True,
        null=True,
    )
    peer_group = models.ForeignKey(
        verbose_name=_('Peer Group'),
        to='netbox_routing_protocols.BGPPeerGroup',
        on_delete=models.PROTECT,
        related_name='peers',
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name=_('Status'),
        max_length=10,
        choices=BGPStatusChoices,
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_peers',
        blank=True,
        null=True,
    )

    clone_fields = (
        'instance',
        'peer_group',
        'remote_as',
        'local_as',
        'enabled',
        'bfd',
        'ttl',
        'keepalive',
        'hold_time',
        'tenant',
    )
    prerequisite_models = ('netbox_routing_protocols.BGPInstance',)

    class Meta:
        verbose_name = 'BGP Peer'
        verbose_name_plural = 'BGP Peers'
        ordering = ('instance', 'peer')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'peer'),
                name='%(app_label)s_%(class)s_instance_peer',
                violation_error_message=_(
                    'The instance already has a peer with this address '
                    '(RFC 4271: one session per neighbor address).'
                ),
            ),
        ]

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.peer})'
        return f'{self.peer}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:bgppeer', args=[self.pk])

    def effective(self, field):
        """The value of a session option: the peer's own, else its group's."""
        value = getattr(self, field)
        if value is None and self.peer_group_id:
            value = getattr(self.peer_group, field)
        return value

    @property
    def is_ibgp(self):
        """True when the neighbor is in the same AS (iBGP), None when unknown."""
        remote_as = self.effective('remote_as')
        if remote_as is None:
            return None
        local_as = self.effective('local_as') or self.instance.asn
        return remote_as.asn == local_as.asn

    def clean(self):
        super().clean()
        if not self.instance_id:
            return
        errors = {}
        if self.peer_group_id and self.peer_group.instance_id != self.instance_id:
            errors['peer_group'] = _('The peer group belongs to another BGP instance.')
        elif self.effective('remote_as') is None:
            errors['remote_as'] = _(
                'A remote AS is required, on the peer or on its peer group.'
            )
        for field in ('peer', 'source'):
            address = getattr(self, f'{field}_id') and getattr(self, field)
            if address and address.vrf_id != self.instance.vrf_id:
                errors[field] = _('The address must be in the VRF of the BGP instance.')
        if self.source_id:
            interface = self.source.assigned_object
            device = getattr(interface, 'device', None)
            if device is not None and device.pk != self.instance.device_id:
                errors['source'] = _(
                    'The source address is on another device than the BGP instance.'
                )
        if errors:
            raise ValidationError(errors)


class BGPPeerAddressFamily(PrimaryModel):
    """What a neighbor (or a peer group) exchanges in an address family."""

    peer = models.ForeignKey(
        verbose_name=_('Peer'),
        to='netbox_routing_protocols.BGPPeer',
        on_delete=models.CASCADE,
        related_name='address_families',
        blank=True,
        null=True,
    )
    peer_group = models.ForeignKey(
        verbose_name=_('Peer Group'),
        to='netbox_routing_protocols.BGPPeerGroup',
        on_delete=models.CASCADE,
        related_name='address_families',
        blank=True,
        null=True,
    )
    address_family = models.ForeignKey(
        verbose_name=_('Address Family'),
        to='netbox_routing_protocols.BGPAddressFamily',
        on_delete=models.PROTECT,
        related_name='peer_address_families',
    )
    enabled = models.BooleanField(verbose_name=_('Enabled'), blank=True, null=True)
    prefixlist_out = models.ForeignKey(
        verbose_name=_('Outbound Prefix List'),
        to='netbox_routing_protocols.PrefixList',
        on_delete=models.SET_NULL,
        related_name='peer_address_families_out',
        blank=True,
        null=True,
    )
    prefixlist_in = models.ForeignKey(
        verbose_name=_('Inbound Prefix List'),
        to='netbox_routing_protocols.PrefixList',
        on_delete=models.SET_NULL,
        related_name='peer_address_families_in',
        blank=True,
        null=True,
    )
    routepolicy_out = models.ForeignKey(
        verbose_name=_('Outbound Route Policy'),
        to='netbox_routing_protocols.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='peer_address_families_out',
        blank=True,
        null=True,
    )
    routepolicy_in = models.ForeignKey(
        verbose_name=_('Inbound Route Policy'),
        to='netbox_routing_protocols.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='peer_address_families_in',
        blank=True,
        null=True,
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_peer_address_families',
        blank=True,
        null=True,
    )

    clone_fields = (
        'peer',
        'peer_group',
        'enabled',
        'prefixlist_out',
        'prefixlist_in',
        'routepolicy_out',
        'routepolicy_in',
        'tenant',
    )
    prerequisite_models = (
        'netbox_routing_protocols.BGPInstance',
        'netbox_routing_protocols.BGPAddressFamily',
    )

    class Meta:
        verbose_name = 'BGP Peer Address Family'
        verbose_name_plural = 'BGP Peer Address Families'
        ordering = ('peer', 'peer_group', 'address_family', 'pk')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_peer_xor_group',
                condition=(
                    models.Q(peer__isnull=False, peer_group__isnull=True)
                    | models.Q(peer__isnull=True, peer_group__isnull=False)
                ),
                violation_error_message=_(
                    'Assign it to a peer or to a peer group, not both.'
                ),
            ),
            models.UniqueConstraint(
                fields=('peer', 'address_family'),
                name='%(app_label)s_%(class)s_peer_address_family',
                violation_error_message=_('The peer already has this address family.'),
            ),
            models.UniqueConstraint(
                fields=('peer_group', 'address_family'),
                name='%(app_label)s_%(class)s_peer_group_address_family',
                violation_error_message=_(
                    'The peer group already has this address family.'
                ),
            ),
        ]

    @property
    def assigned_object(self):
        return self.peer or self.peer_group

    def __str__(self):
        return f'{self.assigned_object} ({self.address_family.get_address_family_display()})'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:bgppeeraddressfamily', args=[self.pk]
        )

    def clean(self):
        super().clean()
        if not self.address_family_id:
            return
        errors = {}
        owner = self.assigned_object
        if owner is not None and owner.instance_id != self.address_family.instance_id:
            errors['address_family'] = _(
                'The address family belongs to another BGP instance.'
            )
        family = PREFIX_LIST_FAMILY.get(self.address_family.address_family)
        for field in ('prefixlist_in', 'prefixlist_out'):
            prefix_list = getattr(self, f'{field}_id') and getattr(self, field)
            if prefix_list is None:
                continue
            if family is None:
                errors[field] = _(
                    'This address family does not carry IP prefixes: no prefix list.'
                )
            elif prefix_list.family != family:
                errors[field] = _(
                    'The prefix list is IPv%(list)s and the address family is '
                    'IPv%(family)s.'
                ) % {'list': prefix_list.family, 'family': family}
        if errors:
            raise ValidationError(errors)


class BFDProfile(PrimaryModel):
    name = models.CharField(verbose_name=_('Name'), max_length=100)
    min_tx_int = models.PositiveIntegerField(
        verbose_name=_('Min TX Interval'),
        validators=[MinValueValidator(60), MaxValueValidator(60000)],
    )
    min_rx_int = models.PositiveIntegerField(
        verbose_name=_('Min RX Interval'),
        validators=[MinValueValidator(60), MaxValueValidator(60000)],
    )
    multiplier = models.PositiveSmallIntegerField(
        verbose_name=_('Multiplier'),
        validators=[MinValueValidator(1), MaxValueValidator(255)],
    )
    hold = models.PositiveIntegerField(
        verbose_name=_('Hold Time'),
        blank=True,
        null=True,
        validators=[MinValueValidator(60), MaxValueValidator(60000)],
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bfd_profiles',
        blank=True,
        null=True,
    )

    clone_fields = ('min_tx_int', 'min_rx_int', 'multiplier', 'hold', 'tenant')

    class Meta:
        verbose_name = 'BFD Profile'
        verbose_name_plural = 'BFD Profiles'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='%(app_label)s_%(class)s_name',
            ),
        ]

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:bfdprofile', args=[self.pk])
