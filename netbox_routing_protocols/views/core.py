from dcim.models import Device
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_tables2 import RequestConfig
from netbox.views import generic
from utilities.views import ViewTab, get_default_template, register_model_view

from netbox_routing_protocols.models import (
    BGPInstance,
    EIGRPRouter,
    ISISInstance,
    OSPFInstance,
    StaticRoute,
)
from netbox_routing_protocols.tables import (
    BGPInstanceTable,
    EIGRPRouterTable,
    ISISInstanceTable,
    OSPFInstanceTable,
    StaticRouteTable,
)

# One section per protocol of the device routing tab. The device is the page, so the
# tables leave its column out. A static route is assigned to devices (many to many);
# the instances of the protocols belong to one device.
DEVICE_ROUTING_SECTIONS = (
    {
        'title': _('Static routes'),
        'list_url': 'plugins:netbox_routing_protocols:staticroute_list',
        'model': StaticRoute,
        'table': StaticRouteTable,
        'device_lookup': 'devices',
        'exclude': ('devices',),
    },
    {
        'title': _('OSPF instances'),
        'list_url': 'plugins:netbox_routing_protocols:ospfinstance_list',
        'model': OSPFInstance,
        'table': OSPFInstanceTable,
        'device_lookup': 'device',
        'exclude': ('device',),
    },
    {
        'title': _('IS-IS instances'),
        'list_url': 'plugins:netbox_routing_protocols:isisinstance_list',
        'model': ISISInstance,
        'table': ISISInstanceTable,
        'device_lookup': 'device',
        'exclude': ('device',),
    },
    {
        'title': _('EIGRP routers'),
        'list_url': 'plugins:netbox_routing_protocols:eigrprouter_list',
        'model': EIGRPRouter,
        'table': EIGRPRouterTable,
        'device_lookup': 'device',
        'exclude': ('device',),
    },
    {
        'title': _('BGP instances'),
        'list_url': 'plugins:netbox_routing_protocols:bgpinstance_list',
        'model': BGPInstance,
        'table': BGPInstanceTable,
        'device_lookup': 'device',
        'exclude': ('device',),
    },
)


# The columns of the instances show their address families (or the VRF of their families)
PREFETCH = {
    ISISInstance: ('address_families',),
    EIGRPRouter: ('eigrpaddressfamily_set__vrf',),
    BGPInstance: ('address_families',),
}


def _device_queryset(section, device, restrict_user=None):
    queryset = (
        section['model']
        .objects.filter(**{section['device_lookup']: device})
        .prefetch_related(*PREFETCH.get(section['model'], ()))
    )
    if restrict_user is not None:
        queryset = queryset.restrict(restrict_user, 'view')
    return queryset


def _routing_count(device):
    return sum(
        _device_queryset(section, device).count() for section in DEVICE_ROUTING_SECTIONS
    )


@register_model_view(Device, name='routing', path='routing')
class DeviceRoutingView(generic.ObjectView):
    """
    The routing of a device: its static routes and its OSPF, IS-IS, EIGRP and BGP
    instances, one section per protocol, in one tab.
    """

    template_name = 'netbox_routing_protocols/device_routing.html'
    queryset = Device.objects.all()
    tab = ViewTab(
        label=_('Routing'),
        badge=_routing_count,
    )

    def get(self, request, *args, **kwargs):
        device = self.get_object(**kwargs)
        sections = []
        for section in DEVICE_ROUTING_SECTIONS:
            queryset = _device_queryset(section, device, restrict_user=request.user)
            table = section['table'](queryset, exclude=section['exclude'])
            RequestConfig(request, paginate=False).configure(table)
            sections.append(
                {
                    'title': section['title'],
                    'list_url': f"{reverse(section['list_url'])}?device_id={device.pk}",
                    'table': table,
                    'count': queryset.count(),
                }
            )
        return render(
            request,
            self.template_name,
            {
                'object': device,
                'base_template': get_default_template(device),
                'tab': self.tab,
                'sections': sections,
            },
        )
