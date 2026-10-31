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
from netbox_routing_plugin.choices import StaticRouteNextHopTypeChoices
from netbox_routing_plugin.fields.ip import IPAddressField

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
    interface = models.ForeignKey(
        to='dcim.Interface',
        on_delete=models.CASCADE,
        related_name='static_routes',
        verbose_name=_('Interface Next Hop'),
        help_text=_(
            'Outgoing interface, for routes without an IP address as next hop. '
            'The route is then carried by the device of the interface only'
        ),
        blank=True,
        null=True,
    )
    next_hop_type = models.CharField(
        max_length=20,
        choices=StaticRouteNextHopTypeChoices,
        default=StaticRouteNextHopTypeChoices.FORWARD,
        blank=True,
        verbose_name=_('Next Hop Type'),
        help_text=_(
            'Forward through an address and/or interface, or one of the special '
            'next hops of RFC 8349 (blackhole, unreachable, prohibit, receive)'
        ),
    )
    next_hop_vrf = models.ForeignKey(
        to='ipam.VRF',
        on_delete=models.PROTECT,
        related_name='staticroutes_next_hop',
        verbose_name=_('Next Hop VRF'),
        help_text=_(
            'Route leaking: the VRF in which the next hop is resolved, when it is '
            'not the VRF of the route'
        ),
        blank=True,
        null=True,
    )
    next_hop_global = models.BooleanField(
        default=False,
        verbose_name=_('Next Hop in the Global Table'),
        help_text=_('Route leaking: resolve the next hop in the global routing table'),
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
        'interface',
        'next_hop_type',
        'next_hop_vrf',
        'next_hop_global',
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
        if self.next_hop_type != StaticRouteNextHopTypeChoices.FORWARD:
            name.append(self.next_hop_type)
        elif self.next_hop or self.interface_id:
            name.append('via')
            if self.next_hop:
                name.append(f'{self.next_hop}')
            if self.interface_id:
                name.append(f'{self.interface}')
        return ' '.join(name)

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing_plugin:staticroute', args=[self.pk])

    def clean(self):
        super().clean()
        errors = {}
        special = self.next_hop_type != StaticRouteNextHopTypeChoices.FORWARD
        if special:
            for field in ('next_hop', 'interface', 'next_hop_vrf'):
                if getattr(self, f'{field}_id' if field != 'next_hop' else field):
                    errors[field] = _(
                        'A {type} route has no next hop, interface or next hop VRF.'
                    ).format(type=self.next_hop_type)
            if self.next_hop_global:
                errors['next_hop_global'] = _(
                    'A {type} route has no next hop in any table.'
                ).format(type=self.next_hop_type)
        elif not self.interface_id and not self.next_hop:
            errors['next_hop'] = _(
                "A route requires set either an IP next hop or an Interface next hop."
            )
        if self.next_hop_vrf_id and self.next_hop_global:
            errors['next_hop_global'] = _(
                'Choose a next hop VRF or the global table, not both.'
            )
        if not special and (self.next_hop_vrf_id or self.next_hop_global):
            if not self.next_hop:
                errors['next_hop'] = _(
                    'Route leaking needs an IP next hop to resolve in the other table.'
                )
            elif self.next_hop_vrf_id and self.next_hop_vrf_id == self.vrf_id:
                errors['next_hop_vrf'] = _('The next hop VRF is the VRF of the route.')
            elif self.next_hop_global and not self.vrf_id:
                errors['next_hop_global'] = _(
                    'The route is already in the global table.'
                )
        prefix = netaddr.IPNetwork(str(self.prefix)) if self.prefix else None
        if prefix is not None and prefix.ip != prefix.network:
            errors['prefix'] = _(
                'The prefix has host bits set, use {network} instead.'
            ).format(network=prefix.cidr)
        if self.next_hop and 'next_hop' not in errors:
            nh = netaddr.IPAddress(str(self.next_hop))
            if prefix is not None and nh.version != prefix.version:
                errors['next_hop'] = _(
                    'The next hop must be an IPv{version} address, like the prefix.'
                ).format(version=prefix.version)
            elif int(nh) == 0 or nh.is_multicast() or nh.is_loopback():
                errors['next_hop'] = _(
                    'The next hop must be a usable unicast address (not unspecified, loopback or multicast).'
                )
            elif nh.version == 6 and nh.is_link_local() and not self.interface_id:
                errors['interface'] = _(
                    'A link-local next hop is only meaningful on a link: '
                    'set the interface next hop (RFC 4291, RFC 4861).'
                )
        if errors:
            raise ValidationError(errors)

    def duplicates_on(self, devices):
        """
        Devices among `devices` that already carry another route with the same
        VRF, prefix, next hop type, next hop, interface and next hop table.
        """
        routes = StaticRoute.objects.filter(
            vrf=self.vrf,
            prefix=self.prefix,
            next_hop=self.next_hop,
            next_hop_type=self.next_hop_type,
            interface=self.interface,
            next_hop_vrf=self.next_hop_vrf,
            next_hop_global=self.next_hop_global,
        ).exclude(pk=self.pk)
        return Device.objects.filter(
            pk__in=[d.pk for d in devices], static_routes__in=routes
        ).distinct()

    def validate_devices(self, devices):
        errors = []
        if self.interface_id:
            others = [d for d in devices if d.pk != self.interface.device_id]
            if others:
                errors.append(
                    _(
                        'The interface {interface} belongs to {device}: '
                        'the route can only be assigned to that device.'
                    ).format(interface=self.interface, device=self.interface.device)
                )
        duplicated = list(self.duplicates_on(devices))
        if duplicated:
            names = ', '.join(str(d) for d in duplicated[:5])
            errors.append(
                _(
                    'These devices already have a route with the same VRF, prefix and next hop: {names}'
                ).format(names=names)
            )
        if errors:
            raise ValidationError({'devices': errors})
