from django.utils.translation import gettext_lazy as _

from extras.ui.panels import TagsPanel
from netbox.views.generic import (
    ObjectListView,
    ObjectEditView,
    ObjectView,
    ObjectDeleteView,
    ObjectChildrenView,
    BulkImportView,
    BulkEditView,
    BulkDeleteView,
)
from netbox.ui import panels, layout
from utilities.views import register_model_view, ViewTab

from netbox_routing.filtersets.ospf import (
    OSPFInterfaceFilterSet,
    OSPFAreaFilterSet,
    OSPFInstanceFilterSet,
    OSPFNetworkFilterSet,
    OSPFRedistributionFilterSet,
)
from netbox_routing.forms import *
from netbox_routing.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
)
from netbox_routing.tables.ospf import (
    OSPFAreaTable,
    OSPFInstanceTable,
    OSPFInterfaceTable,
    OSPFNetworkTable,
    OSPFRedistributionTable,
)
from netbox_routing.ui import *

__all__ = (
    'OSPFInstanceListView',
    'OSPFInstanceView',
    'OSPFInstanceInterfacesView',
    'OSPFInstanceEditView',
    'OSPFInstanceBulkEditView',
    'OSPFInstanceDeleteView',
    'OSPFInstanceBulkDeleteView',
    'OSPFAreaListView',
    'OSPFAreaView',
    'OSPFAreaInterfacesView',
    'OSPFAreaEditView',
    'OSPFAreaBulkEditView',
    'OSPFAreaDeleteView',
    'OSPFAreaBulkDeleteView',
    'OSPFInterfaceListView',
    'OSPFInterfaceView',
    'OSPFInterfaceEditView',
    'OSPFInterfaceBulkEditView',
    'OSPFInterfaceDeleteView',
    'OSPFInterfaceBulkDeleteView',
    'OSPFNetworkListView',
    'OSPFNetworkView',
    'OSPFNetworkEditView',
    'OSPFNetworkBulkEditView',
    'OSPFNetworkDeleteView',
    'OSPFNetworkBulkDeleteView',
    'OSPFRedistributionListView',
    'OSPFRedistributionView',
    'OSPFRedistributionEditView',
    'OSPFRedistributionBulkEditView',
    'OSPFRedistributionDeleteView',
    'OSPFRedistributionBulkDeleteView',
)


#
# Instance
#
@register_model_view(OSPFInstance, name='list', path='', detail=False)
class OSPFInstanceListView(ObjectListView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    table = OSPFInstanceTable
    filterset = OSPFInstanceFilterSet
    filterset_form = OSPFInstanceFilterForm


@register_model_view(OSPFInstance)
class OSPFInstanceView(ObjectView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFInstancePanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing.OSPFArea',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id'],
                title=_('Areas'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing.OSPFRedistribution',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device'],
                title=_('Redistribution'),
            ),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFInstance, name='interfaces')
class OSPFInstanceInterfacesView(ObjectChildrenView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    child_model = OSPFInterface
    table = OSPFInterfaceTable
    filterset = OSPFInterfaceFilterSet
    tab = ViewTab(
        label='Interfaces',
        badge=lambda obj: OSPFInterface.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent)

    def get_extra_context(self, request, instance):
        return {
            'form_interface_assignment': 'instance',
        }


@register_model_view(OSPFInstance, 'add', detail=False)
@register_model_view(OSPFInstance, name='edit')
class OSPFInstanceEditView(ObjectEditView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    form = OSPFInstanceForm


@register_model_view(OSPFInstance, name='delete')
class OSPFInstanceDeleteView(ObjectDeleteView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')


@register_model_view(OSPFInstance, name='bulk_edit', detail=False)
class OSPFInstanceBulkEditView(BulkEditView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    filterset = OSPFInstanceFilterSet
    table = OSPFInstanceTable
    form = OSPFInstanceBulkEditForm


@register_model_view(OSPFInstance, name='bulk_delete', detail=False)
class OSPFInstanceBulkDeleteView(BulkDeleteView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    filterset = OSPFInstanceFilterSet
    table = OSPFInstanceTable


@register_model_view(OSPFInstance, name='bulk_import', detail=False)
class OSPFInstanceBulkImportView(BulkImportView):
    queryset = OSPFInstance.objects.select_related('device', 'vrf')
    model_form = OSPFInstanceImportForm


#
# Area
#
@register_model_view(
    OSPFArea,
    name='list',
    path='',
    detail=False,
)
class OSPFAreaListView(ObjectListView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    table = OSPFAreaTable
    filterset = OSPFAreaFilterSet
    filterset_form = OSPFAreaFilterForm


@register_model_view(OSPFArea)
class OSPFAreaView(ObjectView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFAreaPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFArea, name='interfaces')
class OSPFAreaInterfacesView(ObjectChildrenView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    child_model = OSPFInterface
    table = OSPFInterfaceTable
    filterset = OSPFInterfaceFilterSet
    tab = ViewTab(
        label='Interfaces',
        badge=lambda obj: OSPFInterface.objects.filter(area=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(area=parent)

    def get_extra_context(self, request, instance):
        return {
            'form_interface_assignment': 'area',
        }


@register_model_view(OSPFArea, name='add', detail=False)
@register_model_view(OSPFArea, name='edit')
class OSPFAreaEditView(ObjectEditView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    form = OSPFAreaForm


@register_model_view(OSPFArea, name='delete')
class OSPFAreaDeleteView(ObjectDeleteView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')


@register_model_view(OSPFArea, name='bulk_edit', detail=False)
class OSPFAreaBulkEditView(BulkEditView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    table = OSPFAreaTable
    filterset = OSPFAreaFilterSet
    form = OSPFAreaBulkEditForm


@register_model_view(OSPFArea, name='bulk_delete', detail=False)
class OSPFAreaBulkDeleteView(BulkDeleteView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    table = OSPFAreaTable
    filterset = OSPFAreaFilterSet


@register_model_view(OSPFArea, name='bulk_import', detail=False)
class OSPFAreaBulkImportView(BulkImportView):
    queryset = OSPFArea.objects.select_related('instance__device', 'instance__vrf')
    model_form = OSPFAreaImportForm


#
# Interface
#
@register_model_view(OSPFInterface, name='list', path='', detail=False)
class OSPFInterfaceListView(ObjectListView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    table = OSPFInterfaceTable
    filterset = OSPFInterfaceFilterSet
    filterset_form = OSPFInterfaceFilterForm


@register_model_view(OSPFInterface)
class OSPFInterfaceView(ObjectView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFInterfacePanel(),
            OSPFInterfaceSettingsPanel(title=_('Interface Settings')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFInterface, name='add', detail=False)
@register_model_view(OSPFInterface, name='edit')
class OSPFInterfaceEditView(ObjectEditView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    form = OSPFInterfaceForm


@register_model_view(OSPFInterface, name='delete')
class OSPFInterfaceDeleteView(ObjectDeleteView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )


@register_model_view(OSPFInterface, name='bulk_import', detail=False)
class OSPFInterfaceBulkImportView(BulkImportView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    model_form = OSPFInterfaceImportForm


@register_model_view(OSPFInterface, name='bulk_edit', detail=False)
class OSPFInterfaceBulkEditView(BulkEditView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    filterset = OSPFInterfaceFilterSet
    table = OSPFInterfaceTable
    form = OSPFInterfaceBulkEditForm


@register_model_view(OSPFInterface, name='bulk_delete', detail=False)
class OSPFInterfaceBulkDeleteView(BulkDeleteView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area', 'interface__device'
    )
    filterset = OSPFInterfaceFilterSet
    table = OSPFInterfaceTable


#
# Network
#
NETWORK_SELECT_RELATED = (
    'ospf_interface__instance__device',
    'ospf_interface__instance__vrf',
    'ospf_interface__area',
    'ospf_interface__interface__device',
    'ip_address',
)


@register_model_view(OSPFNetwork, name='list', path='', detail=False)
class OSPFNetworkListView(ObjectListView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    table = OSPFNetworkTable
    filterset = OSPFNetworkFilterSet
    filterset_form = OSPFNetworkFilterForm


@register_model_view(OSPFNetwork)
class OSPFNetworkView(ObjectView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFNetworkPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFNetwork, name='add', detail=False)
@register_model_view(OSPFNetwork, name='edit')
class OSPFNetworkEditView(ObjectEditView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    form = OSPFNetworkForm


@register_model_view(OSPFNetwork, name='delete')
class OSPFNetworkDeleteView(ObjectDeleteView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)


@register_model_view(OSPFNetwork, name='bulk_edit', detail=False)
class OSPFNetworkBulkEditView(BulkEditView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    filterset = OSPFNetworkFilterSet
    table = OSPFNetworkTable
    form = OSPFNetworkBulkEditForm


@register_model_view(OSPFNetwork, name='bulk_delete', detail=False)
class OSPFNetworkBulkDeleteView(BulkDeleteView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    filterset = OSPFNetworkFilterSet
    table = OSPFNetworkTable


#
# Redistribution
#
REDISTRIBUTION_SELECT_RELATED = (
    'instance__device',
    'instance__vrf',
    'ospf_source__device',
    'eigrp_source__device',
    'bgp_source__asn',
    'isis_source__device',
)
REDISTRIBUTION_QUERYSET = OSPFRedistribution.objects.select_related(
    *REDISTRIBUTION_SELECT_RELATED
).prefetch_related('bgp_source__assigned_object')


@register_model_view(OSPFRedistribution, name='list', path='', detail=False)
class OSPFRedistributionListView(ObjectListView):
    queryset = REDISTRIBUTION_QUERYSET
    table = OSPFRedistributionTable
    filterset = OSPFRedistributionFilterSet
    filterset_form = OSPFRedistributionFilterForm


@register_model_view(OSPFRedistribution)
class OSPFRedistributionView(ObjectView):
    queryset = REDISTRIBUTION_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFRedistributionPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFRedistribution, name='add', detail=False)
@register_model_view(OSPFRedistribution, name='edit')
class OSPFRedistributionEditView(ObjectEditView):
    queryset = REDISTRIBUTION_QUERYSET
    form = OSPFRedistributionForm


@register_model_view(OSPFRedistribution, name='delete')
class OSPFRedistributionDeleteView(ObjectDeleteView):
    queryset = REDISTRIBUTION_QUERYSET


@register_model_view(OSPFRedistribution, name='bulk_edit', detail=False)
class OSPFRedistributionBulkEditView(BulkEditView):
    queryset = REDISTRIBUTION_QUERYSET
    filterset = OSPFRedistributionFilterSet
    table = OSPFRedistributionTable
    form = OSPFRedistributionBulkEditForm


@register_model_view(OSPFRedistribution, name='bulk_delete', detail=False)
class OSPFRedistributionBulkDeleteView(BulkDeleteView):
    queryset = REDISTRIBUTION_QUERYSET
    filterset = OSPFRedistributionFilterSet
    table = OSPFRedistributionTable
