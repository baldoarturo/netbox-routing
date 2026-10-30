import hashlib
import ipaddress

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel
from netbox_routing_protocols.choices.ospf import OSPFRouteTypeChoices
from netbox_routing_protocols.models.policy import RoutePolicyMixin
from netbox_routing_protocols.choices.bgp import *

__all__ = (
    'BGPInstance',
    'BGPAddressFamily',
    'BGPPeerGroup',
    'BGPListenRange',
    'BGPRedistribution',
    'BGPPeer',
    'BGPPeerAddressFamily',
    'BFDProfile',
)

_UNSET = object()

# RFC 2385: implementations accept keys of at least 80 characters
BGP_PASSPHRASE_MAX_LENGTH = 80

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


class BGPPeerConfigMixin(RoutePolicyMixin, models.Model):
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
    ebgp_multihop = models.PositiveSmallIntegerField(
        verbose_name=_('eBGP Multihop'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        help_text=_('Maximum hops to a neighbor that is not directly connected'),
    )
    ttl_security_hops = models.PositiveSmallIntegerField(
        verbose_name=_('TTL Security Hops'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(254)],
        help_text=_(
            'Generalized TTL Security Mechanism (RFC 5082): the neighbor is at most '
            'this many hops away, packets with a lower TTL are dropped'
        ),
    )
    passive = models.BooleanField(
        verbose_name=_('Passive'),
        blank=True,
        null=True,
        help_text=_('Wait for the neighbor to open the TCP connection (RFC 4271)'),
    )
    passphrase = models.CharField(
        verbose_name=_('Passphrase'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_(
            'The TCP MD5 key (RFC 2385), stored as plain text, up to 80 characters'
        ),
    )
    show_md5 = models.BooleanField(
        verbose_name=_('MD5 Digest'),
        help_text=_('Also show the MD5 digest of the key'),
        default=False,
    )
    route_reflector_client = models.BooleanField(
        verbose_name=_('Route Reflector Client'),
        blank=True,
        null=True,
        help_text=_('The neighbor is a client of this route reflector (RFC 4456)'),
    )
    extended_nexthop = models.BooleanField(
        verbose_name=_('Extended Next Hop'),
        blank=True,
        null=True,
        help_text=_('Advertise IPv4 prefixes with an IPv6 next hop (RFC 5549)'),
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

    def get_passphrase_md5(self):
        """The MD5 digest (hex) of the key, or None when there is no key."""
        if not self.passphrase:
            return None
        return hashlib.md5(self.passphrase.encode()).hexdigest()

    @property
    def md5_digest(self):
        """The MD5 digest of the key, only when it is set to be shown."""
        return self.get_passphrase_md5() if self.show_md5 else None

    def clean(self):
        super().clean()
        errors = {}
        if self.passphrase and len(self.passphrase) > BGP_PASSPHRASE_MAX_LENGTH:
            errors['passphrase'] = _(
                'The key is longer than %(max)s characters (RFC 2385).'
            ) % {'max': BGP_PASSPHRASE_MAX_LENGTH}
        if self.show_md5 and not self.passphrase:
            errors['show_md5'] = _('There is no key to show the MD5 digest of.')
        if self.ebgp_multihop is not None and self.ttl_security_hops is not None:
            errors['ttl_security_hops'] = _(
                'TTL security (RFC 5082) and eBGP multihop cannot be used together: '
                'the first expects the neighbor close, the second far.'
            )
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


class BGPInstance(RoutePolicyMixin, PrimaryModel):
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
    cluster_id = models.CharField(
        verbose_name=_('Cluster ID'),
        max_length=15,
        blank=True,
        null=True,
        help_text=_(
            'Route reflector cluster ID (RFC 4456), typed by hand: a 32-bit number '
            'or an IPv4 address. Empty uses the router ID'
        ),
    )
    confederation_identifier = models.ForeignKey(
        verbose_name=_('Confederation Identifier'),
        to='ipam.ASN',
        on_delete=models.PROTECT,
        related_name='bgp_confederation_instances',
        blank=True,
        null=True,
        help_text=_(
            'The AS the confederation shows to the outside (RFC 5065); the ASN of '
            'the instance is then its member AS'
        ),
    )
    confederation_peers = models.ManyToManyField(
        verbose_name=_('Confederation Peers'),
        to='ipam.ASN',
        related_name='bgp_confederation_peer_instances',
        blank=True,
        help_text=_('The other member ASes of the confederation (RFC 5065)'),
    )
    graceful_restart_time = models.PositiveSmallIntegerField(
        verbose_name=_('Graceful Restart Time'),
        blank=True,
        null=True,
        validators=[MaxValueValidator(4095)],
        help_text=_(
            'Seconds the neighbors wait for this router to restart (RFC 4724, 12 bits)'
        ),
    )
    graceful_restart_stale_time = models.PositiveIntegerField(
        verbose_name=_('Graceful Restart Stale Paths Time'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_('Seconds the routes of a restarting neighbor are kept (RFC 4724)'),
    )
    graceful_restart_helper_only = models.BooleanField(
        verbose_name=_('Graceful Restart Helper Only'),
        blank=True,
        null=True,
        help_text=_('Help the neighbors to restart but do not restart gracefully'),
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_instances',
        blank=True,
        null=True,
    )

    clone_fields = (
        'device',
        'vrf',
        'asn',
        'tenant',
        'asdot',
        'graceful_restart',
        'graceful_restart_time',
        'graceful_restart_stale_time',
        'graceful_restart_helper_only',
        'cluster_id',
        'confederation_identifier',
        'import_policy',
        'export_policy',
    )
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

    @staticmethod
    def confederation_errors(asn, identifier, peers):
        """{field: message} of the confederation settings (RFC 5065). The peers are
        a many to many relation, so they are checked by the form and the serializer."""
        errors = {}
        peers = list(peers or [])
        if peers and identifier is None:
            errors['confederation_peers'] = _('Set the confederation identifier first.')
        if asn is not None and any(peer.pk == asn.pk for peer in peers):
            errors['confederation_peers'] = _(
                'The member AS of the instance is not one of its confederation peers.'
            )
        if identifier is not None and any(peer.pk == identifier.pk for peer in peers):
            errors['confederation_peers'] = _(
                'The confederation identifier is not a member AS.'
            )
        return errors

    @property
    def vrf_route_distinguisher(self):
        """The route distinguisher of the VRF (RFC 4364), kept in NetBox IPAM"""
        return self.vrf.rd if self.vrf_id else None

    @property
    def vrf_import_targets_display(self):
        if not self.vrf_id:
            return None
        return ', '.join(str(target) for target in self.vrf.import_targets.all())

    @property
    def vrf_export_targets_display(self):
        if not self.vrf_id:
            return None
        return ', '.join(str(target) for target in self.vrf.export_targets.all())

    def clean(self):
        super().clean()
        errors = {}
        if self.cluster_id:
            cluster_id = str(self.cluster_id).strip()
            try:
                if cluster_id.isdigit():
                    cluster_id = str(ipaddress.IPv4Address(int(cluster_id)))
                else:
                    cluster_id = str(ipaddress.IPv4Address(cluster_id))
                self.cluster_id = cluster_id
            except ValueError:
                errors['cluster_id'] = _(
                    'The cluster ID is a 32-bit number or an IPv4 address (RFC 4456).'
                )
        if self.confederation_identifier_id:
            if self.confederation_identifier_id == self.asn_id:
                errors['confederation_identifier'] = _(
                    'The confederation identifier is the AS of the confederation, '
                    'not the member AS of the instance (RFC 5065).'
                )
        if self.router_id == '0.0.0.0':
            errors['router_id'] = _('The router ID cannot be 0.0.0.0 (RFC 6286).')
        if not self.graceful_restart:
            for field in (
                'graceful_restart_time',
                'graceful_restart_stale_time',
                'graceful_restart_helper_only',
            ):
                if getattr(self, field) is not None:
                    errors[field] = _('Enable graceful restart (RFC 4724) first.')
        if errors:
            raise ValidationError(errors)


class BGPAddressFamily(PrimaryModel):
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.BGPInstance',
        on_delete=models.CASCADE,
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
    long_lived_stale_time = models.PositiveIntegerField(
        verbose_name=_('Long-Lived Graceful Restart Stale Time'),
        blank=True,
        null=True,
        validators=[MaxValueValidator(16777215)],
        help_text=_(
            'Seconds the routes of a neighbor that went down are kept, marked '
            'LLGR_STALE (RFC 9494, 24 bits)'
        ),
    )

    clone_fields = ('instance', 'address_family')
    prerequisite_models = ('netbox_routing_protocols.BGPInstance',)

    def clean(self):
        super().clean()
        if (
            self.long_lived_stale_time is not None
            and self.instance_id
            and not self.instance.graceful_restart
        ):
            raise ValidationError(
                {
                    'long_lived_stale_time': _(
                        'Long-lived graceful restart needs graceful restart '
                        'on the instance (RFC 9494).'
                    )
                }
            )

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
        on_delete=models.CASCADE,
        related_name='peer_groups',
    )
    listen_limit = models.PositiveIntegerField(
        verbose_name=_('Listen Limit'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_('Maximum number of neighbors accepted from the listen ranges'),
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
        'ebgp_multihop',
        'ttl_security_hops',
        'passive',
        'route_reflector_client',
        'extended_nexthop',
        'keepalive',
        'hold_time',
        'listen_limit',
        'import_policy',
        'export_policy',
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

    def clean(self):
        super().clean()
        if self.route_reflector_client and self.is_ibgp is False:
            raise ValidationError(
                {
                    'route_reflector_client': _(
                        'Only an iBGP neighbor can be a route reflector client '
                        '(RFC 4456).'
                    )
                }
            )

    @property
    def is_ibgp(self):
        """True when the neighbors of the group are in the same AS (iBGP), None when
        the group does not say"""
        if self.remote_as is None:
            return None
        return self.remote_as.asn == (self.local_as or self.instance.asn).asn

    def sessions_without_policy(self):
        """[(peer address family, direction)] of an eBGP group without an explicit
        import or export policy at any level (RFC 8212)"""
        if self.is_ibgp is not False:
            return []
        peer_afs = list(
            self.address_families.select_related('address_family__instance')
        )
        for peer_af in peer_afs:
            peer_af.peer_group = self
        return [
            (peer_af, direction)
            for peer_af in peer_afs
            if peer_af.enabled is not False
            for direction in ('import', 'export')
            if not peer_af.has_policy(direction, None)
        ]


class BGPListenRange(PrimaryModel):
    """A range of addresses a peer group accepts neighbors from (dynamic neighbors,
    FRR listen range, Cisco bgp listen range). The range is a prefix of IPAM."""

    peer_group = models.ForeignKey(
        verbose_name=_('Peer Group'),
        to='netbox_routing_protocols.BGPPeerGroup',
        on_delete=models.CASCADE,
        related_name='listen_ranges',
    )
    prefix = models.ForeignKey(
        verbose_name=_('Prefix'),
        to='ipam.Prefix',
        on_delete=models.PROTECT,
        related_name='bgp_listen_ranges',
    )

    clone_fields = ('peer_group',)
    prerequisite_models = ('netbox_routing_protocols.BGPPeerGroup',)

    class Meta:
        verbose_name = 'BGP Listen Range'
        verbose_name_plural = 'BGP Listen Ranges'
        ordering = ('peer_group', 'prefix', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=('peer_group', 'prefix'),
                name='%(app_label)s_%(class)s_peer_group_prefix',
                violation_error_message=_(
                    'The peer group already listens on this prefix.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.peer_group}: {self.prefix}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:bgplistenrange', args=[self.pk]
        )

    @property
    def instance(self):
        return self.peer_group.instance

    def clean(self):
        super().clean()
        if not (self.peer_group_id and self.prefix_id):
            return
        errors = {}
        group = self.peer_group
        if self.prefix.vrf_id != group.instance.vrf_id:
            errors['prefix'] = _('The prefix must be in the VRF of the BGP instance.')
        elif (
            BGPListenRange.objects.filter(
                peer_group__instance=group.instance, prefix=self.prefix
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            errors['prefix'] = _(
                'Another peer group of the instance already listens on this prefix.'
            )
        if group.remote_as_id is None:
            errors['peer_group'] = _(
                'A peer group that listens needs a remote AS: the neighbors it '
                'accepts are not known beforehand.'
            )
        if errors:
            raise ValidationError(errors)


class BGPRedistribution(PrimaryModel):
    """Routes taken from another protocol into an address family of a BGP instance:
    the protocol, the source instance (for OSPF, IS-IS and EIGRP), the metric (MED,
    RFC 4271 section 5.1.4) and a route policy that filters them. The source must be
    on the device of the instance and in its VRF."""

    SOURCE_FIELDS = {
        BGPRedistributionProtocolChoices.OSPF: 'ospf_source',
        BGPRedistributionProtocolChoices.ISIS: 'isis_source',
        BGPRedistributionProtocolChoices.EIGRP: 'eigrp_source',
    }

    address_family = models.ForeignKey(
        verbose_name=_('Address Family'),
        to='netbox_routing_protocols.BGPAddressFamily',
        on_delete=models.CASCADE,
        related_name='redistributions',
    )
    protocol = models.CharField(
        verbose_name=_('Protocol'),
        max_length=20,
        choices=BGPRedistributionProtocolChoices,
    )
    ospf_source = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='bgp_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Source'),
        blank=True,
        null=True,
    )
    isis_source = models.ForeignKey(
        to='netbox_routing_protocols.ISISInstance',
        related_name='bgp_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('IS-IS Source'),
        blank=True,
        null=True,
    )
    eigrp_source = models.ForeignKey(
        to='netbox_routing_protocols.EIGRPRouter',
        related_name='bgp_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('EIGRP Source'),
        blank=True,
        null=True,
    )
    metric = models.PositiveBigIntegerField(
        verbose_name=_('Metric'),
        help_text=_('MED of the redistributed routes (RFC 4271)'),
        validators=[MaxValueValidator(4294967295)],
        blank=True,
        null=True,
    )
    route_policy = models.ForeignKey(
        verbose_name=_('Route Policy'),
        to='netbox_routing_protocols.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='bgp_redistributions',
        blank=True,
        null=True,
        help_text=_('Filters the redistributed routes'),
    )
    ospf_match = ArrayField(
        base_field=models.CharField(max_length=20, choices=OSPFRouteTypeChoices),
        verbose_name=_('OSPF Route Types'),
        help_text=_(
            'Types of OSPF routes to redistribute, when the source is OSPF. '
            'Empty takes all of them'
        ),
        blank=True,
        default=list,
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='bgp_redistributions',
        blank=True,
        null=True,
    )

    clone_fields = (
        'address_family',
        'protocol',
        'metric',
        'route_policy',
        'ospf_match',
        'tenant',
    )
    prerequisite_models = ('netbox_routing_protocols.BGPAddressFamily',)

    class Meta:
        verbose_name = 'BGP Redistribution'
        verbose_name_plural = 'BGP Redistributions'
        ordering = ('address_family', 'protocol', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=(
                    'address_family',
                    'protocol',
                    'ospf_source',
                    'isis_source',
                    'eigrp_source',
                ),
                name='%(app_label)s_%(class)s_unique_af_source',
                violation_error_message=_(
                    'This source is already redistributed into the address family.'
                ),
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        if self.source is None:
            return self.get_protocol_display()
        return f'{self.get_protocol_display()} {self.source}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:bgpredistribution', args=[self.pk]
        )

    @property
    def source(self):
        field = self.SOURCE_FIELDS.get(self.protocol)
        return getattr(self, field) if field else None

    @property
    def ospf_match_display(self):
        choices = dict(OSPFRouteTypeChoices.CHOICES)
        return ', '.join(choices.get(item, item) for item in self.ospf_match)

    def clean(self):
        super().clean()
        if not self.address_family_id:
            return
        errors = {}
        if self.ospf_match and self.protocol != BGPRedistributionProtocolChoices.OSPF:
            errors['ospf_match'] = _(
                'The route types only apply when the source is OSPF.'
            )
        for protocol, field in self.SOURCE_FIELDS.items():
            is_set = getattr(self, f'{field}_id') is not None
            if protocol == self.protocol and not is_set:
                errors[field] = _('A source is required for this protocol.')
            elif protocol != self.protocol and is_set:
                errors[field] = _(
                    'Only the source of the selected protocol is allowed.'
                )
        if errors:
            raise ValidationError(errors)

        if self.source is None:
            return
        instance = self.address_family.instance
        source = self.source
        if source.device_id != instance.device_id:
            errors[self.SOURCE_FIELDS[self.protocol]] = _(
                'The source must be on the same device as the BGP instance.'
            )
        elif getattr(source, 'vrf_id', None) != instance.vrf_id:
            # an EIGRP router has no VRF: it runs in the global table
            errors[self.SOURCE_FIELDS[self.protocol]] = _(
                'The source must be in the same VRF as the BGP instance (an EIGRP '
                'router is in the global table).'
            )
        if errors:
            raise ValidationError(errors)


class BGPPeer(BGPPeerConfigMixin, PrimaryModel):
    name = models.CharField(
        verbose_name=_('Name'), max_length=100, blank=True, null=True
    )
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.BGPInstance',
        on_delete=models.CASCADE,
        related_name='peers',
    )
    peer = models.ForeignKey(
        verbose_name=_('Peer Address'),
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        related_name='remote_peers',
        blank=True,
        null=True,
    )
    interface = models.ForeignKey(
        verbose_name=_('Interface'),
        to='dcim.Interface',
        on_delete=models.PROTECT,
        related_name='bgp_peers',
        blank=True,
        null=True,
        help_text=_(
            'Unnumbered peer: the session runs over this interface, to the IPv6 '
            'link-local address of the neighbor (RFC 5549). Instead of the address'
        ),
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
        on_delete=models.RESTRICT,
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
        'ebgp_multihop',
        'ttl_security_hops',
        'passive',
        'route_reflector_client',
        'extended_nexthop',
        'keepalive',
        'hold_time',
        'tenant',
    )
    prerequisite_models = ('netbox_routing_protocols.BGPInstance',)

    class Meta:
        verbose_name = 'BGP Peer'
        verbose_name_plural = 'BGP Peers'
        ordering = ('instance', 'peer', 'interface', 'pk')
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_peer_xor_interface',
                condition=(
                    models.Q(peer__isnull=False, interface__isnull=True)
                    | models.Q(peer__isnull=True, interface__isnull=False)
                ),
                violation_error_message=_(
                    'Set the address of the neighbor or the interface it is reached '
                    'through, not both.'
                ),
            ),
            models.UniqueConstraint(
                fields=('instance', 'interface'),
                name='%(app_label)s_%(class)s_instance_interface',
                violation_error_message=_(
                    'The instance already has a peer on this interface.'
                ),
            ),
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
        target = self.peer or self.interface
        if self.name:
            return f'{self.name} ({target})'
        return f'{target}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:bgppeer', args=[self.pk])

    def effective(self, field):
        """The value of a session option: the peer's own, else its group's."""
        value = getattr(self, field)
        if value is None and self.peer_group_id:
            value = getattr(self.peer_group, field)
        return value

    def sessions_without_policy(self):
        """[(peer address family, direction)] of an eBGP session that has no explicit
        import or export policy at any level. RFC 8212: such a session must not accept
        or advertise any route. Only the enabled families are considered."""
        if self.is_ibgp is not False:
            return []
        missing = []
        own = list(self.address_families.select_related('address_family__instance'))
        group_afs = {}
        if self.peer_group_id:
            group_afs = {
                group_af.address_family_id: group_af
                for group_af in self.peer_group.address_families.select_related(
                    'address_family__instance'
                )
            }
        for peer_af in own:
            peer_af.peer = self
        inherited = [
            group_af
            for group_af in group_afs.values()
            if group_af.address_family_id not in {af.address_family_id for af in own}
        ]
        for group_af in inherited:
            group_af.peer_group = self.peer_group
        for peer_af in own + inherited:
            if peer_af.enabled is False:
                continue
            group_af = (
                group_afs.get(peer_af.address_family_id) if peer_af.peer_id else None
            )
            for direction in ('import', 'export'):
                if not peer_af.has_policy(direction, group_af):
                    missing.append((peer_af, direction))
        return missing

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
        if self.interface_id:
            if self.interface.device_id != self.instance.device_id:
                errors['interface'] = _(
                    'The interface is on another device than the BGP instance.'
                )
            elif self.interface.vrf_id != self.instance.vrf_id:
                errors['interface'] = _(
                    'The interface must be in the VRF of the BGP instance.'
                )
            if self.source_id:
                errors['source'] = _('An unnumbered peer has no source address.')
        if self.route_reflector_client and self.is_ibgp is False:
            errors['route_reflector_client'] = _(
                'Only an iBGP neighbor can be a route reflector client (RFC 4456).'
            )
        if self.source_id:
            interface = self.source.assigned_object
            device = getattr(interface, 'device', None)
            if device is not None and device.pk != self.instance.device_id:
                errors['source'] = _(
                    'The source address is on another device than the BGP instance.'
                )
        if errors:
            raise ValidationError(errors)


class BGPPeerAddressFamily(RoutePolicyMixin, PrimaryModel):
    """What a neighbor (or a peer group) exchanges in an address family. The import
    and export policy here are the most specific: they win over the ones of the peer,
    the peer group and the instance (see effective_policy)."""

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
        on_delete=models.RESTRICT,
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
    send_community = ArrayField(
        base_field=models.CharField(max_length=10, choices=BGPCommunityTypeChoices),
        verbose_name=_('Send Community'),
        help_text=_(
            'Kinds of communities sent to the neighbor (RFC 1997, RFC 4360, RFC 8092). '
            'Empty uses the one of the peer group, else the platform default'
        ),
        blank=True,
        default=list,
    )
    next_hop_self = models.BooleanField(
        verbose_name=_('Next Hop Self'), blank=True, null=True
    )
    remove_private_as = models.BooleanField(
        verbose_name=_('Remove Private AS'), blank=True, null=True
    )
    allowas_in = models.PositiveSmallIntegerField(
        verbose_name=_('Allow AS In'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Accept routes with the local AS in the AS path, this many times'),
    )
    maximum_prefix = models.PositiveIntegerField(
        verbose_name=_('Maximum Prefixes'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_('Prefixes accepted from the neighbor in this family (RFC 4486)'),
    )
    maximum_prefix_warning = models.PositiveSmallIntegerField(
        verbose_name=_('Maximum Prefixes Warning'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text=_('Percentage of the limit that logs a warning'),
    )
    maximum_prefix_action = models.CharField(
        verbose_name=_('Maximum Prefixes Action'),
        max_length=20,
        choices=BGPMaximumPrefixActionChoices,
        blank=True,
        null=True,
        help_text=_('When the limit is exceeded; the session is ceased (RFC 4486)'),
    )
    maximum_prefix_restart = models.PositiveIntegerField(
        verbose_name=_('Maximum Prefixes Restart'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text=_('Minutes before the ceased session is opened again'),
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
        'import_policy',
        'export_policy',
        'send_community',
        'next_hop_self',
        'remove_private_as',
        'allowas_in',
        'maximum_prefix',
        'maximum_prefix_warning',
        'maximum_prefix_action',
        'maximum_prefix_restart',
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

    @property
    def send_community_display(self):
        return ', '.join(
            dict(BGPCommunityTypeChoices.CHOICES).get(item, item)
            for item in self.send_community
        )

    def _group_address_family(self):
        """The same address family of the peer group of the peer, if there is one"""
        if self.peer_id and self.peer.peer_group_id:
            return self.peer.peer_group.address_families.filter(
                address_family=self.address_family_id
            ).first()
        return None

    def effective(self, field):
        """The value of an option: the own, else the one the group has for the family"""
        value = getattr(self, field)
        if value in (None, []) and (group_af := self._group_address_family()):
            value = getattr(group_af, field)
        return value

    def _policy_places(self, group_af=_UNSET):
        """The places a policy can be set, most specific first: the address family,
        the same family of the peer group, the peer or the peer group, the peer group
        of the peer, the instance. group_af is the family of the peer group when the
        caller has it."""
        places = [self]
        if group_af is _UNSET:
            group_af = self._group_address_family()
        if group_af:
            places.append(group_af)
        owner = self.assigned_object
        places.append(owner)
        if self.peer_id and self.peer.peer_group_id:
            places.append(self.peer.peer_group)
        places.append(self.address_family.instance)
        return places

    def policy_chain(self, direction, group_af=_UNSET):
        """[(place, policy)], most specific first; direction is 'import' or 'export'.
        The first one with a policy wins."""
        field = f'{direction}_policy'
        return [
            (place, getattr(place, field)) for place in self._policy_places(group_af)
        ]

    def has_policy(self, direction, group_af=_UNSET):
        """Whether any level sets a policy, without loading it"""
        field = f'{direction}_policy_id'
        return any(
            getattr(place, field) is not None for place in self._policy_places(group_af)
        )

    def effective_policy(self, direction, group_af=_UNSET):
        """(policy, place it comes from) or (None, None) when no level sets one"""
        for place, policy in self.policy_chain(direction, group_af):
            if policy is not None:
                return policy, place
        return None, None

    def _effective_policy_display(self, direction):
        policy, place = self.effective_policy(direction)
        if policy is None:
            return None
        return f'{policy} (from {place._meta.verbose_name}: {place})'

    @property
    def effective_import_policy_display(self):
        return self._effective_policy_display('import')

    @property
    def effective_export_policy_display(self):
        return self._effective_policy_display('export')

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
        if self.maximum_prefix is None:
            for field in (
                'maximum_prefix_warning',
                'maximum_prefix_action',
                'maximum_prefix_restart',
            ):
                if getattr(self, field) is not None:
                    errors[field] = _('Set the maximum number of prefixes first.')
        elif self.maximum_prefix_action == BGPMaximumPrefixActionChoices.RESTART:
            if self.maximum_prefix_restart is None:
                errors['maximum_prefix_restart'] = _(
                    'Set the minutes to wait before the session is opened again.'
                )
        elif self.maximum_prefix_restart is not None:
            errors['maximum_prefix_restart'] = _(
                'The restart time only applies to the action that restarts the session.'
            )
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
