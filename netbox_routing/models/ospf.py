import netaddr
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel

from netbox_routing import choices
from netbox_routing.choices.ospf import (
    OSPFAreaTypeChoices,
    OSPFExternalMetricTypeChoices,
    OSPFRedistributionProtocolChoices,
)
from netbox_routing.constants import ERROR_UNIQUENESS_CONSTRAINT
from netbox_routing.constants.ospf import (
    OSPF_COST_MAX,
    OSPF_COST_MIN,
    OSPF_EXTERNAL_METRIC_MAX,
    OSPF_EXTERNAL_METRIC_MIN,
    OSPF_INTERFACE_TIMERS,
    OSPF_STUB_DEFAULT_COST_MAX,
    OSPF_STUB_DEFAULT_COST_MIN,
    OSPF_TAG_MAX,
)
from netbox_routing.fields.ip import IPAddressField

__all__ = (
    'OSPFInstance',
    'OSPFArea',
    'OSPFInterface',
    'OSPFNetwork',
    'OSPFRedistribution',
)


class OSPFInstance(PrimaryModel):
    name = models.CharField(max_length=100)
    router_id = IPAddressField(verbose_name=_('Router ID'))
    process_id = models.IntegerField(verbose_name=_('Process ID'))
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
    default_originate = models.BooleanField(
        verbose_name=_('Default Originate'),
        help_text=_(
            'Originate a default route (0.0.0.0/0) into OSPF. '
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

    clone_fields = (
        'name',
        'router_id',
        'process_id',
        'device',
        'vrf',
        'default_originate',
        'default_originate_always',
        'default_originate_metric',
        'default_originate_metric_type',
    )
    prerequisite_models = ('dcim.Device',)

    class Meta:
        ordering = ['vrf', 'router_id', 'process_id', 'pk']
        verbose_name = 'OSPF Instance'
        constraints = (
            models.UniqueConstraint(
                fields=('device', 'name'),
                name='%(app_label)s_%(class)s_unique_device_name',
                violation_error_message=ERROR_UNIQUENESS_CONSTRAINT,
                nulls_distinct=False,
            ),
        )

    def __str__(self):
        return f'{self.name} ({self.router_id})'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing:ospfinstance', args=[self.pk])

    def clean(self):
        super().clean()
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


class OSPFArea(PrimaryModel):
    instance = models.ForeignKey(
        to='netbox_routing.OSPFInstance',
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
    prerequisite_models = ('netbox_routing.OSPFInstance',)
    clone_fields = (
        'instance',
        'area_id',
        'area_type',
        'default_cost',
        'nssa_translate_always',
        'nssa_no_redistribution',
        'nssa_default_originate',
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
        return f'{self.area_id}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing:ospfarea', args=[self.pk])

    def clean(self):
        super().clean()
        self._clean_area_type_options()
        area_id = self.area_id
        try:
            int(area_id)
        except ValueError:
            try:
                str(netaddr.IPAddress(area_id))
            except netaddr.core.AddrFormatError:
                raise ValidationError(
                    {
                        'area_id': [
                            'This field must be an integer or a valid net address'
                        ]
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


class OSPFInterface(PrimaryModel):
    instance = models.ForeignKey(
        to='netbox_routing.OSPFInstance',
        related_name='interfaces',
        on_delete=models.RESTRICT,
        blank=False,
        null=False,
    )
    area = models.ForeignKey(
        to='netbox_routing.OSPFArea',
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
    priority = models.IntegerField(blank=True, null=True)
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
    hello_interval = models.PositiveIntegerField(
        verbose_name=_('Hello Interval'),
        help_text=_('Seconds between Hello packets (RFC 2328 default: 10)'),
        default=OSPF_INTERFACE_TIMERS['hello_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['hello_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['hello_interval'][1]),
        ],
    )
    dead_interval = models.PositiveBigIntegerField(
        verbose_name=_('Dead Interval'),
        help_text=_(
            'Seconds without Hello packets before a neighbor is declared down (RFC 2328 default: 40)'
        ),
        default=OSPF_INTERFACE_TIMERS['dead_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['dead_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['dead_interval'][1]),
        ],
    )
    retransmit_interval = models.PositiveIntegerField(
        verbose_name=_('Retransmit Interval'),
        help_text=_('Seconds between LSA retransmissions (RFC 2328 default: 5)'),
        default=OSPF_INTERFACE_TIMERS['retransmit_interval'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['retransmit_interval'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['retransmit_interval'][1]),
        ],
    )
    transmit_delay = models.PositiveIntegerField(
        verbose_name=_('Transmit Delay'),
        help_text=_('Estimated seconds to transmit an LSA (RFC 2328 default: 1)'),
        default=OSPF_INTERFACE_TIMERS['transmit_delay'][2],
        validators=[
            MinValueValidator(OSPF_INTERFACE_TIMERS['transmit_delay'][0]),
            MaxValueValidator(OSPF_INTERFACE_TIMERS['transmit_delay'][1]),
        ],
    )
    mtu_ignore = models.BooleanField(
        verbose_name=_('MTU Ignore'),
        help_text=_(
            'Ignore the MTU mismatch check when forming adjacencies. '
            'The MTU itself comes from the device interface.'
        ),
        default=False,
    )
    authentication = models.CharField(
        max_length=50, choices=choices.AuthenticationChoices, blank=True, null=True
    )
    passphrase = models.CharField(max_length=200, blank=True, null=True)

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
        'authentication',
        'passphrase',
    )
    prerequisite_models = (
        'netbox_routing.OSPFInstance',
        'netbox_routing.OSPFArea',
        'dcim.Interface',
    )

    class Meta:
        verbose_name = 'OSPF Interface'
        ordering = ('instance', 'area', 'interface')  # Name may be non-unique

    def __str__(self):
        return f'{self.interface.name}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing:ospfinterface', args=[self.pk])

    def clean(self):
        super().clean()
        if (
            self.instance_id
            and self.area_id
            and self.area.instance_id != self.instance_id
        ):
            raise ValidationError(
                {'area': _('The area must belong to the OSPF instance.')}
            )
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


class OSPFNetwork(PrimaryModel):
    """
    A `network` statement of an OSPF interface: a reference to the IP address
    (and therefore the subnet) configured on that interface. The statement
    itself is not computed here.
    """

    ospf_interface = models.ForeignKey(
        to='netbox_routing.OSPFInterface',
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
        'netbox_routing.OSPFInterface',
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
        return reverse('plugins:netbox_routing:ospfnetwork', args=[self.pk])

    @property
    def subnet(self):
        return netaddr.IPNetwork(str(self.ip_address.address)).cidr

    def clean(self):
        super().clean()
        if not (self.ospf_interface_id and self.ip_address_id):
            return
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
    Redistribution of routes learned from another protocol of the plugin into
    an OSPF instance. Static routes have no source; for every other protocol
    the source is the process that routes are taken from.
    """

    SOURCE_FIELDS = {
        OSPFRedistributionProtocolChoices.OSPF: 'ospf_source',
        OSPFRedistributionProtocolChoices.EIGRP: 'eigrp_source',
        OSPFRedistributionProtocolChoices.BGP: 'bgp_source',
        OSPFRedistributionProtocolChoices.ISIS: 'isis_source',
    }

    instance = models.ForeignKey(
        to='netbox_routing.OSPFInstance',
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
        to='netbox_routing.OSPFInstance',
        related_name='ospf_redistributed_into',
        on_delete=models.CASCADE,
        verbose_name=_('OSPF Source'),
        blank=True,
        null=True,
    )
    eigrp_source = models.ForeignKey(
        to='netbox_routing.EIGRPRouter',
        related_name='ospf_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('EIGRP Source'),
        blank=True,
        null=True,
    )
    bgp_source = models.ForeignKey(
        to='netbox_routing.BGPRouter',
        related_name='ospf_redistributions',
        on_delete=models.CASCADE,
        verbose_name=_('BGP Source'),
        blank=True,
        null=True,
    )
    isis_source = models.ForeignKey(
        to='netbox_routing.ISISInstance',
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
    route_policy = models.CharField(
        verbose_name=_('Route Policy'),
        help_text=_('Name of the route policy applied to the redistributed routes'),
        max_length=100,
        blank=True,
    )

    clone_fields = (
        'instance',
        'protocol',
        'metric',
        'metric_type',
        'subnets',
        'route_tag',
        'route_policy',
    )
    prerequisite_models = ('netbox_routing.OSPFInstance',)

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
        return reverse('plugins:netbox_routing:ospfredistribution', args=[self.pk])

    @property
    def source(self):
        field = self.SOURCE_FIELDS.get(self.protocol)
        return getattr(self, field) if field else None

    def clean(self):
        super().clean()
        errors = {}
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
        if not self._source_is_on_instance_device():
            raise ValidationError(
                {
                    self.SOURCE_FIELDS[self.protocol]: _(
                        'The source must be on the same device as the OSPF instance.'
                    )
                }
            )

    def _source_is_on_instance_device(self):
        source = self.source
        if self.protocol == OSPFRedistributionProtocolChoices.BGP:
            # A BGP router is assigned to a generic object (device, site, ...)
            device = self.instance.device
            return (
                source.assigned_object_type_id
                == ContentType.objects.get_for_model(device).pk
                and source.assigned_object_id == device.pk
            )
        return source.device_id == self.instance.device_id
