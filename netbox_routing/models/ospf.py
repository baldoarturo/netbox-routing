import netaddr
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
)
from netbox_routing.constants import ERROR_UNIQUENESS_CONSTRAINT
from netbox_routing.constants.ospf import (
    OSPF_COST_MAX,
    OSPF_COST_MIN,
    OSPF_EXTERNAL_METRIC_MAX,
    OSPF_EXTERNAL_METRIC_MIN,
    OSPF_INTERFACE_TIMERS,
)
from netbox_routing.fields.ip import IPAddressField

__all__ = (
    'OSPFInstance',
    'OSPFArea',
    'OSPFInterface',
    'OSPFNetwork',
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
    area_id = models.CharField(max_length=100, verbose_name='Area ID')
    area_type = models.CharField(
        verbose_name=_('Area Type'),
        choices=OSPFAreaTypeChoices,
        blank=False,
        null=False,
        default='standard',
    )
    prerequisite_models = ()
    clone_fields = ('area_id', 'area_type')

    class Meta:
        ordering = ['area_id', 'pk']
        verbose_name = 'OSPF Area'
        constraints = (
            models.UniqueConstraint(
                fields=('area_id',),
                name='%(app_label)s_%(class)s_unique_area_id',
                violation_error_message=ERROR_UNIQUENESS_CONSTRAINT,
            ),
        )

    def __str__(self):
        return f'{self.area_id}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing:ospfarea', args=[self.pk])

    def clean(self):
        super().clean()
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
        on_delete=models.CASCADE,
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
