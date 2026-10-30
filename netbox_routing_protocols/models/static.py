from django.core.validators import MaxValueValidator, MinValueValidator
import netaddr
from django.db import models
from django.db.models import CheckConstraint, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from dcim.models import Device
from ipam.fields import IPNetworkField
from netbox.models import PrimaryModel
from netbox_routing_protocols.fields.ip import IPAddressField

__all__ = ('StaticRoute',)


class StaticRoute(PrimaryModel):
    devices = models.ManyToManyField(to='dcim.Device', related_name='static_routes')
    vrf = models.ForeignKey(
        to='ipam.VRF',
        on_delete=models.PROTECT,
        related_name='staticroutes',
        blank=True,
        null=True,
        verbose_name='VRF',
    )
    prefix = IPNetworkField(
        help_text=_('IPv4 or IPv6 network with mask'),
    )
    next_hop = IPAddressField(
        verbose_name=_('Next Hop'),
        blank=True,
        null=True,
    )
    interface_next_hop = models.CharField(
        max_length=100,
        verbose_name='Interface Next Hop',
        help_text='Forwarding interface, for routes without IP address as next hop',
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Name',
        blank=True,
        default='',
        help_text='Optional name for this static route',
    )
    distance = models.PositiveSmallIntegerField(
        verbose_name=_('Distance'),
        help_text=_(
            'Administrative distance (Junos: preference, RFC 8349: route-preference). '
            'Lower wins; 1-255, default 1'
        ),
        validators=[MinValueValidator(1), MaxValueValidator(255)],
        blank=True,
        default=1,
    )
    permanent = models.BooleanField(
        verbose_name=_('Permanent'),
        default=False,
    )

    tag = models.PositiveBigIntegerField(
        verbose_name='Route Tag',
        help_text='Optional tag for this static route (0-4294967295)',
        validators=[MaxValueValidator(4294967295)],
        blank=True,
        null=True,
    )

    clone_fields = (
        'name',
        'devices',
        'prefix',
        'next_hop',
        'interface_next_hop',
        'vrf',
        'distance',
        'tag',
        'permanent',
    )

    prerequisite_models = ('dcim.Device',)

    class Meta:
        ordering = ['vrf', 'prefix', 'distance', 'pk']
        constraints = (
            CheckConstraint(
                condition=Q(distance__lte=255) & Q(distance__gte=1),
                name='staticroute_distance_1_255',
            ),
        )

    def __str__(self):
        name = [
            f'{self.prefix}',
        ]
        if self.vrf:
            name.append(f'VRF: {self.vrf}')
        if self.next_hop or self.interface_next_hop:
            name.append('via')
            if self.next_hop:
                name.append(f'{self.next_hop}')
            if self.interface_next_hop:
                name.append(f'{self.interface_next_hop}')
        return ' '.join(name)

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_protocols:staticroute', args=[self.pk])

    def clean(self):
        super().clean()
        errors = {}
        if not self.interface_next_hop and not self.next_hop:
            errors['next_hop'] = _(
                "A route requires set either an IP next hop or an Interface next hop."
            )
        prefix = netaddr.IPNetwork(str(self.prefix)) if self.prefix else None
        if prefix is not None and prefix.ip != prefix.network:
            errors['prefix'] = _(
                'The prefix has host bits set, use {network} instead.'
            ).format(network=prefix.cidr)
        if self.next_hop:
            nh = netaddr.IPAddress(str(self.next_hop))
            if prefix is not None and nh.version != prefix.version:
                errors['next_hop'] = _(
                    'The next hop must be an IPv{version} address, like the prefix.'
                ).format(version=prefix.version)
            elif int(nh) == 0 or nh.is_multicast() or nh.is_loopback():
                errors['next_hop'] = _(
                    'The next hop must be a usable unicast address (not unspecified, loopback or multicast).'
                )
            elif nh.version == 6 and nh.is_link_local() and not self.interface_next_hop:
                errors['interface_next_hop'] = _(
                    'A link-local next hop is only meaningful on a link: '
                    'set the interface next hop (RFC 4291, RFC 4861).'
                )
        if errors:
            raise ValidationError(errors)

    def duplicates_on(self, devices):
        """
        Devices among `devices` that already carry another route with the same
        VRF, prefix, next hop and interface next hop.
        """
        routes = StaticRoute.objects.filter(
            vrf=self.vrf, prefix=self.prefix, next_hop=self.next_hop
        ).exclude(pk=self.pk)
        if self.interface_next_hop:
            routes = routes.filter(interface_next_hop=self.interface_next_hop)
        else:
            routes = routes.filter(
                Q(interface_next_hop__isnull=True) | Q(interface_next_hop='')
            )
        return Device.objects.filter(
            pk__in=[d.pk for d in devices], static_routes__in=routes
        ).distinct()

    def validate_devices(self, devices):
        duplicated = list(self.duplicates_on(devices))
        if duplicated:
            names = ', '.join(str(d) for d in duplicated[:5])
            raise ValidationError(
                {
                    'devices': _(
                        'These devices already have a route with the same VRF, prefix and next hop: {names}'
                    ).format(names=names)
                }
            )
