import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from netbox.tables import NetBoxTable
from netbox_routing_protocols.models import (
    EIGRPAddressFamily,
    EIGRPRouter,
    EIGRPInterface,
)

__all__ = (
    'EIGRPAddressFamilyTable',
    'EIGRPRouterTable',
    'EIGRPNetworkTable',
    'EIGRPInterfaceTable',
)


class EIGRPRouterTable(NetBoxTable):
    name = tables.Column(verbose_name=_('Name'), linkify=True)
    device = tables.Column(verbose_name=_('Device'), linkify=True)
    router_id = tables.Column(accessor='rid', verbose_name=_('Router ID'), linkify=True)
    vrf = tables.Column(
        accessor='pk',
        verbose_name=_('VRF'),
        linkify=True,
        orderable=False,
        empty_values=(),
    )
    address_family = tables.Column(
        accessor='pk',
        verbose_name=_('Address Family'),
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    def render_vrf(self, record):
        names = {
            af.vrf.name if af.vrf_id else 'Global'
            for af in record.eigrpaddressfamily_set.all()
        }
        return ', '.join(sorted(names)) or 'Global'

    def render_address_family(self, record):
        names = {
            (
                af.get_family_display()
                if hasattr(af, 'get_family_display')
                else f'IPv{af.family}'
            )
            for af in record.eigrpaddressfamily_set.all()
        }
        return ', '.join(sorted(names))

    import_policy = tables.Column(verbose_name=_('Import Policy'), linkify=True)
    export_policy = tables.Column(verbose_name=_('Export Policy'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = EIGRPRouter
        fields = (
            'pk',
            'id',
            'name',
            'mode',
            'pid',
            'rid',
            'device',
            'import_policy',
            'export_policy',
        )
        default_columns = (
            'name',
            'device',
            'router_id',
            'vrf',
            'address_family',
        )


class EIGRPAddressFamilyTable(NetBoxTable):
    router = tables.Column(verbose_name=_('Router'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = EIGRPAddressFamily
        fields = ('pk', 'id', 'family', 'router')
        default_columns = ('pk', 'id', 'family', 'router')


class EIGRPNetworkTable(NetBoxTable):
    router = tables.Column(verbose_name=_('Router'), linkify=True)
    address_family = tables.Column(verbose_name=_('Address Family'), linkify=True)
    network = tables.Column(verbose_name=_('Network'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = EIGRPInterface
        fields = ('pk', 'id', 'router', 'address_family', 'network')
        default_columns = ('pk', 'id', 'router', 'address_family', 'network')


class EIGRPInterfaceTable(NetBoxTable):
    router = tables.Column(verbose_name=_('Router'), linkify=True)
    address_family = tables.Column(verbose_name=_('Address Family'), linkify=True)
    interface = tables.Column(verbose_name=_('Interface'), linkify=True)

    class Meta(NetBoxTable.Meta):
        model = EIGRPInterface
        fields = (
            'pk',
            'id',
            'router',
            'address_family',
            'interface',
            'passive',
            'bfd',
            'authentication',
            'passphrase',
        )
        default_columns = ('pk', 'id', 'router', 'address_family', 'interface')
