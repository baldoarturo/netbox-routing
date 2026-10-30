import hashlib
from itertools import pairwise

import netaddr
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ipam.fields import IPNetworkField
from netbox.models import PrimaryModel

from netbox_routing_protocols import choices
from netbox_routing_protocols.choices.ospf import (
    OSPFAddressFamilyChoices,
    OSPFFastRerouteChoices,
    OSPFNetworkTypeChoices,
    OSPFRangeTypeChoices,
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFAuthenticationChoices,
    OSPFGracefulRestartChoices,
    OSPFMessageDigestAlgorithmChoices,
    OSPFRouteTypeChoices,
    OSPFSegmentIdentifierChoices,
    OSPFSRAlgorithmChoices,
    OSPFRedistributionProtocolChoices,
)
from netbox_routing_protocols.constants.ospf import (
    OSPF_COST_MAX,
    OSPF_COST_MIN,
    OSPF_AUTH_KEY_ID_MAX,
    OSPF_TRAILER_SA_ID_MAX,
    OSPF_AUTH_KEY_ID_MIN,
    OSPF_EXTERNAL_METRIC_MAX,
    OSPF_EXTERNAL_METRIC_MIN,
    OSPF_GRACEFUL_RESTART_PERIOD_DEFAULT,
    OSPF_GRACEFUL_RESTART_PERIOD_MAX,
    OSPF_GRACEFUL_RESTART_PERIOD_MIN,
    OSPF_INSTANCE_ID_MAX,
    OSPF_INSTANCE_ID_MIN,
    OSPF_V3_INSTANCE_ID_MAX,
    OSPF_INTERFACE_TIMERS,
    OSPF_LDP_SYNC_HOLDDOWN_MAX,
    OSPF_LDP_SYNC_HOLDDOWN_MIN,
    OSPF_LSA_MIN_ARRIVAL_DEFAULT,
    OSPF_LSA_MIN_INTERVAL_DEFAULT,
    OSPF_MAX_LSA_THRESHOLD_DEFAULT,
    OSPF_MAX_LSA_THRESHOLD_MAX,
    OSPF_MAX_LSA_THRESHOLD_MIN,
    OSPF_MD5_KEY_MAX_LENGTH,
    OSPF_PRIORITY_DEFAULT,
    OSPF_PRIORITY_MAX,
    OSPF_PRIORITY_MIN,
    OSPF_SIMPLE_PASSWORD_MAX_LENGTH,
    OSPF_SPF_HOLDDOWN_DEFAULT,
    OSPF_SPF_INITIAL_DELAY_DEFAULT,
    OSPF_SPF_LONG_DELAY_DEFAULT,
    OSPF_SPF_SHORT_DELAY_DEFAULT,
    OSPF_SPF_TIME_TO_LEARN_DEFAULT,
    OSPF_STUB_DEFAULT_COST_MAX,
    OSPF_STUB_DEFAULT_COST_MIN,
    OSPF_SR_INDEX_MAX,
    OSPF_SR_LABEL_MAX,
    OSPF_SR_LABEL_MIN,
    OSPF_TAG_MAX,
    OSPF_TE_ADMIN_GROUP_MAX,
    OSPF_TE_METRIC_MAX,
    OSPF_TTL_SECURITY_HOPS_MAX,
    OSPF_TTL_SECURITY_HOPS_MIN,
)
from netbox_routing_protocols.fields.ip import IPAddressField
from netbox_routing_protocols.models.policy import RoutePolicyMixin

__all__ = (
    'OSPFInstance',
    'OSPFArea',
    'OSPFInterface',
    'OSPFNetwork',
    'OSPFRedistribution',
    'OSPFVirtualLink',
    'OSPFSummaryAddress',
    'OSPFNeighbor',
    'OSPFAreaRange',
    'OSPFPrefixSID',
    'OSPFAuthenticationKey',
)


class OSPFAuthenticationMixin(models.Model):
    """
    Authentication settings, on the interface and as defaults on the area and
    the instance. An interface uses its own when it sets an authentication
    type, else the one of its area, else the one of its instance.
    """

    authentication = models.CharField(
        max_length=50, choices=OSPFAuthenticationChoices, blank=True, null=True
    )
    passphrase = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text=_('The key, stored as plain text. For message digest authentication'),
    )
    authentication_key_id = models.PositiveIntegerField(
        verbose_name=_('Key ID'),
        help_text=_(
            'Message digest key ID, 0 to 255 (RFC 2328 D.3); the SA ID of the '
            'authentication trailer, 0 to 65535 (RFC 7166 4.1)'
        ),
        validators=[
            MinValueValidator(OSPF_AUTH_KEY_ID_MIN),
            MaxValueValidator(OSPF_TRAILER_SA_ID_MAX),
        ],
        blank=True,
        null=True,
    )
    message_digest_algorithm = models.CharField(
        verbose_name=_('Message Digest Algorithm'),
        help_text=_(
            'MD5 (RFC 2328) or HMAC-SHA (RFC 5709, RFC 7166); default: MD5. '
            'The authentication trailer takes HMAC-SHA only'
        ),
        choices=OSPFMessageDigestAlgorithmChoices,
        default=OSPFMessageDigestAlgorithmChoices.MD5,
        max_length=20,
    )
    key_chain = models.CharField(
        verbose_name=_('Key Chain'),
        help_text=_('Name of the key chain, for key chain authentication'),
        max_length=100,
        blank=True,
    )
    show_md5 = models.BooleanField(
        verbose_name=_('MD5 Digest'),
        help_text=_('Also show the MD5 digest of the key'),
        default=False,
    )

    AUTHENTICATION_FIELDS = (
        'authentication',
        'passphrase',
        'authentication_key_id',
        'message_digest_algorithm',
        'key_chain',
        'show_md5',
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

    def _inherited_keys(self):
        """Additional keys of the objects below that use this authentication."""
        from netbox_routing_protocols.models import OSPFAuthenticationKey

        def no_own(prefix):
            return Q(**{f'{prefix}authentication__isnull': True}) | Q(
                **{f'{prefix}authentication': ''}
            )

        if isinstance(self, OSPFInstance):
            return OSPFAuthenticationKey.objects.filter(
                Q(area__instance=self) & no_own('area__')
                | Q(ospf_interface__instance=self)
                & no_own('ospf_interface__')
                & no_own('ospf_interface__area__')
                | Q(virtual_link__instance=self) & no_own('virtual_link__')
            )
        if isinstance(self, OSPFArea):
            return OSPFAuthenticationKey.objects.filter(
                Q(ospf_interface__area=self) & no_own('ospf_interface__')
            )
        return OSPFAuthenticationKey.objects.none()

    def _authentication_ip_version(self):
        """4 or 6: the address family of the instance this object belongs to."""
        owner = getattr(self, 'instance', None) or self
        return getattr(owner, 'ip_version', 4)

    def _clean_authentication(self):
        errors = {}
        auth = self.authentication
        version = self._authentication_ip_version()
        allowed = (
            OSPFAuthenticationChoices.IPV6
            if version == 6
            else OSPFAuthenticationChoices.IPV4
        )
        if auth and auth not in allowed:
            if version == 6:
                msg = _(
                    'OSPFv3 has no authentication in the packet header; use the '
                    'authentication trailer (RFC 7166) or a key chain.'
                )
            else:
                msg = _(
                    'The authentication trailer (RFC 7166) is for OSPFv3: IPv6 '
                    'instances.'
                )
            raise ValidationError({'authentication': msg})
        if (
            self.authentication_key_id is not None
            and self.authentication_key_id > OSPF_AUTH_KEY_ID_MAX
            and auth != OSPFAuthenticationChoices.TRAILER
        ):
            errors['authentication_key_id'] = _(
                'The key ID goes up to {max} (RFC 2328 D.3); only the SA ID of the '
                'authentication trailer goes up to {trailer}.'
            ).format(max=OSPF_AUTH_KEY_ID_MAX, trailer=OSPF_TRAILER_SA_ID_MAX)
        if auth == OSPFAuthenticationChoices.TRAILER:
            if not self.passphrase:
                errors['passphrase'] = _('A key is required for the trailer.')
            if self.authentication_key_id is None:
                errors['authentication_key_id'] = _(
                    'The SA ID is required for the trailer (RFC 7166 4.1).'
                )
            if self.message_digest_algorithm == OSPFMessageDigestAlgorithmChoices.MD5:
                errors['message_digest_algorithm'] = _(
                    'The authentication trailer takes HMAC-SHA only (RFC 7166 4.4).'
                )
            if self.key_chain:
                errors['key_chain'] = _('A key chain is not used with the trailer.')
        elif auth == OSPFAuthenticationChoices.SIMPLE:
            if not self.passphrase:
                errors['passphrase'] = _('A password is required.')
            elif len(self.passphrase) > OSPF_SIMPLE_PASSWORD_MAX_LENGTH:
                errors['passphrase'] = _(
                    'A simple password has at most {length} characters (RFC 2328 D.2).'
                ).format(length=OSPF_SIMPLE_PASSWORD_MAX_LENGTH)
            if self.authentication_key_id is not None:
                errors['authentication_key_id'] = _(
                    'A key ID is not used with a simple password.'
                )
            if self.key_chain:
                errors['key_chain'] = _(
                    'A key chain is not used with a simple password.'
                )
        elif auth == OSPFAuthenticationChoices.MESSAGE_DIGEST:
            if not self.passphrase:
                errors['passphrase'] = _('A key is required for message digest.')
            elif (
                self.message_digest_algorithm == OSPFMessageDigestAlgorithmChoices.MD5
                and len(self.passphrase) > OSPF_MD5_KEY_MAX_LENGTH
            ):
                errors['passphrase'] = _(
                    'An MD5 key has at most {length} characters (RFC 2328 D.3).'
                ).format(length=OSPF_MD5_KEY_MAX_LENGTH)
            if self.authentication_key_id is None:
                errors['authentication_key_id'] = _(
                    'A key ID is required for message digest.'
                )
            if self.key_chain:
                errors['key_chain'] = _('A key chain is not used with message digest.')
        elif auth == OSPFAuthenticationChoices.KEYCHAIN:
            if not self.key_chain:
                errors['key_chain'] = _('A key chain name is required.')
            if self.passphrase:
                errors['passphrase'] = _('A key is not used with a key chain.')
            if self.authentication_key_id is not None:
                errors['authentication_key_id'] = _(
                    'A key ID is not used with a key chain.'
                )
        else:
            for field in ('passphrase', 'authentication_key_id', 'key_chain'):
                if getattr(self, field) not in (None, ''):
                    errors[field] = _('Select an authentication type first.')
        if (
            self.pk
            and auth
            not in (
                OSPFAuthenticationChoices.MESSAGE_DIGEST,
                OSPFAuthenticationChoices.TRAILER,
            )
            and (self.authentication_keys.exists() or self._inherited_keys().exists())
        ):
            errors['authentication'] = _(
                'The authentication, or an object that inherits it, has additional '
                'keys, which need message digest or authentication trailer: delete '
                'them first.'
            )
        if self.show_md5 and not self.passphrase:
            errors['show_md5'] = _('There is no key to show the MD5 digest of.')
        if errors:
            raise ValidationError(errors)


class OSPFTimersMixin(models.Model):
    """Hello, dead, retransmit and transmit delay timers (RFC 2328 C.3)."""

    hello_interval = models.PositiveIntegerField(
        verbose_name=_('Hello Interval'),
        help_text=_('Seconds between Hello packets (RFC 2328 value for a LAN: 10)'),
        default=OSPF_INTERFACE_TIMERS['hello_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['hello_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['hello_interval'][1]),
        ],
    )
    dead_interval = models.PositiveBigIntegerField(
        verbose_name=_('Dead Interval'),
        help_text=_(
            'Seconds without Hello packets before a neighbor is declared down (RFC 2328 value for a LAN: 4 x hello, 40)'
        ),
        default=OSPF_INTERFACE_TIMERS['dead_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['dead_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['dead_interval'][1]),
        ],
    )
    retransmit_interval = models.PositiveIntegerField(
        verbose_name=_('Retransmit Interval'),
        help_text=_(
            'Seconds between LSA retransmissions (RFC 2328 value for a LAN: 5)'
        ),
        default=OSPF_INTERFACE_TIMERS['retransmit_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['retransmit_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['retransmit_interval'][1]),
        ],
    )
    transmit_delay = models.PositiveIntegerField(
        verbose_name=_('Transmit Delay'),
        help_text=_(
            'Estimated seconds to transmit an LSA (RFC 2328 value for a LAN: 1)'
        ),
        default=OSPF_INTERFACE_TIMERS['transmit_delay'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['transmit_delay'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['transmit_delay'][1]),
        ],
    )

    class Meta:
        abstract = True

    def _clean_timers(self):
        if (
            self.hello_interval is not None
            and self.dead_interval is not None
            and self.dead_interval <= self.hello_interval
        ):
            raise ValidationError(
                {
                    'dead_interval': _(
                        'The dead interval must be greater than the hello interval.'
                    )
                }
            )


class OSPFTTLSecurityMixin(models.Model):
    """Generalized TTL Security Mechanism for OSPF (RFC 5082)."""

    ttl_security = models.BooleanField(
        verbose_name=_('TTL Security'),
        help_text=_(
            'Send the packets with a TTL of 255 and discard the received ones that arrive with a lower TTL (RFC 5082)'
        ),
        default=False,
    )
    ttl_security_hops = models.PositiveSmallIntegerField(
        verbose_name=_('TTL Security Hops'),
        help_text=_(
            'Maximum number of hops to the neighbor: packets with a TTL below '
            '256 minus this value are discarded (1 for directly connected neighbors)'
        ),
        blank=True,
        null=True,
        validators=[
            MinValueValidator(OSPF_TTL_SECURITY_HOPS_MIN),
            MaxValueValidator(OSPF_TTL_SECURITY_HOPS_MAX),
        ],
    )

    class Meta:
        abstract = True

    def _clean_ttl_security(self):
        if self.ttl_security and self.ttl_security_hops is None:
            raise ValidationError(
                {'ttl_security_hops': _('The number of hops is required.')}
            )
        if not self.ttl_security and self.ttl_security_hops is not None:
            raise ValidationError(
                {'ttl_security_hops': _('Enable TTL security to set the hops.')}
            )


def authentication_conflict(required, own, version=4):
    """
    The authentication type (null, simple password or cryptographic) is a
    parameter of the area, and has to be the same for all the routers attached
    to a network (RFC 2328 C.2 and C.3): the interfaces of an area cannot use a
    different type from the one the area uses.
    """
    if not required or not own or version != 4:
        return False  # OSPFv3 has no such rule: the trailer is per interface
    return _authentication_type(required) != _authentication_type(own)


def _authentication_type(authentication):
    """AuType of RFC 2328 D: the message digest and the key chain are both 2."""
    if authentication in (
        OSPFAuthenticationChoices.MESSAGE_DIGEST,
        OSPFAuthenticationChoices.KEYCHAIN,
    ):
        return 2
    return 1 if authentication == OSPFAuthenticationChoices.SIMPLE else 0


def _authentication_conflict_error(interfaces, required):
    names = ', '.join(str(interface) for interface in interfaces[:5])
    more = len(interfaces) - 5
    return ValidationError(
        {
            'authentication': _(
                'These interfaces or virtual links cannot use {required} authentication: {names}{more}'
            ).format(
                required=required,
                names=names,
                more=_(' and {count} more').format(count=more) if more > 0 else '',
            )
        }
    )


class OSPFInstance(OSPFAuthenticationMixin, RoutePolicyMixin, PrimaryModel):
    name = models.CharField(max_length=100)
    router_id = IPAddressField(verbose_name=_('Router ID'))
    device = models.ForeignKey(
        to='dcim.Device',
        related_name='ospf_instances',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    vrf = models.ForeignKey(
        verbose_name=_('VRF'),
        to='ipam.VRF',
        related_name='ospf_instances',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    address_family = models.CharField(
        verbose_name=_('Address Family'),
        help_text=_(
            'IPv4 is OSPFv2 (RFC 2328), IPv6 is OSPFv3 (RFC 5340). It cannot be '
            'changed: create another instance'
        ),
        max_length=4,
        choices=OSPFAddressFamilyChoices,
        default=OSPFAddressFamilyChoices.IPV4,
    )
    default_originate = models.BooleanField(
        verbose_name=_('Default Originate'),
        help_text=_(
            'Originate a default route (0.0.0.0/0, or ::/0 in OSPFv3) into OSPF. '
            'Unless "always" is set, it is only advertised while a default route exists.'
        ),
        default=False,
    )
    default_originate_always = models.BooleanField(
        verbose_name=_('Default Originate Always'),
        help_text=_('Advertise the default route even if none exists locally'),
        default=False,
    )
    default_originate_metric = models.PositiveIntegerField(
        verbose_name=_('Default Originate Metric'),
        help_text=_('Metric of the originated default route'),
        validators=[
            MinValueValidator(OSPF_EXTERNAL_METRIC_MIN),
            MaxValueValidator(OSPF_EXTERNAL_METRIC_MAX),
        ],
        blank=True,
        null=True,
    )
    default_originate_metric_type = models.CharField(
        verbose_name=_('Default Originate Metric Type'),
        choices=OSPFExternalMetricTypeChoices,
        default=OSPFExternalMetricTypeChoices.TYPE_2,
        max_length=1,
    )

    # Advanced options. Fields left out of the UI take their default, which is
    # the one in the RFC when there is one.
    spf_initial_delay = models.PositiveIntegerField(
        verbose_name=_('SPF Initial Delay'),
        help_text=_('Milliseconds. SPF back-off, RFC 8405 (default: 50)'),
        default=OSPF_SPF_INITIAL_DELAY_DEFAULT,
    )
    spf_short_delay = models.PositiveIntegerField(
        verbose_name=_('SPF Short Delay'),
        help_text=_('Milliseconds. SPF back-off, RFC 8405 (default: 200)'),
        default=OSPF_SPF_SHORT_DELAY_DEFAULT,
    )
    spf_long_delay = models.PositiveIntegerField(
        verbose_name=_('SPF Long Delay'),
        help_text=_('Milliseconds. SPF back-off, RFC 8405 (default: 5000)'),
        default=OSPF_SPF_LONG_DELAY_DEFAULT,
    )
    spf_time_to_learn = models.PositiveIntegerField(
        verbose_name=_('SPF Time to Learn'),
        help_text=_('Milliseconds. SPF back-off, RFC 8405 (default: 500)'),
        default=OSPF_SPF_TIME_TO_LEARN_DEFAULT,
    )
    spf_holddown = models.PositiveIntegerField(
        verbose_name=_('SPF Holddown'),
        help_text=_(
            'Milliseconds, longer than the time to learn. SPF back-off, RFC 8405 (default: 10000)'
        ),
        default=OSPF_SPF_HOLDDOWN_DEFAULT,
    )
    lsa_min_interval = models.PositiveIntegerField(
        verbose_name=_('LSA Minimum Interval'),
        help_text=_(
            'Milliseconds between originations of the same LSA, '
            'MinLSInterval in RFC 2328 (default: 5000)'
        ),
        default=OSPF_LSA_MIN_INTERVAL_DEFAULT,
    )
    lsa_min_arrival = models.PositiveIntegerField(
        verbose_name=_('LSA Minimum Arrival'),
        help_text=_(
            'Milliseconds before accepting a new instance of the same LSA, '
            'MinLSArrival in RFC 2328 (default: 1000)'
        ),
        default=OSPF_LSA_MIN_ARRIVAL_DEFAULT,
    )
    max_metric_router_lsa = models.BooleanField(
        verbose_name=_('Max Metric (Stub Router)'),
        help_text=_(
            'Advertise the maximum metric in the router LSA so that '
            'transit traffic avoids this router (RFC 6987)'
        ),
        default=False,
    )
    max_metric_on_startup = models.PositiveIntegerField(
        verbose_name=_('Max Metric On Startup'),
        help_text=_(
            'Seconds to keep advertising the maximum metric after startup '
            '(requires max metric)'
        ),
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
    )
    graceful_restart = models.CharField(
        verbose_name=_('Graceful Restart'),
        help_text=_('Restart support, RestartSupport in RFC 3623'),
        choices=OSPFGracefulRestartChoices,
        default=OSPFGracefulRestartChoices.DISABLED,
        max_length=20,
    )
    graceful_restart_period = models.PositiveIntegerField(
        verbose_name=_('Graceful Restart Period'),
        help_text=_(
            'Seconds, RestartInterval in RFC 3623: 1 to 1800 (suggested default: 120)'
        ),
        validators=[
            MinValueValidator(OSPF_GRACEFUL_RESTART_PERIOD_MIN),
            MaxValueValidator(OSPF_GRACEFUL_RESTART_PERIOD_MAX),
        ],
        default=OSPF_GRACEFUL_RESTART_PERIOD_DEFAULT,
    )
    graceful_restart_helper = models.BooleanField(
        verbose_name=_('Graceful Restart Helper'),
        help_text=_('Help neighbors that restart gracefully (RFC 3623)'),
        default=True,
    )
    graceful_restart_helper_strict_lsa_checking = models.BooleanField(
        verbose_name=_('Strict LSA Checking'),
        help_text=_(
            'The helper ends the graceful restart when relevant LSAs change '
            '(RFC 3623, suggested default: enabled)'
        ),
        default=True,
    )
    rfc1583_compatibility = models.BooleanField(
        verbose_name=_('RFC 1583 Compatibility'),
        help_text=_(
            'Preference rules for AS-external routes, RFC1583Compatibility in '
            'RFC 2328 (default: enabled)'
        ),
        default=True,
    )
    log_adjacency_changes = models.BooleanField(
        verbose_name=_('Log Adjacency Changes'),
        default=False,
    )
    log_adjacency_changes_detail = models.BooleanField(
        verbose_name=_('Log Adjacency Changes in Detail'),
        help_text=_('Log every state change (requires log adjacency changes)'),
        default=False,
    )
    bfd_all_interfaces = models.BooleanField(
        verbose_name=_('BFD on All Interfaces'),
        default=False,
    )
    passive_interface_default = models.BooleanField(
        verbose_name=_('Passive Interfaces by Default'),
        help_text=_('Interfaces are passive unless configured otherwise'),
        default=False,
    )
    max_lsa = models.PositiveIntegerField(
        verbose_name=_('Max LSAs'),
        help_text=_('Maximum number of LSAs the process accepts'),
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
    )
    max_lsa_threshold = models.PositiveIntegerField(
        verbose_name=_('Max LSAs Warning Threshold'),
        help_text=_('Percentage of max LSAs that triggers a warning (default: 75)'),
        validators=[
            MinValueValidator(OSPF_MAX_LSA_THRESHOLD_MIN),
            MaxValueValidator(OSPF_MAX_LSA_THRESHOLD_MAX),
        ],
        default=OSPF_MAX_LSA_THRESHOLD_DEFAULT,
    )
    max_lsa_warning_only = models.BooleanField(
        verbose_name=_('Max LSAs Warning Only'),
        help_text=_(
            'Only log a warning when the maximum is reached (requires max LSAs)'
        ),
        default=False,
    )
    external_lsdb_limit = models.PositiveIntegerField(
        verbose_name=_('External LSDB Limit'),
        help_text=_(
            'Maximum number of non-default AS-external LSAs, ospfExtLsdbLimit in '
            'RFC 1765. Empty means no limit'
        ),
        blank=True,
        null=True,
    )
    exit_overflow_interval = models.PositiveIntegerField(
        verbose_name=_('Exit Overflow Interval'),
        help_text=_(
            'Seconds before leaving the overflow state; 0 means never until restarted '
            '(RFC 1765, default: 0; requires an external LSDB limit)'
        ),
        default=0,
    )

    reference_bandwidth = models.PositiveIntegerField(
        verbose_name=_('Reference Bandwidth'),
        help_text=_(
            'Mbps. Bandwidth that gets an interface cost of 1, used to derive '
            'the cost of interfaces without one. Empty uses the platform default'
        ),
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
    )
    maximum_paths = models.PositiveSmallIntegerField(
        verbose_name=_('Maximum Paths'),
        help_text=_(
            'Equal-cost paths installed for a destination (ECMP), 1 to 64. '
            'Empty uses the platform default'
        ),
        validators=[MinValueValidator(1), MaxValueValidator(64)],
        blank=True,
        null=True,
    )
    distance_intra_area = models.PositiveSmallIntegerField(
        verbose_name=_('Distance (Intra-Area)'),
        help_text=_(
            'Administrative distance of intra-area routes, 1 to 255. '
            'Empty uses the platform default'
        ),
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        blank=True,
        null=True,
    )
    distance_inter_area = models.PositiveSmallIntegerField(
        verbose_name=_('Distance (Inter-Area)'),
        help_text=_(
            'Administrative distance of inter-area routes, 1 to 255. '
            'Empty uses the platform default'
        ),
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        blank=True,
        null=True,
    )
    distance_external = models.PositiveSmallIntegerField(
        verbose_name=_('Distance (External)'),
        help_text=_(
            'Administrative distance of external routes, 1 to 255. '
            'Empty uses the platform default'
        ),
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        blank=True,
        null=True,
    )

    default_metric = models.PositiveIntegerField(
        verbose_name=_('Default Metric'),
        help_text=_(
            'Metric of the redistributed routes that have none of their own. '
            'Empty uses the platform default'
        ),
        validators=[
            MinValueValidator(OSPF_EXTERNAL_METRIC_MIN),
            MaxValueValidator(OSPF_EXTERNAL_METRIC_MAX),
        ],
        blank=True,
        null=True,
    )

    opaque_capability = models.BooleanField(
        verbose_name=_('Opaque LSAs'),
        help_text=_(
            'Support opaque LSAs: the O bit of the Options field (RFC 5250). '
            'Traffic engineering and segment routing need it'
        ),
        default=False,
    )
    te_router_address = models.GenericIPAddressField(
        verbose_name=_('TE Router Address'),
        help_text=_(
            'Stable address of the router in the traffic engineering LSAs, usually '
            'a loopback (RFC 3630 2.4.1). Empty uses the router ID'
        ),
        protocol='both',
        blank=True,
        null=True,
    )

    segment_routing = models.BooleanField(
        verbose_name=_('Segment Routing'),
        help_text=_(
            'Advertise segment routing (RFC 8665). It uses the extended prefix and '
            'link opaque LSAs (RFC 7684), so it needs the opaque LSAs'
        ),
        default=False,
    )
    srgb_start = models.PositiveIntegerField(
        verbose_name=_('SRGB Start'),
        help_text=_(
            'First label of the segment routing global block, 16 to 1048575. '
            'Empty uses the platform default'
        ),
        validators=[
            MinValueValidator(OSPF_SR_LABEL_MIN),
            MaxValueValidator(OSPF_SR_LABEL_MAX),
        ],
        blank=True,
        null=True,
    )
    srgb_size = models.PositiveIntegerField(
        verbose_name=_('SRGB Size'),
        help_text=_('Number of labels of the block (RFC 8665 2.1: more than 0)'),
        validators=[
            MinValueValidator(1),
            MaxValueValidator(OSPF_SR_LABEL_MAX - OSPF_SR_LABEL_MIN + 1),
        ],
        blank=True,
        null=True,
    )

    ldp_sync = models.BooleanField(
        verbose_name=_('LDP-IGP Synchronization'),
        help_text=_(
            'Advertise the maximum link metric on the interfaces until LDP is '
            'operational on them, so the traffic does not use a path without labels '
            '(RFC 5443)'
        ),
        default=False,
    )
    ldp_sync_holddown = models.PositiveIntegerField(
        verbose_name=_('LDP Sync Hold-down'),
        help_text=_(
            'Seconds to wait for LDP before the interface advertises its normal '
            'metric anyway. Empty to wait indefinitely'
        ),
        validators=[
            MinValueValidator(OSPF_LDP_SYNC_HOLDDOWN_MIN),
            MaxValueValidator(OSPF_LDP_SYNC_HOLDDOWN_MAX),
        ],
        blank=True,
        null=True,
    )
    ospf_instance_id = models.PositiveSmallIntegerField(
        verbose_name=_('Instance ID'),
        help_text=_(
            'Identifies the instance in the packets, so several can run over the '
            'same link; routers only form adjacencies with the same ID (RFC 6549, '
            'RFC 5340 2.4). OSPFv2: 0 to 127; OSPFv3: 0 to 255. The default is 0'
        ),
        default=OSPF_INSTANCE_ID_MIN,
        validators=[
            MinValueValidator(OSPF_INSTANCE_ID_MIN),
            MaxValueValidator(OSPF_V3_INSTANCE_ID_MAX),
        ],
    )
    ADVANCED_FIELDS = (
        'spf_initial_delay',
        'spf_short_delay',
        'spf_long_delay',
        'spf_time_to_learn',
        'spf_holddown',
        'lsa_min_interval',
        'lsa_min_arrival',
        'max_metric_router_lsa',
        'max_metric_on_startup',
        'graceful_restart',
        'graceful_restart_period',
        'graceful_restart_helper',
        'graceful_restart_helper_strict_lsa_checking',
        'rfc1583_compatibility',
        'log_adjacency_changes',
        'log_adjacency_changes_detail',
        'bfd_all_interfaces',
        'passive_interface_default',
        'max_lsa',
        'max_lsa_threshold',
        'max_lsa_warning_only',
        'external_lsdb_limit',
        'exit_overflow_interval',
        'reference_bandwidth',
        'maximum_paths',
        'distance_intra_area',
        'distance_inter_area',
        'distance_external',
        'default_metric',
        'opaque_capability',
        'te_router_address',
        'segment_routing',
        'srgb_start',
        'srgb_size',
        'ldp_sync',
        'ldp_sync_holddown',
        'ospf_instance_id',
    )

    clone_fields = (
        (
            'name',
            'router_id',
            'device',
            'vrf',
            'address_family',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
        )
        + ADVANCED_FIELDS
        + OSPFAuthenticationMixin.AUTHENTICATION_FIELDS
    )
    prerequisite_models = ('dcim.Device',)

    class Meta:
        ordering = ['vrf', 'router_id', 'pk']
        verbose_name = 'OSPF Instance'
        constraints = (
            models.UniqueConstraint(
                fields=('device', 'vrf', 'address_family'),
                name='%(app_label)s_%(class)s_unique_device_vrf_family',
                violation_error_message=_(
                    'The device already has an OSPF instance of this address family '
                    'in this VRF (an empty VRF is the default VRF).'
                ),
                nulls_distinct=False,
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.router_id})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfinstance', args=[self.pk])

    @property
    def ip_version(self):
        """The IP version (4 or 6) the instance routes."""
        return 6 if self.address_family == OSPFAddressFamilyChoices.IPV6 else 4

    @property
    def uses_opaque_lsas(self):
        """Traffic engineering and segment routing travel in opaque LSAs in OSPFv2
        only: OSPFv3 carries the flooding scope in the LSA type (RFC 5340 A.4.2.1)."""
        return self.ip_version == 4

    def _clean_instance_id(self):
        if (
            self.ip_version == 4
            and self.ospf_instance_id is not None
            and self.ospf_instance_id > OSPF_INSTANCE_ID_MAX
        ):
            raise ValidationError(
                {
                    'ospf_instance_id': _(
                        'An OSPFv2 instance ID goes up to {max} (RFC 6549); OSPFv3 '
                        'up to {v3} (RFC 5340 2.4).'
                    ).format(max=OSPF_INSTANCE_ID_MAX, v3=OSPF_V3_INSTANCE_ID_MAX)
                }
            )
        if self.ip_version == 6 and self.opaque_capability:
            raise ValidationError(
                {
                    'opaque_capability': _(
                        'OSPFv3 has no opaque LSAs: the scope is part of the LSA '
                        'type (RFC 5340 A.4.2.1).'
                    )
                }
            )

    def _clean_address_family(self):
        """The family is fixed when the instance is created (a new one is needed)."""
        if not self.pk:
            return
        stored = (
            type(self)
            .objects.filter(pk=self.pk)
            .values_list('address_family', flat=True)
            .first()
        )
        if stored is not None and stored != self.address_family:
            raise ValidationError(
                {
                    'address_family': _(
                        'The address family cannot be changed: create a new instance.'
                    )
                }
            )

    def _clean_advanced_options(self):
        errors = {}
        if not self.spf_initial_delay <= self.spf_short_delay:
            errors['spf_short_delay'] = _(
                'The short delay cannot be shorter than the initial delay.'
            )
        if not self.spf_short_delay <= self.spf_long_delay:
            errors['spf_long_delay'] = _(
                'The long delay cannot be shorter than the short delay.'
            )
        if not self.spf_holddown > self.spf_time_to_learn:
            errors['spf_holddown'] = _(
                'The holddown must be longer than the time to learn.'
            )
        if self.max_metric_on_startup is not None and not self.max_metric_router_lsa:
            errors['max_metric_on_startup'] = _('Max metric must be enabled.')
        if self.log_adjacency_changes_detail and not self.log_adjacency_changes:
            errors['log_adjacency_changes_detail'] = _(
                'Log adjacency changes must be enabled.'
            )
        if self.max_lsa_warning_only and self.max_lsa is None:
            errors['max_lsa_warning_only'] = _('Max LSAs must be set.')
        if self.exit_overflow_interval and self.external_lsdb_limit is None:
            errors['exit_overflow_interval'] = _('An external LSDB limit must be set.')
        if errors:
            raise ValidationError(errors)

    def _clean_interface_authentication(self):
        """The interfaces of the areas that use this default must agree."""
        if not (self.pk and self.authentication):
            return
        interfaces = [
            ospf_interface
            for ospf_interface in OSPFInterface.objects.filter(instance=self)
            .filter(Q(area__authentication__isnull=True) | Q(area__authentication=''))
            .select_related('interface')
            if authentication_conflict(
                self.authentication, ospf_interface.authentication, self.ip_version
            )
        ]
        if not self.areas.filter(area_type=OSPFAreaTypeChoices.BACKBONE).exclude(
            Q(authentication__isnull=True) | Q(authentication='')
        ):
            interfaces += [
                virtual_link
                for virtual_link in self.virtual_links.all()
                if authentication_conflict(
                    self.authentication, virtual_link.authentication, self.ip_version
                )
            ]
        if interfaces:
            raise _authentication_conflict_error(interfaces, self.authentication)

    def _clean_traffic_engineering(self):
        if self.te_router_address:
            address = netaddr.IPAddress(self.te_router_address)
            if address.version != self.ip_version:
                raise ValidationError(
                    {
                        'te_router_address': _(
                            'The router address must be an IPv{version} address, '
                            'like the address family of the instance.'
                        ).format(version=self.ip_version)
                    }
                )
            if address.is_loopback() or address.is_multicast() or int(address) == 0:
                raise ValidationError(
                    {
                        'te_router_address': _(
                            'The router address must be a unicast address, usually '
                            'the one of a loopback interface.'
                        )
                    }
                )
            if self.uses_opaque_lsas and not self.opaque_capability:
                raise ValidationError(
                    {
                        'te_router_address': _(
                            'Traffic engineering needs the opaque LSAs.'
                        )
                    }
                )
        if (
            self.pk
            and self.uses_opaque_lsas
            and not self.opaque_capability
            and self.areas.filter(traffic_engineering=True).exists()
        ):
            raise ValidationError(
                {
                    'opaque_capability': _(
                        'Areas of the instance use traffic engineering, which needs '
                        'the opaque LSAs.'
                    )
                }
            )

    def _clean_ldp_sync(self):
        if not self.ldp_sync and self.ldp_sync_holddown is not None:
            raise ValidationError(
                {
                    'ldp_sync_holddown': _(
                        'Enable LDP-IGP synchronization to set the hold-down.'
                    )
                }
            )

    def _clean_segment_routing(self):
        errors = {}
        if (
            self.segment_routing
            and self.uses_opaque_lsas
            and not self.opaque_capability
        ):
            errors['segment_routing'] = _('Segment routing needs the opaque LSAs.')
        if (self.srgb_start is None) != (self.srgb_size is None):
            errors['srgb_size'] = _('Set both the start and the size of the SRGB.')
        elif self.srgb_start is not None:
            if not self.segment_routing:
                errors['srgb_start'] = _('Segment routing is not enabled.')
            elif self.srgb_start + self.srgb_size - 1 > OSPF_SR_LABEL_MAX:
                errors['srgb_size'] = _(
                    'The block goes past the last MPLS label ({last}).'
                ).format(last=OSPF_SR_LABEL_MAX)
        if self.pk and not errors:
            sids = self.prefix_sids.all()
            if not self.segment_routing:
                if (
                    sids.exists()
                    or self.interfaces.filter(adjacency_sid__isnull=False).exists()
                ):
                    errors['segment_routing'] = _(
                        'The instance has prefix SIDs or adjacency SIDs.'
                    )
            elif (
                self.srgb_size is not None
                and sids.filter(
                    sid_type=OSPFSegmentIdentifierChoices.INDEX, sid__gte=self.srgb_size
                ).exists()
            ):
                errors['srgb_size'] = _(
                    'There are prefix SIDs with an index outside the block.'
                )
        if errors:
            raise ValidationError(errors)

    def clean(self):
        super().clean()
        self._clean_address_family()
        self._clean_instance_id()
        self._clean_traffic_engineering()
        self._clean_segment_routing()
        self._clean_ldp_sync()
        self._clean_advanced_options()
        self._clean_authentication()
        self._clean_interface_authentication()
        if not self.default_originate and (
            self.default_originate_always or self.default_originate_metric is not None
        ):
            raise ValidationError(
                {
                    'default_originate': _(
                        'Default originate must be enabled to set "always" or a metric.'
                    )
                }
            )
        if self.router_id is not None and self.router_id != '':
            try:
                router_id = netaddr.IPAddress(self.router_id)
            except (netaddr.AddrFormatError, ValueError):
                return  # reported by the field's own validation
            if router_id.version != 4:
                raise ValidationError(
                    {'router_id': _('The router ID must be an IPv4 address (x.x.x.x).')}
                )
            if int(router_id) == 0:
                raise ValidationError(
                    {'router_id': _('The router ID cannot be 0.0.0.0.')}
                )
            if self.pk and any(
                netaddr.IPAddress(str(remote).split('/')[0]) == router_id
                for remote in self.virtual_links.values_list(
                    'remote_router_id', flat=True
                )
            ):
                raise ValidationError(
                    {
                        'router_id': _(
                            'A virtual link of the instance has this router ID as '
                            'its remote router.'
                        )
                    }
                )


class OSPFArea(OSPFAuthenticationMixin, PrimaryModel):
    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='areas',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name=_('Instance'),
    )
    area_id = models.CharField(max_length=100, verbose_name='Area ID')
    area_type = models.CharField(
        verbose_name=_('Area Type'),
        choices=OSPFAreaTypeChoices,
        blank=False,
        null=False,
        default='standard',
    )
    default_cost = models.PositiveIntegerField(
        verbose_name=_('Default Cost'),
        help_text=_(
            'Cost of the default route the ABR advertises into the area '
            '(stub and NSSA areas only)'
        ),
        validators=[
            MinValueValidator(OSPF_STUB_DEFAULT_COST_MIN),
            MaxValueValidator(OSPF_STUB_DEFAULT_COST_MAX),
        ],
        blank=True,
        null=True,
    )
    nssa_translate_always = models.BooleanField(
        verbose_name=_('Translate Type 7 Always'),
        help_text=_('Always translate type 7 LSAs into type 5 (NSSA areas only)'),
        default=False,
    )
    nssa_no_redistribution = models.BooleanField(
        verbose_name=_('No Redistribution'),
        help_text=_(
            'Do not import redistributed routes into the NSSA (NSSA areas only)'
        ),
        default=False,
    )
    nssa_default_originate = models.BooleanField(
        verbose_name=_('Default Information Originate'),
        help_text=_('Originate a default type 7 LSA into the NSSA (NSSA areas only)'),
        default=False,
    )
    traffic_engineering = models.BooleanField(
        verbose_name=_('Traffic Engineering'),
        help_text=_(
            'Originate traffic engineering LSAs, opaque type 10 with area flooding '
            'scope (RFC 3630). Needs the opaque LSAs on the instance'
        ),
        default=False,
    )
    fast_reroute = models.BooleanField(
        verbose_name=_('Fast Reroute'),
        help_text=_(
            'Compute loop-free alternate next hops for the routes of the area '
            '(RFC 5286); the interfaces choose the mode'
        ),
        default=False,
    )
    prerequisite_models = ('netbox_routing_protocols.OSPFInstance',)
    clone_fields = (
        'instance',
        'area_id',
        'area_type',
        'default_cost',
        'nssa_translate_always',
        'nssa_no_redistribution',
        'nssa_default_originate',
        'traffic_engineering',
        'fast_reroute',
        *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
    )

    class Meta:
        ordering = ['instance__name', 'area_id', 'pk']
        verbose_name = 'OSPF Area'
        constraints = (
            models.UniqueConstraint(
                fields=('instance', 'area_id'),
                name='%(app_label)s_%(class)s_unique_instance_area_id',
                violation_error_message=_(
                    'The area ID must be unique within the OSPF instance.'
                ),
            ),
        )

    def __str__(self):
        return f'{self.area_id} ({self.instance.name})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfarea', args=[self.pk])

    @property
    def area_number(self):
        """The area ID as a number (0.0.0.0 is 0), or None if it is invalid."""
        try:
            number = int(self.area_id)
        except (TypeError, ValueError):
            try:
                number = int(netaddr.IPAddress(self.area_id))
            except (netaddr.AddrFormatError, TypeError, ValueError):
                return None
        return number if 0 <= number <= 0xFFFFFFFF else None

    def get_authentication_type(self):
        """The authentication type of the area: its own or its instance's."""
        if self.authentication:
            return self.authentication
        if self.instance_id:
            return self.instance.authentication or None
        return None

    def _clean_interface_authentication(self):
        """Every interface of the area has to agree with its authentication."""
        required = self.get_authentication_type()
        if not (self.pk and required):
            return
        interfaces = [
            ospf_interface
            for ospf_interface in self.interfaces.select_related('interface')
            if authentication_conflict(
                required, ospf_interface.authentication, self.instance.ip_version
            )
        ]
        if self.area_type == OSPFAreaTypeChoices.BACKBONE:
            # Virtual links belong to the backbone
            interfaces += [
                virtual_link
                for virtual_link in self.instance.virtual_links.all()
                if authentication_conflict(
                    required, virtual_link.authentication, self.instance.ip_version
                )
            ]
        if interfaces:
            raise _authentication_conflict_error(interfaces, required)

    def _clean_traffic_engineering(self):
        if (
            self.traffic_engineering
            and self.instance_id
            and self.instance.uses_opaque_lsas
            and not self.instance.opaque_capability
        ):
            raise ValidationError(
                {
                    'traffic_engineering': _(
                        'Traffic engineering needs the opaque LSAs on the OSPF instance.'
                    )
                }
            )
        if (
            self.pk
            and not self.traffic_engineering
            and self.interfaces.filter(
                Q(te_metric__isnull=False)
                | Q(te_max_reservable_bandwidth__isnull=False)
                | Q(te_admin_group__isnull=False)
            ).exists()
        ):
            raise ValidationError(
                {
                    'traffic_engineering': _(
                        'Interfaces of the area have traffic engineering attributes.'
                    )
                }
            )

    def clean(self):
        super().clean()
        self._clean_traffic_engineering()
        self._clean_area_type_options()
        self._clean_dependents()
        self._clean_authentication()
        self._clean_interface_authentication()
        self._clean_fast_reroute()
        if self.area_number is None:
            raise ValidationError(
                {'area_id': ['This field must be an integer or a valid net address']}
            )
        # Area 0.0.0.0 is reserved for the backbone (RFC 2328 C.2)
        if self.area_number == 0 and self.area_type != OSPFAreaTypeChoices.BACKBONE:
            raise ValidationError(
                {'area_type': _('Area 0 is the backbone: its type must be Backbone.')}
            )
        if self.area_number != 0 and self.area_type == OSPFAreaTypeChoices.BACKBONE:
            raise ValidationError(
                {'area_id': _('The backbone area ID must be 0 (0.0.0.0).')}
            )

    def _clean_fast_reroute(self):
        if (
            self.pk
            and not self.fast_reroute
            and self.interfaces.filter(fast_reroute__isnull=False).exists()
        ):
            raise ValidationError(
                {
                    'fast_reroute': _(
                        'Interfaces of the area use fast reroute, which needs it '
                        'enabled on the area.'
                    )
                }
            )

    def _clean_dependents(self):
        """What hangs from the area has to stay valid with its type."""
        if not self.pk:
            return
        if (
            self.area_type != OSPFAreaTypeChoices.STANDARD
            and self.virtual_links.exists()
        ):
            raise ValidationError(
                {
                    'area_type': _(
                        'Virtual links cross this area: it has to be a standard '
                        'area (RFC 2328 C.4).'
                    )
                }
            )
        if (
            self.area_type
            not in (
                OSPFAreaTypeChoices.NSSA,
                OSPFAreaTypeChoices.TNSSA,
            )
            and self.ranges.filter(
                range_type=OSPFRangeTypeChoices.NSSA_EXTERNAL
            ).exists()
        ):
            raise ValidationError(
                {
                    'area_type': _(
                        'The area has type 7 to type 5 ranges, which only exist '
                        'on NSSA areas (RFC 3101).'
                    )
                }
            )

    def _clean_area_type_options(self):
        stub_types = (
            OSPFAreaTypeChoices.STUB,
            OSPFAreaTypeChoices.TSA,
            OSPFAreaTypeChoices.NSSA,
            OSPFAreaTypeChoices.TNSSA,
        )
        nssa_types = (OSPFAreaTypeChoices.NSSA, OSPFAreaTypeChoices.TNSSA)
        errors = {}
        if self.default_cost is not None and self.area_type not in stub_types:
            errors['default_cost'] = _(
                'The default cost only applies to stub and NSSA areas.'
            )
        if self.area_type not in nssa_types:
            for field in (
                'nssa_translate_always',
                'nssa_no_redistribution',
                'nssa_default_originate',
            ):
                if getattr(self, field):
                    errors[field] = _('This option only applies to NSSA areas.')
        if errors:
            raise ValidationError(errors)


class OSPFInterface(
    OSPFAuthenticationMixin, OSPFTimersMixin, OSPFTTLSecurityMixin, PrimaryModel
):
    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='interfaces',
        on_delete=models.RESTRICT,
        blank=False,
        null=False,
    )
    area = models.ForeignKey(
        to='netbox_routing_protocols.OSPFArea',
        on_delete=models.RESTRICT,
        related_name='interfaces',
        blank=False,
        null=False,
    )
    interface = models.OneToOneField(
        to='dcim.Interface',
        related_name='ospf_interfaces',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    passive = models.BooleanField(verbose_name='Passive', blank=True, null=True)
    priority = models.PositiveSmallIntegerField(
        verbose_name=_('Priority'),
        help_text=_(
            'Designated router election priority, 0 to 255; 0 never becomes DR '
            '(RFC 2328; default: 1)'
        ),
        validators=[
            MinValueValidator(OSPF_PRIORITY_MIN),
            MaxValueValidator(OSPF_PRIORITY_MAX),
        ],
        default=OSPF_PRIORITY_DEFAULT,
    )
    bfd = models.BooleanField(blank=True, null=True, verbose_name='BFD')
    network_type = models.CharField(
        verbose_name=_('Network Type'),
        help_text=_('OSPF Interface Network Type'),
        choices=choices.OSPFNetworkTypeChoices,
        default=choices.OSPFNetworkTypeChoices.BROADCAST,
        blank=False,
        null=False,
    )
    cost = models.PositiveIntegerField(
        verbose_name=_('Cost'),
        help_text=_(
            'Interface output cost ({min}-{max}). Leave empty to derive it from the interface bandwidth.'
        ).format(min=OSPF_COST_MIN, max=OSPF_COST_MAX),
        validators=[
            MinValueValidator(OSPF_COST_MIN),
            MaxValueValidator(OSPF_COST_MAX),
        ],
        blank=True,
        null=True,
    )
    prefix_suppression = models.BooleanField(
        verbose_name=_('Prefix Suppression'),
        help_text=_(
            'Do not advertise the prefixes of this interface in the router LSA, '
            'hiding transit-only networks (RFC 6860)'
        ),
        blank=True,
        null=True,
    )
    database_filter_all_out = models.BooleanField(
        verbose_name=_('Database Filter All Out'),
        help_text=_('Do not flood any LSA out of this interface'),
        blank=True,
        null=True,
    )
    flood_reduction = models.BooleanField(
        verbose_name=_('Flood Reduction'),
        help_text=_(
            'Flood LSAs as DoNotAge to reduce refresh traffic in stable '
            'topologies (RFC 4136)'
        ),
        blank=True,
        null=True,
    )
    demand_circuit = models.BooleanField(
        verbose_name=_('Demand Circuit'),
        help_text=_(
            'Suppress periodic Hellos and refreshes on a demand circuit ' '(RFC 1793)'
        ),
        blank=True,
        null=True,
    )
    te_metric = models.PositiveBigIntegerField(
        verbose_name=_('TE Metric'),
        help_text=_(
            'Traffic engineering metric of the link, which can differ from the OSPF '
            'cost (RFC 3630 2.5.5)'
        ),
        validators=[MaxValueValidator(OSPF_TE_METRIC_MAX)],
        blank=True,
        null=True,
    )
    te_max_reservable_bandwidth = models.PositiveBigIntegerField(
        verbose_name=_('TE Maximum Reservable Bandwidth'),
        help_text=_(
            'kbit/s that can be reserved on the link (RFC 3630 2.5.7). Empty '
            'reserves up to the bandwidth of the interface'
        ),
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
    )
    te_admin_group = models.PositiveBigIntegerField(
        verbose_name=_('TE Administrative Group'),
        help_text=_(
            '32-bit mask of the administrative groups (affinity, colors) of the '
            'link (RFC 3630 2.5.9)'
        ),
        validators=[MaxValueValidator(OSPF_TE_ADMIN_GROUP_MAX)],
        blank=True,
        null=True,
    )
    adjacency_sid = models.PositiveIntegerField(
        verbose_name=_('Adjacency SID'),
        help_text=_(
            'Local MPLS label of the adjacency over this interface, 16 to 1048575 '
            '(RFC 8665 6.1). Needs segment routing on the instance'
        ),
        validators=[
            MinValueValidator(OSPF_SR_LABEL_MIN),
            MaxValueValidator(OSPF_SR_LABEL_MAX),
        ],
        blank=True,
        null=True,
    )
    fast_reroute = models.CharField(
        verbose_name=_('Fast Reroute'),
        max_length=20,
        choices=OSPFFastRerouteChoices,
        help_text=_(
            'Protect the traffic that uses this interface with a precomputed '
            'alternate. Needs fast reroute on the area'
        ),
        blank=True,
        null=True,
    )
    ldp_sync = models.BooleanField(
        verbose_name=_('LDP-IGP Synchronization'),
        help_text=_(
            'Override the instance setting for this interface (RFC 5443). '
            'Empty to inherit it'
        ),
        blank=True,
        null=True,
    )
    unnumbered = models.BooleanField(
        verbose_name=_('Unnumbered'),
        help_text=_(
            'Point-to-point interface that borrows the address of another interface '
            '(RFC 2328 1.2): it has no network statements'
        ),
        default=False,
    )
    mtu_ignore = models.BooleanField(
        verbose_name=_('MTU Ignore'),
        help_text=_(
            'Ignore the MTU mismatch check when forming adjacencies. '
            'The MTU itself comes from the device interface.'
        ),
        default=False,
    )
    clone_fields = (
        'instance',
        'area',
        'interface',
        'passive',
        'priority',
        'bfd',
        'cost',
        'hello_interval',
        'dead_interval',
        'retransmit_interval',
        'transmit_delay',
        'mtu_ignore',
        'adjacency_sid',
        'fast_reroute',
        'ldp_sync',
        'te_metric',
        'te_max_reservable_bandwidth',
        'te_admin_group',
        'prefix_suppression',
        'database_filter_all_out',
        'flood_reduction',
        'demand_circuit',
        'authentication',
        'passphrase',
        'authentication_key_id',
        'message_digest_algorithm',
        'key_chain',
        'show_md5',
    )
    prerequisite_models = (
        'netbox_routing_protocols.OSPFInstance',
        'netbox_routing_protocols.OSPFArea',
        'dcim.Interface',
    )

    class Meta:
        verbose_name = 'OSPF Interface'
        ordering = ('instance', 'area', 'interface')  # Name may be non-unique

    def __str__(self):
        return f'{self.interface.device} {self.interface.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfinterface', args=[self.pk])

    def get_authentication_source(self):
        """
        Where the authentication in use comes from: ('interface', self),
        ('area', area), ('instance', instance) or (None, None).
        """
        levels = [('interface', self)]
        if self.area_id:
            levels.append(('area', self.area))
        if self.instance_id:
            levels.append(('instance', self.instance))
        for level, source in levels:
            if source.authentication:
                return level, source
        return None, None

    @property
    def authentication_source(self):
        return self.get_authentication_source()[0]

    @property
    def effective_authentication(self):
        source = self.get_authentication_source()[1]
        return source.authentication if source else None

    def _clean_unnumbered(self):
        if not self.unnumbered:
            return
        if self.instance_id and self.instance.ip_version != 4:
            raise ValidationError(
                {
                    'unnumbered': _(
                        'OSPFv3 runs over the link-local addresses: there are no '
                        'unnumbered interfaces.'
                    )
                }
            )
        if self.network_type != OSPFNetworkTypeChoices.POINT_TO_POINT:
            raise ValidationError(
                {'unnumbered': _('Only point-to-point interfaces can be unnumbered.')}
            )
        if self.pk and self.networks.exists():
            raise ValidationError(
                {
                    'unnumbered': _(
                        'An unnumbered interface has no networks: remove them first.'
                    )
                }
            )

    def _clean_fast_reroute(self):
        if self.fast_reroute and self.area_id and not self.area.fast_reroute:
            raise ValidationError(
                {'fast_reroute': _('Fast reroute is not enabled on the area.')}
            )

    def _clean_segment_routing(self):
        if (
            self.adjacency_sid is not None
            and self.instance_id
            and not self.instance.segment_routing
        ):
            raise ValidationError(
                {'adjacency_sid': _('Segment routing is not enabled on the instance.')}
            )

    def _clean_traffic_engineering(self):
        """The traffic engineering attributes need the TE LSAs of the area."""
        if not self.area_id or self.area.traffic_engineering:
            return
        errors = {
            field: _('The area does not use traffic engineering.')
            for field in ('te_metric', 'te_max_reservable_bandwidth', 'te_admin_group')
            if getattr(self, field) is not None
        }
        if errors:
            raise ValidationError(errors)

    def _clean_interface_scope(self):
        """The interface has to be on the device, and in the VRF, of the instance."""
        if not (self.instance_id and self.interface_id):
            return
        interface = self.interface
        if interface.device_id != self.instance.device_id:
            raise ValidationError(
                {
                    'interface': _(
                        'The interface must belong to the device of the OSPF instance.'
                    )
                }
            )
        if interface.vrf_id != self.instance.vrf_id:
            raise ValidationError(
                {
                    'interface': _(
                        'The interface is in {interface_vrf} but the OSPF instance '
                        'is in {instance_vrf}.'
                    ).format(
                        interface_vrf=interface.vrf or _('the global routing table'),
                        instance_vrf=self.instance.vrf or _('the global routing table'),
                    )
                }
            )

    def _clean_area_authentication(self):
        """The interface must agree with the authentication type of its area."""
        if not (self.area_id and self.authentication):
            return
        required = self.area.get_authentication_type()
        if authentication_conflict(
            required, self.authentication, self.instance.ip_version
        ):
            raise ValidationError(
                {
                    'authentication': _(
                        'The area uses {required} authentication, which cannot '
                        'be combined with {own}.'
                    ).format(required=required, own=self.authentication)
                }
            )

    def clean(self):
        super().clean()
        self._clean_authentication()
        self._clean_area_authentication()
        if (
            self.instance_id
            and self.area_id
            and self.area.instance_id != self.instance_id
        ):
            raise ValidationError(
                {'area': _('The area must belong to the OSPF instance.')}
            )
        self._clean_interface_scope()
        self._clean_traffic_engineering()
        self._clean_segment_routing()
        self._clean_fast_reroute()
        self._clean_unnumbered()
        self._clean_timers()
        self._clean_ttl_security()


class OSPFNetwork(PrimaryModel):
    """
    A `network` statement of an OSPF interface: a reference to the IP address
    (and therefore the subnet) configured on that interface. The statement
    itself is not computed here.
    """

    ospf_interface = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInterface',
        related_name='networks',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Interface'),
    )
    ip_address = models.ForeignKey(
        to='ipam.IPAddress',
        related_name='ospf_networks',
        on_delete=models.CASCADE,
        verbose_name=_('IP Address'),
    )

    clone_fields = ('ospf_interface',)
    prerequisite_models = (
        'netbox_routing_protocols.OSPFInterface',
        'ipam.IPAddress',
    )

    class Meta:
        verbose_name = 'OSPF Network'
        ordering = ('ospf_interface', 'ip_address')
        constraints = (
            models.UniqueConstraint(
                fields=('ospf_interface', 'ip_address'),
                name='%(app_label)s_%(class)s_unique_interface_ip_address',
                violation_error_message=_(
                    'This IP address is already a network of the OSPF interface.'
                ),
            ),
        )

    def __str__(self):
        return str(self.subnet)

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfnetwork', args=[self.pk])

    @property
    def subnet(self):
        return netaddr.IPNetwork(str(self.ip_address.address)).cidr

    def clean(self):
        super().clean()
        if not (self.ospf_interface_id and self.ip_address_id):
            return
        if self.ospf_interface.instance.ip_version != 4:
            raise ValidationError(
                {
                    'ospf_interface': _(
                        'OSPFv3 is enabled on the interface, not with networks '
                        '(RFC 5340 2.1): networks are for IPv4 instances.'
                    )
                }
            )
        if self.ospf_interface.unnumbered:
            raise ValidationError(
                {
                    'ospf_interface': _(
                        'The interface is unnumbered: it has no networks.'
                    )
                }
            )
        if self.subnet.version != 4:
            raise ValidationError(
                {'ip_address': _('OSPFv2 networks must be IPv4 addresses.')}
            )
        if self.ip_address.assigned_object != self.ospf_interface.interface:
            raise ValidationError(
                {
                    'ip_address': _(
                        'The IP address must be assigned to the OSPF interface\'s interface ({interface}).'
                    ).format(interface=self.ospf_interface.interface)
                }
            )


class OSPFRedistribution(PrimaryModel):
    """
    Redistribution of routes into an OSPF instance. Connected (local) and
    static routes have no source; for the other protocols, which are the ones
    modelled by the plugin, the source is the process routes are taken from.
    """

    SOURCE_FIELDS = {
        OSPFRedistributionProtocolChoices.OSPF: 'ospf_source',
        OSPFRedistributionProtocolChoices.EIGRP: 'eigrp_source',
        OSPFRedistributionProtocolChoices.BGP: 'bgp_source',
        OSPFRedistributionProtocolChoices.ISIS: 'isis_source',
    }

    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('Instance'),
    )
    protocol = models.CharField(
        verbose_name=_('Protocol'),
        choices=OSPFRedistributionProtocolChoices,
        max_length=20,
    )
    ospf_source = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='ospf_redistributed_into',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Source'),
        blank=True,
        null=True,
    )
    eigrp_source = models.ForeignKey(
        to='netbox_routing_protocols.EIGRPRouter',
        related_name='ospf_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('EIGRP Source'),
        blank=True,
        null=True,
    )
    bgp_source = models.ForeignKey(
        to='netbox_routing_protocols.BGPInstance',
        related_name='ospf_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('BGP Source'),
        blank=True,
        null=True,
    )
    isis_source = models.ForeignKey(
        to='netbox_routing_protocols.ISISInstance',
        related_name='ospf_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('IS-IS Source'),
        blank=True,
        null=True,
    )
    metric = models.PositiveIntegerField(
        verbose_name=_('Metric'),
        help_text=_('Metric of the redistributed routes'),
        validators=[
            MinValueValidator(OSPF_EXTERNAL_METRIC_MIN),
            MaxValueValidator(OSPF_EXTERNAL_METRIC_MAX),
        ],
        blank=True,
        null=True,
    )
    metric_type = models.CharField(
        verbose_name=_('Metric Type'),
        choices=OSPFExternalMetricTypeChoices,
        default=OSPFExternalMetricTypeChoices.TYPE_2,
        max_length=1,
    )
    subnets = models.BooleanField(
        verbose_name=_('Subnets'),
        help_text=_('Redistribute subnets, not only classful networks'),
        default=True,
    )
    route_tag = models.PositiveBigIntegerField(
        verbose_name=_('Route Tag'),
        help_text=_('Tag set on the redistributed routes'),
        validators=[MaxValueValidator(OSPF_TAG_MAX)],
        blank=True,
        null=True,
    )
    route_policy = models.ForeignKey(
        to='netbox_routing_protocols.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='ospf_redistributions',
        verbose_name=_('Route Policy'),
        help_text=_('Route policy applied to the redistributed routes'),
        blank=True,
        null=True,
    )
    ospf_match = ArrayField(
        base_field=models.CharField(max_length=20, choices=OSPFRouteTypeChoices),
        verbose_name=_('OSPF Route Types'),
        help_text=_(
            'Types of OSPF routes to redistribute, when the source is OSPF. '
            'Empty uses the platform default'
        ),
        blank=True,
        default=list,
    )

    clone_fields = (
        'instance',
        'protocol',
        'metric',
        'metric_type',
        'subnets',
        'route_tag',
        'route_policy',
        'ospf_match',
    )
    prerequisite_models = ('netbox_routing_protocols.OSPFInstance',)

    class Meta:
        verbose_name = 'OSPF Redistribution'
        ordering = ('instance', 'protocol', 'pk')
        constraints = (
            models.UniqueConstraint(
                fields=(
                    'instance',
                    'protocol',
                    'ospf_source',
                    'eigrp_source',
                    'bgp_source',
                    'isis_source',
                ),
                name='%(app_label)s_%(class)s_unique_instance_source',
                violation_error_message=_(
                    'This source is already redistributed into the OSPF instance.'
                ),
                nulls_distinct=False,
            ),
        )

    def __str__(self):
        if self.source is None:
            return self.get_protocol_display()
        return f'{self.get_protocol_display()} {self.source}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:ospfredistribution', args=[self.pk]
        )

    @property
    def source(self):
        field = self.SOURCE_FIELDS.get(self.protocol)
        return getattr(self, field) if field else None

    @property
    def ospf_match_display(self):
        labels = dict(OSPFRouteTypeChoices.CHOICES)
        return (
            ', '.join(str(labels.get(value, value)) for value in self.ospf_match) or '—'
        )

    def clean(self):
        super().clean()
        errors = {}
        if self.ospf_match and self.protocol != OSPFRedistributionProtocolChoices.OSPF:
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

        if not self.instance_id or self.source is None:
            return
        if self.protocol == OSPFRedistributionProtocolChoices.OSPF:
            if self.ospf_source_id == self.instance_id:
                raise ValidationError(
                    {
                        'ospf_source': _(
                            'An OSPF instance cannot be redistributed into itself.'
                        )
                    }
                )
        if (
            self.protocol == OSPFRedistributionProtocolChoices.OSPF
            and self.ospf_source.address_family != self.instance.address_family
        ):
            raise ValidationError(
                {
                    'ospf_source': _(
                        'The source runs another address family: IPv4 and IPv6 '
                        'routes cannot be redistributed into one another.'
                    )
                }
            )
        if not self._source_is_on_instance_device():
            raise ValidationError(
                {
                    self.SOURCE_FIELDS[self.protocol]: _(
                        'The source must be on the same device as the OSPF instance.'
                    )
                }
            )

    def _source_is_on_instance_device(self):
        return self.source.device_id == self.instance.device_id


class OSPFVirtualLink(
    OSPFAuthenticationMixin, OSPFTimersMixin, OSPFTTLSecurityMixin, PrimaryModel
):
    """
    A virtual link joins this router to another area border router through a
    non-backbone transit area, to restore or increase the connectivity of the
    backbone (RFC 2328 C.4). It has to be configured at both ends.
    """

    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='virtual_links',
        on_delete=models.CASCADE,
        verbose_name=_('Instance'),
    )
    transit_area = models.ForeignKey(
        to='netbox_routing_protocols.OSPFArea',
        related_name='virtual_links',
        on_delete=models.RESTRICT,
        verbose_name=_('Transit Area'),
    )
    remote_router_id = IPAddressField(
        verbose_name=_('Remote Router ID'),
        help_text=_('Router ID of the other end of the virtual link'),
    )

    clone_fields = (
        'instance',
        'transit_area',
        *OSPF_INTERFACE_TIMERS,
        *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
    )
    prerequisite_models = (
        'netbox_routing_protocols.OSPFInstance',
        'netbox_routing_protocols.OSPFArea',
    )

    class Meta:
        verbose_name = 'OSPF Virtual Link'
        ordering = (
            'instance__name',
            'transit_area__area_id',
            'remote_router_id',
            'pk',
        )
        constraints = (
            models.UniqueConstraint(
                fields=('instance', 'transit_area', 'remote_router_id'),
                name='%(app_label)s_%(class)s_unique_instance_transit_remote',
                violation_error_message=_(
                    'This virtual link already exists in the OSPF instance.'
                ),
            ),
        )

    def __str__(self):
        return f'{self.remote_router_id} via area {self.transit_area}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:ospfvirtuallink', args=[self.pk]
        )

    def get_backbone(self):
        """The backbone area of the instance, if it has one."""
        if not self.instance_id:
            return None
        return self.instance.areas.filter(
            area_type=OSPFAreaTypeChoices.BACKBONE
        ).first()

    def get_authentication_type(self):
        """A virtual link is part of the backbone: its type, else the instance's."""
        backbone = self.get_backbone()
        if backbone is not None:
            return backbone.get_authentication_type()
        return (self.instance.authentication or None) if self.instance_id else None

    def get_authentication_source(self):
        """Where the authentication in use comes from, as for an interface."""
        levels = [('virtual link', self)]
        backbone = self.get_backbone()
        if backbone is not None:
            levels.append(('area', backbone))
        if self.instance_id:
            levels.append(('instance', self.instance))
        for level, source in levels:
            if source.authentication:
                return level, source
        return None, None

    @property
    def authentication_source(self):
        return self.get_authentication_source()[0]

    @property
    def effective_authentication(self):
        source = self.get_authentication_source()[1]
        return source.authentication if source else None

    def clean(self):
        super().clean()
        self._clean_timers()
        self._clean_ttl_security()
        self._clean_authentication()
        errors = {}
        if self.instance_id and self.transit_area_id:
            transit = self.transit_area
            if transit.instance_id != self.instance_id:
                errors['transit_area'] = _(
                    'The transit area must belong to the OSPF instance.'
                )
            elif transit.area_type != OSPFAreaTypeChoices.STANDARD:
                # Not the backbone (RFC 2328 C.4), nor a stub (RFC 2328 C.4)
                # or NSSA (RFC 3101 1.3) area: none of them can be crossed
                errors['transit_area'] = _(
                    'The transit area must be a standard area: virtual links '
                    'cannot cross the backbone, stub or NSSA areas.'
                )
        if self.remote_router_id not in (None, ''):
            try:
                remote = netaddr.IPAddress(self.remote_router_id)
            except (netaddr.AddrFormatError, ValueError):
                remote = None  # reported by the field's own validation
            if remote is not None:
                if remote.version != 4 or int(remote) == 0:
                    errors['remote_router_id'] = _(
                        'The router ID must be an IPv4 address (x.x.x.x) other than 0.0.0.0.'
                    )
                elif self.instance_id and remote == netaddr.IPAddress(
                    self.instance.router_id
                ):
                    errors['remote_router_id'] = _(
                        'The remote router ID cannot be the one of this instance.'
                    )
        if errors:
            raise ValidationError(errors)
        if self.authentication and self.instance_id:
            required = self.get_authentication_type()
            if authentication_conflict(
                required, self.authentication, self.instance.ip_version
            ):
                raise ValidationError(
                    {
                        'authentication': _(
                            'The backbone uses {required} authentication, which '
                            'cannot be combined with {own}.'
                        ).format(required=required, own=self.authentication)
                    }
                )


class OSPFSummaryAddress(PrimaryModel):
    """
    Summarization of the external routes an ASBR redistributes into OSPF: one
    LSA for the prefix replaces those of the routes it covers.
    """

    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='summary_addresses',
        on_delete=models.CASCADE,
        verbose_name=_('Instance'),
    )
    prefix = IPNetworkField(
        verbose_name=_('Prefix'),
        help_text=_(
            'Prefix that summarizes the external routes, of the address family '
            'of the instance'
        ),
    )
    not_advertise = models.BooleanField(
        verbose_name=_('Do Not Advertise'),
        help_text=_(
            'Suppress the routes covered by the prefix instead of summarizing them'
        ),
        default=False,
    )
    route_tag = models.PositiveBigIntegerField(
        verbose_name=_('Route Tag'),
        help_text=_('Tag set on the summary route'),
        validators=[MaxValueValidator(OSPF_TAG_MAX)],
        blank=True,
        null=True,
    )

    clone_fields = ('instance', 'not_advertise', 'route_tag')
    prerequisite_models = ('netbox_routing_protocols.OSPFInstance',)

    class Meta:
        verbose_name = 'OSPF Summary Address'
        verbose_name_plural = 'OSPF Summary Addresses'
        ordering = ('instance__name', 'prefix', 'pk')
        constraints = (
            models.UniqueConstraint(
                fields=('instance', 'prefix'),
                name='%(app_label)s_%(class)s_unique_instance_prefix',
                violation_error_message=_(
                    'This prefix is already summarized in the OSPF instance.'
                ),
            ),
        )

    def __str__(self):
        return str(self.prefix)

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:ospfsummaryaddress', args=[self.pk]
        )

    def clean(self):
        super().clean()
        if self.prefix in (None, ''):
            return
        try:
            prefix = netaddr.IPNetwork(str(self.prefix))
        except (netaddr.AddrFormatError, ValueError):
            return  # reported by the field's own validation
        if self.instance_id and prefix.version != self.instance.ip_version:
            raise ValidationError(
                {
                    'prefix': _(
                        'The prefix must be IPv{version}, like the address '
                        'family of the instance.'
                    ).format(version=self.instance.ip_version)
                }
            )
        if prefix.ip != prefix.cidr.ip:
            raise ValidationError(
                {
                    'prefix': _('The prefix has host bits set: use {cidr}.').format(
                        cidr=prefix.cidr
                    )
                }
            )


class OSPFNeighbor(PrimaryModel):
    """
    A neighbor configured by hand on a non-broadcast (NBMA) or point-to-multipoint
    interface, where it cannot be discovered with multicast Hellos (RFC 2328 C.5
    and C.6): it is identified by its IP address on the network. On NBMA networks
    its eligibility to become the designated router (priority) has to be defined,
    and Hellos to it go out at the poll interval while it is down.
    """

    NBMA_NETWORK_TYPES = (OSPFNetworkTypeChoices.NON_BROADCAST,)
    POINT_TO_MULTIPOINT_NETWORK_TYPES = (
        OSPFNetworkTypeChoices.POINT_TO_MULTIPOINT,
        OSPFNetworkTypeChoices.POINT_TO_MULTIPOINT_NON_BROADCAST,
    )

    ospf_interface = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInterface',
        related_name='neighbors',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Interface'),
    )
    ip_address = IPAddressField(
        verbose_name=_('IP Address'),
        help_text=_('Interface address of the neighbor on the network'),
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name=_('Priority'),
        help_text=_(
            'Eligibility of the neighbor to become the designated router, 0 to 255; '
            '0 is not eligible. Required on non-broadcast networks, not used on '
            'point-to-multipoint ones'
        ),
        validators=[
            MinValueValidator(OSPF_PRIORITY_MIN),
            MaxValueValidator(OSPF_PRIORITY_MAX),
        ],
        blank=True,
        null=True,
    )
    poll_interval = models.PositiveIntegerField(
        verbose_name=_('Poll Interval'),
        help_text=_(
            'Seconds between Hellos to the neighbor while it is down, much larger '
            'than the hello interval. Only on non-broadcast networks; empty uses '
            'the platform default'
        ),
        validators=[MinValueValidator(1)],
        blank=True,
        null=True,
    )

    clone_fields = ('ospf_interface', 'priority', 'poll_interval')
    prerequisite_models = ('netbox_routing_protocols.OSPFInterface',)

    class Meta:
        verbose_name = 'OSPF Neighbor'
        ordering = ('ospf_interface', 'ip_address', 'pk')
        constraints = (
            models.UniqueConstraint(
                fields=('ospf_interface', 'ip_address'),
                name='%(app_label)s_%(class)s_unique_interface_ip_address',
                violation_error_message=_(
                    'This neighbor is already configured on the OSPF interface.'
                ),
            ),
        )

    def __str__(self):
        return str(self.ip_address)

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfneighbor', args=[self.pk])

    def _local_networks(self):
        """
        The IPv4 networks configured on the interface of the OSPF interface.
        `_address_change` = (IP address pk, new address or None) answers for an
        address that is about to change or move away, before it is saved.
        """
        change = getattr(self, '_address_change', None)
        addresses = [
            (address.pk, str(address.address))
            for address in self.ospf_interface.interface.ip_addresses.all()
            if not change or address.pk != change[0]
        ]
        if change and change[1]:
            addresses.append((change[0], change[1]))
        networks = []
        for _pk, address in addresses:
            interface_address = netaddr.IPNetwork(address)
            if interface_address.version == 4:
                networks.append(interface_address)
        return networks

    def clean(self):
        super().clean()
        if not self.ospf_interface_id:
            return
        network_type = self.ospf_interface.network_type
        nbma = network_type in self.NBMA_NETWORK_TYPES
        point_to_multipoint = network_type in self.POINT_TO_MULTIPOINT_NETWORK_TYPES
        errors = {}
        if not (nbma or point_to_multipoint):
            errors['ospf_interface'] = _(
                'Neighbors are configured on non-broadcast and point-to-multipoint '
                'interfaces only.'
            )
        elif nbma:
            if self.priority is None:
                errors['priority'] = _(
                    'The eligibility to become the designated router has to be '
                    'defined on non-broadcast networks.'
                )
            if (
                self.poll_interval is not None
                and self.poll_interval <= self.ospf_interface.hello_interval
            ):
                errors['poll_interval'] = _(
                    'The poll interval must be larger than the hello interval ({hello}).'
                ).format(hello=self.ospf_interface.hello_interval)
        else:
            if self.priority is not None:
                errors['priority'] = _(
                    'No designated router is elected on point-to-multipoint networks.'
                )
            if self.poll_interval is not None:
                errors['poll_interval'] = _(
                    'The poll interval only applies to non-broadcast networks.'
                )
        if self.ip_address not in (None, ''):
            try:
                address = netaddr.IPAddress(self.ip_address)
            except (netaddr.AddrFormatError, ValueError):
                address = None  # reported by the field's own validation
            if address is not None:
                networks = self._local_networks()
                version = self.ospf_interface.instance.ip_version
                if (
                    address.version != version
                    or address.is_loopback()
                    or address.is_multicast()
                ):
                    errors['ip_address'] = _(
                        'The neighbor must have a unicast IPv{version} address.'
                    ).format(version=version)
                elif version == 6:
                    if not address.is_link_local():
                        errors['ip_address'] = _(
                            'OSPFv3 neighbors are identified by their link-local '
                            'address (RFC 5340 3.1.1).'
                        )
                elif any(address == network.ip for network in networks):
                    errors['ip_address'] = _(
                        'This is an address of the interface itself.'
                    )
                elif networks and not any(address in network for network in networks):
                    errors['ip_address'] = _(
                        'The neighbor must be on a network attached to the interface.'
                    )
        if errors:
            raise ValidationError(errors)


class OSPFAreaRange(PrimaryModel):
    """
    An address range of an area (RFC 2328 C.2): an [address, mask] pair that an
    area border router summarizes into a single route when advertising the area
    to the others. Its status is Advertise or DoNotAdvertise (the routes it
    covers are not advertised outside the area at all).
    """

    area = models.ForeignKey(
        to='netbox_routing_protocols.OSPFArea',
        related_name='ranges',
        on_delete=models.CASCADE,
        verbose_name=_('Area'),
    )
    prefix = IPNetworkField(
        verbose_name=_('Prefix'),
        help_text=_('Address range of the area, of the address family of the instance'),
    )
    range_type = models.CharField(
        verbose_name=_('Range Type'),
        help_text=_(
            'Summary of the intra-area routes (RFC 2328 C.2), or, on an NSSA, '
            'the addresses of the type 7 LSAs translated into type 5 (RFC 3101 3.2)'
        ),
        choices=OSPFRangeTypeChoices,
        default=OSPFRangeTypeChoices.SUMMARY,
        max_length=20,
    )
    advertise = models.BooleanField(
        verbose_name=_('Advertise'),
        help_text=_(
            'Status of the range: advertised outside the area as a single route '
            '(Advertise), or not advertised at all (DoNotAdvertise)'
        ),
        default=True,
    )

    clone_fields = ('area', 'range_type', 'advertise')
    prerequisite_models = ('netbox_routing_protocols.OSPFArea',)

    class Meta:
        verbose_name = 'OSPF Area Range'
        ordering = ('area__instance__name', 'area__area_id', 'prefix', 'pk')
        constraints = (
            models.UniqueConstraint(
                fields=('area', 'range_type', 'prefix'),
                name='%(app_label)s_%(class)s_unique_area_type_prefix',
                violation_error_message=_('This range already exists in the area.'),
            ),
        )

    def __str__(self):
        return str(self.prefix)

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfarearange', args=[self.pk])

    def clean(self):
        super().clean()
        if (
            self.area_id
            and self.range_type == OSPFRangeTypeChoices.NSSA_EXTERNAL
            and self.area.area_type
            not in (OSPFAreaTypeChoices.NSSA, OSPFAreaTypeChoices.TNSSA)
        ):
            raise ValidationError(
                {'range_type': _('Type 7 to type 5 ranges only exist on NSSA areas.')}
            )
        if self.prefix in (None, ''):
            return
        try:
            prefix = netaddr.IPNetwork(str(self.prefix))
        except (netaddr.AddrFormatError, ValueError):
            return  # reported by the field's own validation
        if self.area_id and prefix.version != self.area.instance.ip_version:
            raise ValidationError(
                {
                    'prefix': _(
                        'The prefix must be IPv{version}, like the address '
                        'family of the instance.'
                    ).format(version=self.area.instance.ip_version)
                }
            )
        if prefix.ip != prefix.cidr.ip:
            raise ValidationError(
                {
                    'prefix': _('The prefix has host bits set: use {cidr}.').format(
                        cidr=prefix.cidr
                    )
                }
            )


class OSPFPrefixSID(PrimaryModel):
    """
    A prefix segment identifier (RFC 8665 5): the SID of a prefix, advertised in
    the extended prefix opaque LSA. The SID of a node is the one of a host route
    of the router, usually its loopback, with the node flag (RFC 7684 2.1).
    """

    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='prefix_sids',
        on_delete=models.CASCADE,
        verbose_name=_('Instance'),
    )
    prefix = IPNetworkField(
        verbose_name=_('Prefix'),
        help_text=_(
            'Prefix the SID is advertised for, of the address family of the ' 'instance'
        ),
    )
    sid_type = models.CharField(
        verbose_name=_('SID Type'),
        help_text=_(
            'An index into the SRGB (flags V and L clear) or an absolute, local '
            'MPLS label (V and L set). The other combinations are invalid'
        ),
        choices=OSPFSegmentIdentifierChoices,
        default=OSPFSegmentIdentifierChoices.INDEX,
        max_length=10,
    )
    sid = models.PositiveBigIntegerField(
        verbose_name=_('SID'),
        help_text=_('The index (up to 4294967295) or the label (16 to 1048575)'),
        validators=[MaxValueValidator(OSPF_SR_INDEX_MAX)],
    )
    algorithm = models.PositiveSmallIntegerField(
        verbose_name=_('Algorithm'),
        help_text=_('SR-Algorithm the SID belongs to (RFC 8665 3.1)'),
        choices=OSPFSRAlgorithmChoices,
        default=OSPFSRAlgorithmChoices.SPF,
    )
    node_sid = models.BooleanField(
        verbose_name=_('Node SID'),
        help_text=_(
            'The prefix identifies the router itself: the N flag of the extended '
            'prefix TLV (RFC 7684 2.1). It has to be a host route'
        ),
        default=False,
    )
    no_php = models.BooleanField(
        verbose_name=_('No PHP'),
        help_text=_('NP flag: the penultimate hop must not pop the SID (RFC 8665 5)'),
        default=False,
    )
    explicit_null = models.BooleanField(
        verbose_name=_('Explicit Null'),
        help_text=_(
            'E flag: upstream neighbors replace the SID with an explicit null '
            'label (RFC 8665 5)'
        ),
        default=False,
    )

    clone_fields = (
        'instance',
        'sid_type',
        'algorithm',
        'node_sid',
        'no_php',
        'explicit_null',
    )
    prerequisite_models = ('netbox_routing_protocols.OSPFInstance',)

    class Meta:
        verbose_name = 'OSPF Prefix SID'
        verbose_name_plural = 'OSPF Prefix SIDs'
        ordering = ('instance__name', 'prefix', 'algorithm', 'pk')
        constraints = (
            models.UniqueConstraint(
                fields=('instance', 'prefix', 'algorithm'),
                name='%(app_label)s_%(class)s_unique_instance_prefix_algorithm',
                violation_error_message=_(
                    'This prefix already has a SID for the algorithm.'
                ),
            ),
            models.UniqueConstraint(
                fields=('instance', 'algorithm', 'sid_type', 'sid'),
                name='%(app_label)s_%(class)s_unique_instance_algorithm_sid',
                violation_error_message=_(
                    'This SID is already used by another prefix for the algorithm.'
                ),
            ),
        )

    def __str__(self):
        return f'{self.prefix} ({self.get_sid_type_display()} {self.sid})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:ospfprefixsid', args=[self.pk])

    def clean(self):
        super().clean()
        errors = {}
        if self.instance_id and not self.instance.segment_routing:
            errors['instance'] = _('Segment routing is not enabled on the instance.')
        if self.sid is not None:
            if self.sid_type == OSPFSegmentIdentifierChoices.ABSOLUTE:
                if not OSPF_SR_LABEL_MIN <= self.sid <= OSPF_SR_LABEL_MAX:
                    errors['sid'] = _('A label goes from {first} to {last}.').format(
                        first=OSPF_SR_LABEL_MIN, last=OSPF_SR_LABEL_MAX
                    )
            elif (
                self.instance_id
                and self.instance.srgb_size is not None
                and self.sid >= self.instance.srgb_size
            ):
                errors['sid'] = _(
                    'The index is outside the SRGB, which has {size} labels.'
                ).format(size=self.instance.srgb_size)
        if self.prefix not in (None, ''):
            try:
                prefix = netaddr.IPNetwork(str(self.prefix))
            except (netaddr.AddrFormatError, ValueError):
                prefix = None  # reported by the field's own validation
            if prefix is not None:
                if self.instance_id and prefix.version != self.instance.ip_version:
                    errors['prefix'] = _(
                        'The prefix must be IPv{version}, like the address '
                        'family of the instance.'
                    ).format(version=self.instance.ip_version)
                elif prefix.ip != prefix.cidr.ip:
                    errors['prefix'] = _(
                        'The prefix has host bits set: use {cidr}.'
                    ).format(cidr=prefix.cidr)
                elif self.node_sid and prefix.prefixlen != (
                    32 if prefix.version == 4 else 128
                ):
                    errors['node_sid'] = _('The SID of a node is for a host route.')
        if errors:
            raise ValidationError(errors)


_KEY_PARENTS = ('instance', 'area', 'ospf_interface', 'virtual_link')


class OSPFAuthenticationKey(PrimaryModel):
    """
    An additional key of the cryptographic authentication of an instance, an
    area, an interface or a virtual link, to roll the keys over without losing
    the adjacencies: a router sends with one key and accepts any of the keys
    that are valid (RFC 2328 D.3). The optional lifetimes are the ones of
    RFC 7474: accept from, send from, send until and accept until.
    """

    PARENTS = _KEY_PARENTS

    instance = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInstance',
        related_name='authentication_keys',
        on_delete=models.CASCADE,
        verbose_name=_('Instance'),
        blank=True,
        null=True,
    )
    area = models.ForeignKey(
        to='netbox_routing_protocols.OSPFArea',
        related_name='authentication_keys',
        on_delete=models.CASCADE,
        verbose_name=_('Area'),
        blank=True,
        null=True,
    )
    ospf_interface = models.ForeignKey(
        to='netbox_routing_protocols.OSPFInterface',
        related_name='authentication_keys',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Interface'),
        blank=True,
        null=True,
    )
    virtual_link = models.ForeignKey(
        to='netbox_routing_protocols.OSPFVirtualLink',
        related_name='authentication_keys',
        on_delete=models.CASCADE,
        verbose_name=_('Virtual Link'),
        blank=True,
        null=True,
    )
    key_id = models.PositiveIntegerField(
        verbose_name=_('Key ID'),
        help_text=_(
            'Message digest key ID, 0 to 255 (RFC 2328 D.3); the SA ID of the '
            'authentication trailer, 0 to 65535 (RFC 7166 4.1)'
        ),
        validators=[
            MinValueValidator(OSPF_AUTH_KEY_ID_MIN),
            MaxValueValidator(OSPF_TRAILER_SA_ID_MAX),
        ],
    )
    passphrase = models.CharField(
        max_length=200,
        help_text=_('The key, stored as plain text'),
    )
    message_digest_algorithm = models.CharField(
        verbose_name=_('Message Digest Algorithm'),
        help_text=_('MD5 (RFC 2328) or HMAC-SHA (RFC 5709, RFC 7166); default: MD5'),
        choices=OSPFMessageDigestAlgorithmChoices,
        default=OSPFMessageDigestAlgorithmChoices.MD5,
        max_length=20,
    )
    accept_from = models.DateTimeField(
        verbose_name=_('Accept From'),
        help_text=_('KeyStartAccept (RFC 7474): the router accepts the key from here'),
        blank=True,
        null=True,
    )
    send_from = models.DateTimeField(
        verbose_name=_('Send From'),
        help_text=_(
            'KeyStartGenerate (RFC 7474): the router signs with the key from here'
        ),
        blank=True,
        null=True,
    )
    send_until = models.DateTimeField(
        verbose_name=_('Send Until'),
        help_text=_(
            'KeyStopGenerate (RFC 7474): the router stops signing with the key'
        ),
        blank=True,
        null=True,
    )
    accept_until = models.DateTimeField(
        verbose_name=_('Accept Until'),
        help_text=_('KeyStopAccept (RFC 7474): the router stops accepting the key'),
        blank=True,
        null=True,
    )

    clone_fields = (
        'instance',
        'area',
        'ospf_interface',
        'virtual_link',
        'message_digest_algorithm',
    )
    prerequisite_models = ('netbox_routing_protocols.OSPFInstance',)

    class Meta:
        verbose_name = 'OSPF Authentication Key'
        ordering = (
            'instance',
            'area',
            'ospf_interface',
            'virtual_link',
            'key_id',
            'pk',
        )
        constraints = (
            models.CheckConstraint(
                condition=(
                    Q(
                        instance__isnull=False,
                        area__isnull=True,
                        ospf_interface__isnull=True,
                        virtual_link__isnull=True,
                    )
                    | Q(
                        instance__isnull=True,
                        area__isnull=False,
                        ospf_interface__isnull=True,
                        virtual_link__isnull=True,
                    )
                    | Q(
                        instance__isnull=True,
                        area__isnull=True,
                        ospf_interface__isnull=False,
                        virtual_link__isnull=True,
                    )
                    | Q(
                        instance__isnull=True,
                        area__isnull=True,
                        ospf_interface__isnull=True,
                        virtual_link__isnull=False,
                    )
                ),
                name='%(app_label)s_%(class)s_one_parent',
                violation_error_message=_(
                    'A key belongs to exactly one instance, area, interface or virtual link.'
                ),
            ),
            *(
                models.UniqueConstraint(
                    fields=(parent, 'key_id'),
                    condition=Q(**{f'{parent}__isnull': False}),
                    name=f'%(app_label)s_%(class)s_unique_{parent}_key_id',
                    violation_error_message=_(
                        'The key ID is already used by another key.'
                    ),
                )
                for parent in _KEY_PARENTS
            ),
        )

    def __str__(self):
        return f'Key {self.key_id}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:ospfauthenticationkey', args=[self.pk]
        )

    @property
    def parent(self):
        for name in self.PARENTS:
            parent = getattr(self, name)
            if parent is not None:
                return parent
        return None

    @staticmethod
    def _effective_authentication(parent):
        """The authentication the parent uses: its own or the one it inherits."""
        if isinstance(parent, OSPFArea):
            return parent.get_authentication_type()
        if isinstance(parent, (OSPFInterface, OSPFVirtualLink)):
            source = parent.get_authentication_source()[1]
            return source.authentication if source else None
        return parent.authentication

    @staticmethod
    def _effective_key_id(parent):
        if isinstance(parent, (OSPFInterface, OSPFVirtualLink)):
            source = parent.get_authentication_source()[1]
            return source.authentication_key_id if source else None
        return parent.authentication_key_id

    def _clean_parent(self):
        set_parents = [n for n in self.PARENTS if getattr(self, f'{n}_id') is not None]
        if len(set_parents) != 1:
            raise ValidationError(
                _(
                    'A key belongs to exactly one instance, area, interface or '
                    'virtual link.'
                )
            )
        parent = self.parent
        auth = self._effective_authentication(parent)
        if auth not in (
            OSPFAuthenticationChoices.MESSAGE_DIGEST,
            OSPFAuthenticationChoices.TRAILER,
        ):
            raise ValidationError(
                _(
                    'Several keys need message digest or authentication trailer '
                    'authentication on the {parent}.'
                ).format(parent=parent._meta.verbose_name)
            )
        return parent, auth

    def clean(self):
        super().clean()
        parent, auth = self._clean_parent()
        errors = {}
        if self.key_id == self._effective_key_id(parent):
            errors['key_id'] = _('This is the key ID of the authentication itself.')
        if auth == OSPFAuthenticationChoices.TRAILER:
            if self.message_digest_algorithm == OSPFMessageDigestAlgorithmChoices.MD5:
                errors['message_digest_algorithm'] = _(
                    'The authentication trailer takes HMAC-SHA only (RFC 7166 4.4).'
                )
        else:
            if self.key_id is not None and self.key_id > OSPF_AUTH_KEY_ID_MAX:
                errors['key_id'] = _(
                    'The key ID of message digest goes up to {max} (RFC 2328 D.3).'
                ).format(max=OSPF_AUTH_KEY_ID_MAX)
            if (
                self.message_digest_algorithm == OSPFMessageDigestAlgorithmChoices.MD5
                and len(self.passphrase or '') > OSPF_MD5_KEY_MAX_LENGTH
            ):
                errors['passphrase'] = _(
                    'An MD5 key has at most {length} characters (RFC 2328 D.3).'
                ).format(length=OSPF_MD5_KEY_MAX_LENGTH)
        # RFC 7474 3: accept from <= send from <= send until <= accept until
        times = [
            ('accept_from', self.accept_from),
            ('send_from', self.send_from),
            ('send_until', self.send_until),
            ('accept_until', self.accept_until),
        ]
        set_times = [(name, value) for name, value in times if value is not None]
        for (_a, earlier), (name, later) in pairwise(set_times):
            if later < earlier:
                errors[name] = _(
                    'The lifetimes go in order: accept from, send from, send until, '
                    'accept until (RFC 7474).'
                )
                break
        if errors:
            raise ValidationError(errors)
