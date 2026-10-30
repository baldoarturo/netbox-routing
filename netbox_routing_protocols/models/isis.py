# SPDX-License-Identifier: Apache-2.0

import netaddr
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ipam.fields import IPNetworkField
from netbox.models import PrimaryModel

from netbox_routing_protocols import choices
from netbox_routing_protocols.choices.isis import ISISSettingChoices
from netbox_routing_protocols.constants.isis import (
    ISISSETTING_ASSIGNMENT_MODEL_NAMES,
    ISISSETTING_ASSIGNMENT_MODELS,
)
from netbox_routing_protocols.helpers.isis import (
    auth_pair_errors,
    metric_errors,
    net_error,
    range_errors,
    router_id_error,
    type_levels,
)
from netbox_routing_protocols.models.policy import RoutePolicyMixin

# Label space of segment routing (RFC 8660, RFC 8667): 20 bits, 0-15 are reserved
SR_MIN_LABEL = 16
SR_MAX_LABEL = 1048575

__all__ = (
    'ISISInstance',
    'ISISInterface',
    'ISISSetting',
    'ISISLevel',
    'ISISInterfaceLevel',
    'ISISSegmentRouting',
    'ISISFlexAlgo',
    'ISISPrefixSID',
    'ISISSRv6Locator',
)


class ISISSetting(PrimaryModel):
    """EAV long-tail for IS-IS scalars (mirrors BGPSetting).

    Attaches to an ISISInstance or ISISInterface via a generic FK; the
    divergent/long-tail knobs that don't warrant their own column live
    here as (key, value) pairs validated against ISISSettingChoices.
    """

    assigned_object_type = models.ForeignKey(
        verbose_name=_('Assigned Object Type'),
        to=ContentType,
        limit_choices_to=ISISSETTING_ASSIGNMENT_MODELS,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    assigned_object_id = models.PositiveBigIntegerField(
        verbose_name=_('Assigned Object ID'), blank=True, null=True
    )
    assigned_object = GenericForeignKey(
        ct_field='assigned_object_type', fk_field='assigned_object_id'
    )
    key = models.CharField(
        verbose_name=_('Setting Name'),
        max_length=64,
        choices=ISISSettingChoices,
    )
    value = models.CharField(
        verbose_name=_('Setting Value'),
        max_length=128,
    )

    class Meta:
        verbose_name = 'IS-IS Setting'
        verbose_name_plural = 'IS-IS Settings'
        ordering = (
            'assigned_object_type',
            'assigned_object_id',
            'key',
            'pk',
        )
        constraints = [
            models.UniqueConstraint(
                fields=('assigned_object_type', 'assigned_object_id', 'key'),
                name='netbox_routing_protocols_isissettings_unique',
            ),
            models.CheckConstraint(
                condition=models.Q(
                    assigned_object_type__isnull=False,
                    assigned_object_id__isnull=False,
                ),
                name='netbox_routing_protocols_isissetting_assignment_required',
            ),
        ]

    def clean(self):
        super().clean()
        # An ISISSetting is meaningless unless attached to an ISISInstance or
        # ISISInterface. ISISSettingForm.clean() already enforces this for the
        # UI; mirror it at the model layer so the API and bulk-import paths
        # cannot persist orphan rows either (the CheckConstraint is the DB
        # backstop, and NULLs would also defeat the unique constraint).
        if self.assigned_object_type_id is None or self.assigned_object_id is None:
            raise ValidationError(_('An IS-IS Setting must be assigned to an object.'))
        # NB: a *dangling* assigned_object_id (valid type, nonexistent row) is
        # already rejected by NetBox's base NetBoxModel.clean(), which validates
        # every GenericForeignKey's existence. See
        # ISISSettingAssignmentAPITestCase.test_create_with_nonexistent_object_is_rejected.
        # The assigned type must be an IS-IS model: limit_choices_to only constrains the
        # form picker, so without this the API/bulk-import paths could attach a setting to
        # an arbitrary object type and break the EAV contract.
        if (
            self.assigned_object_type.app_label != 'netbox_routing_protocols'
            or self.assigned_object_type.model not in ISISSETTING_ASSIGNMENT_MODEL_NAMES
        ):
            raise ValidationError(
                {
                    'assigned_object_type': _(
                        'IS-IS Setting must be assigned to an ISISInstance or ISISInterface.'
                    )
                }
            )
        # The value must match the type the key declares in ISISSettingChoices.FIELD_TYPES.
        # The typed Mixin enforces this for inline editing, but the standalone form / API /
        # import accept free-form text, so a typed knob (integer/boolean) could otherwise be
        # stored with a junk value. (The mixin persist path also calls clean(), so this is a
        # shared backstop.)
        field_type = ISISSettingChoices.FIELD_TYPES.get(self.key)
        if field_type == 'integer':
            try:
                parsed = int(self.value)
            except (TypeError, ValueError):
                raise ValidationError(
                    {'value': _('This setting requires an integer value.')}
                )
            # Every integer ISIS setting is a count/timer/metric; the form enforces min_value=0,
            # so the model backstop (API/import/direct writes) must reject negatives too.
            if parsed < 0:
                raise ValidationError(
                    {'value': _('This setting requires a non-negative integer value.')}
                )
            if self.key == 'max_area_addresses' and parsed > 254:
                raise ValidationError(
                    {
                        'value': _(
                            'The maximum area addresses is at most 254 (ISO 10589).'
                        )
                    }
                )
        elif self.key in ('te_ipv4_router_id', 'te_ipv6_router_id'):
            message = router_id_error(self.value, 4 if self.key[6] == '4' else 6)
            if message:
                raise ValidationError({'value': message})
        elif field_type == 'boolean':
            if str(self.value).strip().lower() not in (
                'true',
                'false',
                '1',
                '0',
                'yes',
                'no',
            ):
                raise ValidationError(
                    {'value': _('This setting requires a boolean value.')}
                )

    def __str__(self):
        return f'{self.assigned_object}: {self.key}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isissetting', args=[self.pk])


class ISISInstance(RoutePolicyMixin, PrimaryModel):
    device = models.ForeignKey(
        verbose_name=_('Device'),
        to='dcim.Device',
        related_name='isis_instances',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    vrf = models.ForeignKey(
        verbose_name=_('VRF'),
        to='ipam.VRF',
        related_name='isis_instances',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    process_tag = models.CharField(
        verbose_name=_('Process Tag'),
        max_length=100,
        blank=True,
        default='',
        help_text=_(
            "IS-IS process area-tag; empty string for the untagged 'router isis' process"
        ),
    )
    net = models.CharField(
        verbose_name=_('NET'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Network Entity Title (e.g. 49.0001.0001.0001.0001.00)'),
    )
    is_type = models.CharField(
        verbose_name=_('IS type'),
        max_length=50,
        choices=choices.ISISIsTypeChoices,
        blank=True,
        default='',
        help_text=_('IS type — absent means IOS default (level-1-2)'),
    )
    metric_style = models.CharField(
        verbose_name=_('Metric style'),
        max_length=20,
        choices=choices.ISISMetricStyleChoices,
        blank=True,
        default='',
        help_text=_(
            'Metric style: wide, narrow, or transition. Absent = IOS default (narrow).'
        ),
    )
    overload_bit = models.BooleanField(
        verbose_name=_('Overload bit'),
        null=True,
        blank=True,
        help_text=_('Set the IS-IS overload bit (set-overload-bit).'),
    )
    area_auth_type = models.CharField(
        verbose_name=_('Area auth type'),
        max_length=16,
        choices=choices.ISISAuthTypeChoices,
        blank=True,
        default='',
        help_text=_(
            'IS-IS area password authentication type (md5, text or an HMAC-SHA variant).'
        ),
    )
    area_auth_key = models.CharField(
        verbose_name=_('Area auth key'),
        max_length=128,
        blank=True,
        default='',
        help_text=_(
            'IS-IS area password authentication key (plaintext — routing-protocol auth, not config access).'
        ),
    )
    domain_auth_type = models.CharField(
        verbose_name=_('Domain auth type'),
        max_length=16,
        choices=choices.ISISAuthTypeChoices,
        blank=True,
        default='',
        help_text=_(
            'IS-IS domain password authentication type (md5, text or an HMAC-SHA variant).'
        ),
    )
    domain_auth_key = models.CharField(
        verbose_name=_('Domain auth key'),
        max_length=128,
        blank=True,
        default='',
        help_text=_(
            'IS-IS domain password authentication key (plaintext — routing-protocol auth, not config access).'
        ),
    )
    # SPF / LSP timers — initial-delay and max-wait mean the same across Cisco,
    # Nokia, Junos and IOS-XR, so they get their own columns. The backoff
    # sub-knob (second-wait vs rapid-runs) diverges by algorithm → ISISSetting.
    spf_initial_wait = models.PositiveIntegerField(
        verbose_name=_('SPF initial wait'),
        blank=True,
        null=True,
        help_text=_(
            'Initial SPF delay in milliseconds (Cisco initial-wait / Nokia spf-initial-wait / Junos delay).'
        ),
    )
    spf_max_wait = models.PositiveIntegerField(
        verbose_name=_('SPF max wait'),
        blank=True,
        null=True,
        help_text=_(
            'Maximum SPF wait in milliseconds (Cisco maximum-wait / Nokia spf-max-wait / Junos holddown).'
        ),
    )
    lsp_initial_wait = models.PositiveIntegerField(
        verbose_name=_('LSP-gen initial wait'),
        blank=True,
        null=True,
        help_text=_('Initial LSP generation delay in milliseconds.'),
    )
    lsp_max_wait = models.PositiveIntegerField(
        verbose_name=_('LSP-gen max wait'),
        blank=True,
        null=True,
        help_text=_('Maximum LSP generation wait in milliseconds.'),
    )
    lsp_lifetime = models.PositiveIntegerField(
        verbose_name=_('LSP lifetime'),
        blank=True,
        null=True,
        help_text=_('Maximum LSP lifetime in seconds (max-lsp-lifetime).'),
    )
    lsp_refresh_interval = models.PositiveIntegerField(
        verbose_name=_('LSP refresh interval'),
        blank=True,
        null=True,
        help_text=_('LSP refresh interval in seconds (lsp-refresh-interval).'),
    )
    lsp_mtu = models.PositiveIntegerField(
        verbose_name=_('LSP MTU'),
        blank=True,
        null=True,
        help_text=_('LSP MTU / lsp-mtu-size in bytes.'),
    )
    overload_on_startup = models.BooleanField(
        verbose_name=_('Overload on startup'),
        blank=True,
        null=True,
        help_text=_('Set the overload bit on startup (set-overload-bit on-startup).'),
    )
    overload_timeout = models.PositiveIntegerField(
        verbose_name=_('Overload timeout'),
        blank=True,
        null=True,
        help_text=_('Seconds to keep the overload bit set after startup.'),
    )
    suppress_attached_bit = models.BooleanField(
        verbose_name=_('Suppress attached bit'),
        blank=True,
        null=True,
        help_text=_(
            'Do not set the ATT (attached) bit in the L1 LSP even when attached '
            '(Cisco attached-bit send never / Nokia suppress-attached-bit).'
        ),
    )
    ignore_attached_bit = models.BooleanField(
        verbose_name=_('Ignore attached bit'),
        blank=True,
        null=True,
        help_text=_(
            'Ignore the ATT bit received from L1/L2 routers, installing no default '
            'route toward them (ignore-attached-bit).'
        ),
    )
    te_enabled = models.BooleanField(
        verbose_name=_('Traffic engineering'),
        blank=True,
        null=True,
        help_text=_('IS-IS traffic-engineering enabled.'),
    )
    fast_reroute = models.CharField(
        verbose_name=_('Fast reroute'),
        max_length=16,
        choices=choices.ISISFastRerouteChoices,
        blank=True,
        default='',
        help_text=_(
            'Process-wide IP fast-reroute computation (LFA, Remote-LFA or TI-LFA).'
        ),
    )
    microloop_avoidance = models.BooleanField(
        verbose_name=_('Micro-loop avoidance'),
        blank=True,
        null=True,
        help_text=_(
            'Delay post-convergence forwarding to avoid transient micro-loops.'
        ),
    )
    # Segment-routing global state (enable, SRGB/SRLB, MSD, SRv6 enable) lives on the
    # dedicated 1:1 ISISSegmentRouting child; per-prefix SIDs live on ISISPrefixSID
    # (per ISISInterface) and SRv6 locators on ISISSRv6Locator — not duplicated here.
    distance = models.PositiveSmallIntegerField(
        verbose_name=_('Administrative distance'),
        blank=True,
        null=True,
        help_text=_('Administrative distance / route preference.'),
    )
    maximum_paths = models.PositiveSmallIntegerField(
        verbose_name=_('Maximum paths'),
        blank=True,
        null=True,
        help_text=_('Maximum number of equal-cost paths (ECMP).'),
    )
    reference_bandwidth = models.PositiveBigIntegerField(
        verbose_name=_('Reference bandwidth'),
        blank=True,
        null=True,
        help_text=_('Auto-cost reference bandwidth (Mbps).'),
    )
    settings = GenericRelation(
        verbose_name=_('Settings'),
        to='netbox_routing_protocols.ISISSetting',
        related_name='isis_instance',
        related_query_name='isis_instance',
        content_type_field='assigned_object_type',
        object_id_field='assigned_object_id',
    )

    clone_fields = (
        'device',
        'vrf',
        'process_tag',
        'is_type',
        'metric_style',
        'spf_initial_wait',
        'spf_max_wait',
        'lsp_initial_wait',
        'lsp_max_wait',
        'lsp_lifetime',
        'lsp_refresh_interval',
        'lsp_mtu',
        'te_enabled',
        'distance',
        'maximum_paths',
        'reference_bandwidth',
    )
    prerequisite_models = ('dcim.Device',)

    class Meta:
        ordering = ['device', 'process_tag']
        verbose_name = 'IS-IS Instance'
        constraints = [
            models.UniqueConstraint(
                fields=('device', 'process_tag'),
                name='netbox_routing_protocols_isisinstance_device_process_tag_unique',
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        # An authentication type and its key are only meaningful together.
        for type_field, key_field in (
            ('area_auth_type', 'area_auth_key'),
            ('domain_auth_type', 'domain_auth_key'),
        ):
            errors.update(
                auth_pair_errors(
                    getattr(self, type_field),
                    getattr(self, key_field),
                    type_field,
                    key_field,
                )
            )
        # Reject a malformed NET at the model layer (form/API/import all run full_clean)
        # rather than letting it fail downstream when pushed to the device.
        if self.net and (message := net_error(self.net)):
            errors['net'] = message
        errors.update(self._range_errors())
        if errors:
            raise ValidationError(errors)
        self._clean_children()

    def _range_errors(self):
        """Limits of the timers and counters (ISO 10589 7.3, vendor documentation) and
        the pairs that must stay in order."""
        errors = range_errors(
            self,
            (
                ('lsp_lifetime', 1, 65535),
                ('lsp_refresh_interval', 1, 65535),
                ('lsp_mtu', 512, None),
                ('distance', 1, 255),
                ('maximum_paths', 1, None),
                ('reference_bandwidth', 1, None),
            ),
        )
        for low, high in (
            ('spf_initial_wait', 'spf_max_wait'),
            ('lsp_initial_wait', 'lsp_max_wait'),
        ):
            first, last = getattr(self, low), getattr(self, high)
            if first is not None and last is not None and first > last:
                errors[high] = _(
                    'The maximum wait cannot be less than the initial wait.'
                )
        if (
            self.lsp_refresh_interval is not None
            and self.lsp_lifetime is not None
            and self.lsp_refresh_interval >= self.lsp_lifetime
        ):
            errors['lsp_refresh_interval'] = _(
                'The refresh interval must be less than the LSP lifetime.'
            )
        if self.overload_timeout is not None and not self.overload_on_startup:
            errors['overload_timeout'] = _(
                'The overload timeout needs overload on startup.'
            )
        return errors

    def _clean_children(self):
        """A change of device, VRF, IS type or metric style must not leave interfaces
        or levels that the new values make invalid."""
        if self.pk is None:
            return
        problems = []
        children = [
            *self.interfaces.select_related('interface'),
            *self.levels.all(),
        ]
        for child in children:
            child.instance = self
            try:
                child.clean()
            except ValidationError as e:
                problems.append(f'{child} ({"; ".join(e.messages)})')
        if problems:
            raise ValidationError(
                _('This change makes related objects invalid: %(problems)s.')
                % {'problems': ', '.join(problems[:5])}
            )

    def __str__(self):
        tag = self.process_tag or 'default'
        return f'{self.device} ({tag})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isisinstance', args=[self.pk])


class ISISInterface(PrimaryModel):
    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.ISISInstance',
        related_name='interfaces',
        on_delete=models.PROTECT,
        blank=False,
        null=False,
    )
    interface = models.ForeignKey(
        verbose_name=_('Interface'),
        to='dcim.Interface',
        related_name='isis_interfaces',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    address_family = models.CharField(
        verbose_name=_('Address Family'),
        max_length=10,
        choices=choices.ISISAddressFamilyChoices,
    )
    circuit_type = models.CharField(
        verbose_name=_('Circuit Type'),
        max_length=20,
        choices=choices.ISISCircuitTypeChoices,
        blank=True,
        default='',
    )
    network_type = models.CharField(
        verbose_name=_('Network Type'),
        max_length=20,
        choices=choices.ISISNetworkTypeChoices,
        blank=True,
        default='',
    )
    metric = models.PositiveIntegerField(
        verbose_name=_('Metric'), blank=True, null=True
    )
    passive = models.BooleanField(verbose_name=_('Passive'), blank=True, null=True)
    hello_auth_type = models.CharField(
        verbose_name=_('Hello auth type'),
        max_length=16,
        choices=choices.ISISAuthTypeChoices,
        blank=True,
        default='',
        help_text=_(
            'IS-IS per-interface hello (IIH) authentication type (md5, text or an HMAC-SHA variant).'
        ),
    )
    hello_auth_key = models.CharField(
        verbose_name=_('Hello auth key'),
        max_length=128,
        blank=True,
        default='',
        help_text=_(
            'IS-IS per-interface hello (IIH) authentication key (plaintext — '
            'routing-protocol auth, not config access).'
        ),
    )
    frr_enabled = models.BooleanField(
        verbose_name=_('FRR enabled'),
        blank=True,
        null=True,
        help_text=_(
            'Fast-reroute backup computation on this interface (False = explicitly excluded).'
        ),
    )
    frr_protection = models.CharField(
        verbose_name=_('FRR protection'),
        max_length=8,
        choices=choices.ISISFrrProtectionChoices,
        blank=True,
        default='',
        help_text=_(
            'Requested repair coverage: link protection or node (node-link) protection.'
        ),
    )
    bfd_enabled = models.BooleanField(
        verbose_name=_('BFD enabled'),
        blank=True,
        null=True,
        help_text=_(
            'BFD enabled for IS-IS on this interface (timers come from the interface BFD config).'
        ),
    )
    csnp_interval = models.PositiveIntegerField(
        verbose_name=_('CSNP interval'),
        blank=True,
        null=True,
        help_text=_('Complete Sequence Number PDU interval in seconds.'),
    )
    retransmit_interval = models.PositiveIntegerField(
        verbose_name=_('Retransmit interval'),
        blank=True,
        null=True,
        help_text=_('LSP retransmission interval in seconds.'),
    )
    lsp_interval = models.PositiveIntegerField(
        verbose_name=_('LSP interval'),
        blank=True,
        null=True,
        help_text=_(
            'LSP transmission pacing interval in milliseconds '
            '(Nokia lsp-pacing-interval / Junos lsp-interval).'
        ),
    )
    mesh_group = models.CharField(
        verbose_name=_('Mesh group'),
        max_length=32,
        blank=True,
        default='',
        help_text=_("Mesh-group identifier, or 'blocked'."),
    )
    settings = GenericRelation(
        verbose_name=_('Settings'),
        to='netbox_routing_protocols.ISISSetting',
        related_name='isis_interface',
        related_query_name='isis_interface',
        content_type_field='assigned_object_type',
        object_id_field='assigned_object_id',
    )

    clone_fields = (
        'instance',
        'interface',
        'address_family',
        'circuit_type',
        'network_type',
        'metric',
        'passive',
        'bfd_enabled',
        'csnp_interval',
        'retransmit_interval',
        'lsp_interval',
        'mesh_group',
    )
    prerequisite_models = (
        'netbox_routing_protocols.ISISInstance',
        'dcim.Interface',
    )

    class Meta:
        verbose_name = 'IS-IS Interface'
        ordering = ('instance', 'interface', 'pk')
        constraints = [
            models.UniqueConstraint(
                fields=('interface', 'address_family'),
                name='netbox_routing_protocols_isisinterface_interface_af_unique',
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        # The interface and the IS-IS instance must live on the same device. Enforced
        # at the model layer so the form, API and bulk-import paths all get it; both
        # fields are flagged so the UI highlights the mismatch on either selector.
        if (
            self.instance_id
            and self.interface_id
            and self.instance.device != self.interface.device
        ):
            msg = _('IS-IS Instance Device and Interface Device must match.')
            errors['instance'] = msg
            errors['interface'] = msg
        elif (
            self.instance_id
            and self.interface_id
            and self.interface.vrf_id != self.instance.vrf_id
        ):
            errors['interface'] = _(
                'The interface is in {interface_vrf} but the IS-IS instance '
                'is in {instance_vrf}.'
            ).format(
                interface_vrf=self.interface.vrf or _('the global routing table'),
                instance_vrf=self.instance.vrf or _('the global routing table'),
            )
        errors.update(
            range_errors(
                self,
                (
                    ('csnp_interval', 1, 65535),
                    ('retransmit_interval', 1, 65535),
                    ('lsp_interval', 1, None),
                ),
            )
        )
        if self.instance_id:
            errors.update(metric_errors(self, ('metric',), self.instance.metric_style))
        # The circuit type must share a level with the IS type of the instance.
        if (
            self.instance_id
            and self.circuit_type
            and not type_levels(self.circuit_type) & type_levels(self.instance.is_type)
        ):
            errors['circuit_type'] = _(
                'The circuit type does not run any level of the instance IS type.'
            )
        # Hello auth type and key are only meaningful together (mirrors ISISInstance).
        errors.update(
            auth_pair_errors(
                self.hello_auth_type,
                self.hello_auth_key,
                'hello_auth_type',
                'hello_auth_key',
            )
        )
        if errors:
            raise ValidationError(errors)
        self._clean_levels()

    def _clean_levels(self):
        """Interface levels must be levels the circuit (or, by default, the instance) runs."""
        if self.pk is None or not self.instance_id:
            return
        allowed = type_levels(self.circuit_type) & type_levels(self.instance.is_type)
        bad = [str(lv.level) for lv in self.levels.all() if lv.level not in allowed]
        if bad:
            raise ValidationError(
                {
                    'circuit_type': _(
                        'Interface levels exist for levels this circuit does not run: %(levels)s.'
                    )
                    % {'levels': ', '.join(bad)}
                }
            )

    def __str__(self):
        return f'{self.interface} ({self.address_family})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isisinterface', args=[self.pk])


class ISISLevel(PrimaryModel):
    """Per-level (L1/L2) tuning of an IS-IS instance.

    IS-IS knobs like default-metric and wide-metrics-only are configured
    independently per level on Nokia, Junos and IOS-XR — a structured child
    table rather than flat instance columns.
    """

    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.ISISInstance',
        related_name='levels',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    level = models.PositiveSmallIntegerField(
        verbose_name=_('Level'),
        choices=choices.ISISLevelChoices,
    )
    default_metric = models.PositiveIntegerField(
        verbose_name=_('Default metric'), blank=True, null=True
    )
    wide_metrics_only = models.BooleanField(
        verbose_name=_('Wide metrics only'), blank=True, null=True
    )
    preference = models.PositiveSmallIntegerField(
        verbose_name=_('Preference'), blank=True, null=True
    )
    labeled_preference = models.PositiveSmallIntegerField(
        verbose_name=_('Labeled preference'),
        blank=True,
        null=True,
        help_text=_(
            'Route preference for SR-labeled (MPLS) paths at this level (Junos labeled-preference).'
        ),
    )
    disabled = models.BooleanField(
        verbose_name=_('Disabled'),
        blank=True,
        null=True,
        help_text=_(
            'Level explicitly disabled on this instance (e.g. Junos "level <n> disable").'
        ),
    )
    auth_type = models.CharField(
        verbose_name=_('Auth type'),
        max_length=16,
        choices=choices.ISISAuthTypeChoices,
        blank=True,
        default='',
        help_text=_(
            'Per-level authentication type (md5, text or an HMAC-SHA variant).'
        ),
    )
    auth_key = models.CharField(
        verbose_name=_('Auth key'),
        max_length=128,
        blank=True,
        default='',
        help_text=_(
            'Per-level authentication key (plaintext — routing-protocol auth, not config access).'
        ),
    )

    clone_fields = (
        'instance',
        'default_metric',
        'wide_metrics_only',
        'preference',
        'labeled_preference',
        'disabled',
    )
    prerequisite_models = ('netbox_routing_protocols.ISISInstance',)

    class Meta:
        verbose_name = 'IS-IS Level'
        ordering = ('instance', 'level')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'level'),
                name='netbox_routing_protocols_isislevel_instance_level_unique',
            ),
        ]

    def clean(self):
        super().clean()
        errors = auth_pair_errors(
            self.auth_type, self.auth_key, 'auth_type', 'auth_key'
        )
        if self.instance_id:
            if (
                self.level not in type_levels(self.instance.is_type)
                and not self.disabled
            ):
                errors['level'] = _(
                    'The instance IS type does not run this level; mark it disabled.'
                )
            errors.update(
                metric_errors(self, ('default_metric',), self.instance.metric_style)
            )
            if self.wide_metrics_only and self.instance.metric_style == 'narrow':
                errors['wide_metrics_only'] = _(
                    'Wide metrics only conflicts with the narrow metric style of the instance.'
                )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.instance} L{self.level}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isislevel', args=[self.pk])


class ISISInterfaceLevel(PrimaryModel):
    """Per-level (L1/L2) tuning of an IS-IS interface.

    hello-interval, hello-multiplier, metric and priority are per-Level on
    Nokia, Junos and IOS-XR (interface.level[n]).
    """

    interface = models.ForeignKey(
        verbose_name=_('Interface'),
        to='netbox_routing_protocols.ISISInterface',
        related_name='levels',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    level = models.PositiveSmallIntegerField(
        verbose_name=_('Level'),
        choices=choices.ISISLevelChoices,
    )
    metric = models.PositiveIntegerField(
        verbose_name=_('Metric'), blank=True, null=True
    )
    hello_interval = models.PositiveIntegerField(
        verbose_name=_('Hello interval'), blank=True, null=True
    )
    hello_multiplier = models.PositiveIntegerField(
        verbose_name=_('Hello multiplier'), blank=True, null=True
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name=_('Priority'), blank=True, null=True
    )
    passive = models.BooleanField(verbose_name=_('Passive'), blank=True, null=True)

    clone_fields = (
        'interface',
        'metric',
        'hello_interval',
        'hello_multiplier',
        'priority',
    )
    prerequisite_models = ('netbox_routing_protocols.ISISInterface',)

    class Meta:
        verbose_name = 'IS-IS Interface Level'
        ordering = ('interface', 'level')
        constraints = [
            models.UniqueConstraint(
                fields=('interface', 'level'),
                name='netbox_routing_protocols_isisinterfacelevel_interface_level_unique',
            ),
        ]

    def clean(self):
        super().clean()
        errors = range_errors(
            self,
            (
                ('hello_interval', 1, 65535),
                ('hello_multiplier', 2, 1000),
                ('priority', 0, 127),
            ),
        )
        if self.interface_id:
            instance = self.interface.instance
            errors.update(metric_errors(self, ('metric',), instance.metric_style))
            allowed = type_levels(self.interface.circuit_type) & type_levels(
                instance.is_type
            )
            if self.level not in allowed:
                errors['level'] = _(
                    'The circuit of this interface does not run this level.'
                )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.interface} L{self.level}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:isisinterfacelevel', args=[self.pk]
        )


class ISISSegmentRouting(PrimaryModel):
    """Segment Routing (SR-MPLS) configuration of an IS-IS instance (1:1)."""

    instance = models.OneToOneField(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.ISISInstance',
        related_name='segment_routing',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    enabled = models.BooleanField(
        verbose_name=_('Enabled'),
        blank=True,
        null=True,
        help_text=_('SR-MPLS enabled for this IS-IS instance.'),
    )
    srv6_enabled = models.BooleanField(
        verbose_name=_('SRv6 enabled'),
        blank=True,
        null=True,
        help_text=_(
            'SRv6 enabled for this IS-IS instance (locators are modelled separately).'
        ),
    )
    prefix_sid_range = models.CharField(
        verbose_name=_('Prefix-SID range'),
        max_length=32,
        blank=True,
        default='',
        help_text=_("Prefix-SID range: 'global' or a named/explicit range."),
    )
    srgb_start = models.PositiveIntegerField(
        verbose_name=_('SRGB start label'), blank=True, null=True
    )
    srgb_range = models.PositiveIntegerField(
        verbose_name=_('SRGB range size'), blank=True, null=True
    )
    srlb_start = models.PositiveIntegerField(
        verbose_name=_('SRLB start label'),
        blank=True,
        null=True,
        help_text=_('SR Local Block start label (local/adjacency/binding SIDs).'),
    )
    srlb_range = models.PositiveIntegerField(
        verbose_name=_('SRLB range size'), blank=True, null=True
    )
    maximum_sid_depth = models.PositiveSmallIntegerField(
        verbose_name=_('Maximum SID depth'), blank=True, null=True
    )
    tunnel_table_pref = models.PositiveSmallIntegerField(
        verbose_name=_('Tunnel-table preference'), blank=True, null=True
    )

    clone_fields = (
        'enabled',
        'srv6_enabled',
        'prefix_sid_range',
        'srgb_start',
        'srgb_range',
    )
    prerequisite_models = ('netbox_routing_protocols.ISISInstance',)

    class Meta:
        verbose_name = 'IS-IS Segment Routing'
        verbose_name_plural = 'IS-IS Segment Routing'
        ordering = ('instance',)

    def clean(self):
        super().clean()
        errors = {}
        # An SRGB / SRLB block is a (start, range) pair — a lone bound is meaningless.
        for start_field, range_field, label in (
            ('srgb_start', 'srgb_range', 'SRGB'),
            ('srlb_start', 'srlb_range', 'SRLB'),
        ):
            start, size = getattr(self, start_field), getattr(self, range_field)
            if (start is None) != (size is None):
                missing = range_field if start is not None else start_field
                errors[missing] = _(
                    '%(block)s start and range must be set together.'
                ) % {'block': label}
        blocks = []
        for start_field, range_field, label in (
            ('srgb_start', 'srgb_range', 'SRGB'),
            ('srlb_start', 'srlb_range', 'SRLB'),
        ):
            start, size = getattr(self, start_field), getattr(self, range_field)
            if start is None or size is None:
                continue
            if start < SR_MIN_LABEL or size < 1 or start + size - 1 > SR_MAX_LABEL:
                errors[start_field] = _(
                    '%(block)s labels must be within %(min)s-%(max)s (20 bits, labels 0-15 are reserved).'
                ) % {'block': label, 'min': SR_MIN_LABEL, 'max': SR_MAX_LABEL}
            else:
                blocks.append((start, start + size - 1))
        if len(blocks) == 2 and not (
            blocks[0][1] < blocks[1][0] or blocks[1][1] < blocks[0][0]
        ):
            errors['srlb_start'] = _('The SRGB and the SRLB cannot overlap.')
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.instance} (SR)'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:isissegmentrouting', args=[self.pk]
        )


class ISISFlexAlgo(PrimaryModel):
    """A flexible-algorithm (Flex-Algo) definition used by an IS-IS instance.

    On Junos the definition lives under routing-options/flex-algorithm and the
    IS-IS instance participates via source-packet-routing/flex-algorithm; on
    Nokia it sits under isis/segment-routing/flexible-algorithms. Modeled here
    per (instance, algo_id) with the common definition knobs.
    """

    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.ISISInstance',
        related_name='flex_algos',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    algo_id = models.PositiveSmallIntegerField(
        verbose_name=_('Algorithm ID'),
        validators=[MinValueValidator(128), MaxValueValidator(255)],
        help_text=_('Flex-Algo identifier (128-255).'),
    )
    metric_type = models.CharField(
        verbose_name=_('Metric type'),
        max_length=40,
        choices=choices.ISISFlexAlgoMetricTypeChoices,
        blank=True,
        default='',
        help_text=_(
            'Flex-Algo metric type (RFC 9350): IGP, minimum delay or TE metric.'
        ),
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name=_('Priority'), blank=True, null=True
    )
    admin_group_exclude = models.CharField(
        verbose_name=_('Admin-group exclude'),
        max_length=200,
        blank=True,
        default='',
        help_text=_(
            'Comma-separated affinity/admin-group names excluded from this algo.'
        ),
    )
    admin_group_include_any = models.CharField(
        verbose_name=_('Admin-group include-any'),
        max_length=200,
        blank=True,
        default='',
        help_text=_('Comma-separated affinity/admin-group names (include-any).'),
    )
    admin_group_include_all = models.CharField(
        verbose_name=_('Admin-group include-all'),
        max_length=200,
        blank=True,
        default='',
        help_text=_('Comma-separated affinity/admin-group names (include-all).'),
    )

    clone_fields = ('instance', 'metric_type', 'priority')
    prerequisite_models = ('netbox_routing_protocols.ISISInstance',)

    class Meta:
        verbose_name = 'IS-IS Flex-Algo'
        ordering = ('instance', 'algo_id')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'algo_id'),
                name='netbox_routing_protocols_isisflexalgo_instance_algo_id_unique',
            ),
            models.CheckConstraint(
                condition=models.Q(algo_id__gte=128, algo_id__lte=255),
                name='netbox_routing_protocols_isisflexalgo_algo_id_range',
            ),
        ]

    def clean(self):
        super().clean()
        errors = range_errors(self, (('priority', 0, 255),))
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.instance} flex-algo {self.algo_id}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isisflexalgo', args=[self.pk])


class ISISPrefixSID(PrimaryModel):
    """A per-prefix SR-MPLS prefix-SID (node-SID) advertised for an IS-IS interface.

    Attaches to the loopback's ISISInterface (which already fixes the address
    family via its unique (interface, address_family)); keyed per algorithm so a
    prefix can carry a base (algo 0) SID plus one per Flex-Algo. The value is
    either an index into the SRGB or an absolute label (mutually exclusive).
    """

    interface = models.ForeignKey(
        verbose_name=_('Interface'),
        to='netbox_routing_protocols.ISISInterface',
        related_name='prefix_sids',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    algorithm = models.PositiveSmallIntegerField(
        verbose_name=_('Algorithm'),
        default=0,
        help_text=_('SR algorithm: 0 (SPF) or a Flex-Algo (128-255).'),
    )
    sid_index = models.PositiveIntegerField(
        verbose_name=_('SID index'),
        blank=True,
        null=True,
        help_text=_(
            'Prefix-SID index into the SRGB (mutually exclusive with an absolute label).'
        ),
    )
    sid_label = models.PositiveIntegerField(
        verbose_name=_('SID label'),
        blank=True,
        null=True,
        help_text=_('Absolute prefix-SID label (mutually exclusive with an index).'),
    )
    n_flag = models.BooleanField(
        verbose_name=_('Node (N) flag'),
        blank=True,
        null=True,
        help_text=_(
            'Node-SID flag — the prefix-SID identifies a single node (a /32 or /128 loopback).'
        ),
    )
    no_php = models.BooleanField(
        verbose_name=_('No-PHP (P) flag'),
        blank=True,
        null=True,
        help_text=_('Disable penultimate-hop-popping for this prefix-SID.'),
    )
    explicit_null = models.BooleanField(
        verbose_name=_('Explicit-null (E) flag'),
        blank=True,
        null=True,
        help_text=_('Request explicit-null instead of PHP for this prefix-SID.'),
    )
    readvertise = models.BooleanField(
        verbose_name=_('Re-advertise (R) flag'),
        blank=True,
        null=True,
        help_text=_(
            'Prefix-SID is re-advertised (redistributed/leaked) from another level or protocol.'
        ),
    )

    clone_fields = ('interface', 'algorithm', 'n_flag', 'no_php', 'explicit_null')
    prerequisite_models = ('netbox_routing_protocols.ISISInterface',)

    class Meta:
        verbose_name = 'IS-IS Prefix-SID'
        ordering = ('interface', 'algorithm')
        constraints = [
            models.UniqueConstraint(
                fields=('interface', 'algorithm'),
                name='netbox_routing_protocols_isisprefixsid_interface_algorithm_unique',
            ),
            models.CheckConstraint(
                condition=models.Q(algorithm=0)
                | models.Q(algorithm__gte=128, algorithm__lte=255),
                name='netbox_routing_protocols_isisprefixsid_algorithm_range',
            ),
        ]

    def clean(self):
        super().clean()
        # algorithm is 0 (SPF) or a Flex-Algo in 128-255; the 1-127 gap (and any
        # value above 255) is invalid. Validate here so a bad value raises a
        # ValidationError (HTTP 400) instead of tripping the CheckConstraint at
        # save() as an IntegrityError (HTTP 500). Mirrors ISISFlexAlgo.algo_id.
        if (
            self.algorithm is not None
            and self.algorithm != 0
            and not (128 <= self.algorithm <= 255)
        ):
            raise ValidationError(
                {
                    'algorithm': _(
                        'Algorithm must be 0 (SPF) or a Flex-Algo value in 128-255.'
                    )
                }
            )
        # A prefix-SID is expressed as an SRGB index OR an absolute label, never both.
        if self.sid_index is not None and self.sid_label is not None:
            msg = _(
                'A prefix-SID takes either an index or an absolute label, not both.'
            )
            raise ValidationError({'sid_index': msg, 'sid_label': msg})
        errors = {}
        if self.no_php and self.explicit_null:
            msg = _(
                'The no-PHP (P) and explicit-null (E) flags cannot be set together: '
                'explicit-null already keeps the label (RFC 8667).'
            )
            errors['no_php'] = errors['explicit_null'] = msg
        errors.update(range_errors(self, (('sid_label', SR_MIN_LABEL, SR_MAX_LABEL),)))
        errors.update(range_errors(self, (('sid_index', 0, SR_MAX_LABEL),)))
        if self.interface_id:
            instance = self.interface.instance
            if (
                self.algorithm
                and 'algorithm' not in errors
                and not instance.flex_algos.filter(algo_id=self.algorithm).exists()
            ):
                errors['algorithm'] = _('The instance has no Flex-Algo %(algo)s.') % {
                    'algo': self.algorithm
                }
            sr = getattr(instance, 'segment_routing', None)
            if (
                self.sid_index is not None
                and sr is not None
                and sr.srgb_range
                and self.sid_index >= sr.srgb_range
            ):
                errors['sid_index'] = _(
                    'The index is outside the SRGB (range size %(size)s).'
                ) % {'size': sr.srgb_range}
            if self.n_flag and self._has_only_wide_prefixes():
                errors['n_flag'] = _(
                    'The node flag needs a host prefix (/32 or /128) on the interface.'
                )
        if errors:
            raise ValidationError(errors)

    def _has_only_wide_prefixes(self):
        """The interface has addresses of the family and none of them is a host prefix."""
        version = 4 if self.interface.address_family == 'ipv4' else 6
        host = 32 if version == 4 else 128
        masks = [
            address.address.prefixlen
            for address in self.interface.interface.ip_addresses.all()
            if address.address.version == version
        ]
        return bool(masks) and all(mask != host for mask in masks)

    def __str__(self):
        return f'{self.interface} SID (algo {self.algorithm})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:isisprefixsid', args=[self.pk])


class ISISSRv6Locator(PrimaryModel):
    """An SRv6 locator advertised by an IS-IS instance (RFC 8986 LOC = Block:Node).

    Locators are defined per instance on both vendors but in different config
    trees (IOS-XR under segment-routing/srv6, Junos under routing-options); the
    neutral shape here keeps the common attributes as columns and stashes
    no-cross-vendor-analogue leaves in ``vendor_ext``. The SID-structure lengths
    are derivable and left null unless a device reports non-default structure.
    """

    instance = models.ForeignKey(
        verbose_name=_('Instance'),
        to='netbox_routing_protocols.ISISInstance',
        related_name='srv6_locators',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    name = models.CharField(verbose_name=_('Name'), max_length=64)
    prefix = IPNetworkField(
        verbose_name=_('Prefix'),
        help_text=_('IPv6 locator prefix (RFC 8986 LOC = Block:Node).'),
    )
    algorithm = models.PositiveSmallIntegerField(
        verbose_name=_('Algorithm'),
        blank=True,
        null=True,
        help_text=_(
            'SR algorithm bound to the locator (0 = SPF, 128-255 = Flex-Algo).'
        ),
    )
    is_anycast = models.BooleanField(
        verbose_name=_('Anycast'),
        blank=True,
        null=True,
        help_text=_(
            'Anycast locator shared by several nodes (sets the prefix-attribute A-flag).'
        ),
    )
    is_micro_segment = models.BooleanField(
        verbose_name=_('Micro-segment (uSID)'),
        blank=True,
        null=True,
        help_text=_(
            'uSID / micro-segment locator (XR micro-segment behavior, Junos micro-sid).'
        ),
    )
    flavor = models.CharField(
        verbose_name=_('Flavor'),
        max_length=64,
        blank=True,
        default='',
        help_text=_(
            'END-SID behaviour flavor(s) as reported, e.g. "psp usd" (Junos set) or "psp-usd" (XR).'
        ),
    )
    block_length = models.PositiveSmallIntegerField(
        verbose_name=_('Block length'),
        blank=True,
        null=True,
        help_text=_(
            'Locator-Block length in bits (RFC 8986 B); null = derive from prefix.'
        ),
    )
    node_length = models.PositiveSmallIntegerField(
        verbose_name=_('Node length'),
        blank=True,
        null=True,
        help_text=_(
            'Locator-Node length in bits (RFC 8986 N); null = derive from prefix.'
        ),
    )
    function_length = models.PositiveSmallIntegerField(
        verbose_name=_('Function length'),
        blank=True,
        null=True,
        help_text=_('Function length in bits (RFC 8986 F); null = vendor default.'),
    )
    argument_length = models.PositiveSmallIntegerField(
        verbose_name=_('Argument length'),
        blank=True,
        null=True,
        help_text=_('Argument length in bits (RFC 8986 A); null = none.'),
    )
    isis_level = models.PositiveSmallIntegerField(
        verbose_name=_('IS-IS level'),
        choices=choices.ISISLevelChoices,
        blank=True,
        null=True,
        help_text=_(
            'Advertise the locator in this level only (IOS-XR); null = both levels.'
        ),
    )
    enabled = models.BooleanField(
        verbose_name=_('Enabled'),
        blank=True,
        null=True,
        help_text=_('Locator is attached/advertised by the IS-IS instance.'),
    )
    vendor_ext = models.JSONField(
        verbose_name=_('Vendor extensions'),
        blank=True,
        default=dict,
        help_text=_(
            'No-cross-vendor-analogue leaves (Junos end-sid/block sizing, XR uSID carrier format).'
        ),
    )

    clone_fields = (
        'instance',
        'algorithm',
        'is_micro_segment',
        'flavor',
        'block_length',
        'node_length',
    )
    prerequisite_models = ('netbox_routing_protocols.ISISInstance',)

    class Meta:
        verbose_name = 'IS-IS SRv6 Locator'
        ordering = ('instance', 'name')
        constraints = [
            models.UniqueConstraint(
                fields=('instance', 'name'),
                name='netbox_routing_protocols_isissrv6locator_instance_name_unique',
            ),
            models.CheckConstraint(
                condition=models.Q(algorithm=0)
                | models.Q(algorithm__gte=128, algorithm__lte=255)
                | models.Q(algorithm__isnull=True),
                name='netbox_routing_protocols_isissrv6locator_algorithm_range',
            ),
        ]

    def clean(self):
        super().clean()
        # algorithm is 0 (SPF) or a Flex-Algo in 128-255; reject the 1-127 gap (and
        # >255) at clean() so the API/UI return a 400 instead of tripping the DB
        # CheckConstraint. Mirrors ISISPrefixSID.
        if (
            self.algorithm is not None
            and self.algorithm != 0
            and not (128 <= self.algorithm <= 255)
        ):
            raise ValidationError(
                {
                    'algorithm': _(
                        'Algorithm must be 0 (SPF) or a Flex-Algo value in 128-255.'
                    )
                }
            )
        if self.prefix:
            network = netaddr.IPNetwork(str(self.prefix))
            if network.version != 6:
                raise ValidationError(
                    {'prefix': _('An SRv6 locator is an IPv6 prefix.')}
                )
            if (
                self.block_length is not None
                and self.node_length is not None
                and self.block_length + self.node_length != network.prefixlen
            ):
                raise ValidationError(
                    {
                        'prefix': _(
                            'The locator prefix length must equal block + node length '
                            '(RFC 8986).'
                        )
                    }
                )
        if (
            self.algorithm
            and self.instance_id
            and 128 <= self.algorithm <= 255
            and not self.instance.flex_algos.filter(algo_id=self.algorithm).exists()
        ):
            raise ValidationError(
                {
                    'algorithm': _('The instance has no Flex-Algo %(algo)s.')
                    % {'algo': self.algorithm}
                }
            )
        # RFC 8986: L + F + A <= 128 (L = block + node). Validate only when the
        # relevant lengths are pinned; otherwise the device derives them. When
        # block and node are both unpinned the locator length is the prefix length,
        # so use prefix.prefixlen rather than falling back to 0 (else an oversized
        # derived locator, e.g. /120 + 16-bit function, would slip through).
        if self.block_length is None and self.node_length is None:
            loc = netaddr.IPNetwork(str(self.prefix)).prefixlen if self.prefix else 0
        else:
            loc = (self.block_length or 0) + (self.node_length or 0)
        total = loc + (self.function_length or 0) + (self.argument_length or 0)
        if (
            any(
                v is not None
                for v in (
                    self.block_length,
                    self.node_length,
                    self.function_length,
                    self.argument_length,
                )
            )
            and total > 128
        ):
            raise ValidationError(
                _(
                    'SID structure exceeds 128 bits: block + node + function + argument must be <= 128.'
                )
            )

    def __str__(self):
        return f'{self.instance} SRv6 {self.name}'

    def get_absolute_url(self):
        return reverse(
            'plugins:netbox_routing_protocols:isissrv6locator', args=[self.pk]
        )
