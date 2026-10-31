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

from netbox_routing_plugin.filtersets.ospf import (
    OSPFInterfaceFilterSet,
    OSPFAreaFilterSet,
    OSPFInstanceFilterSet,
    OSPFNetworkFilterSet,
    OSPFRedistributionFilterSet,
    OSPFVirtualLinkFilterSet,
    OSPFSummaryAddressFilterSet,
    OSPFAuthenticationKeyFilterSet,
    OSPFNeighborFilterSet,
    OSPFAreaRangeFilterSet,
    OSPFPrefixSIDFilterSet,
)
from netbox_routing_plugin.forms import *
from netbox_routing_plugin.models import (
    OSPFArea,
    OSPFInstance,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFAuthenticationKey,
    OSPFNeighbor,
    OSPFAreaRange,
    OSPFPrefixSID,
)
from netbox_routing_plugin.tables.ospf import (
    OSPFAreaTable,
    OSPFInstanceTable,
    OSPFInterfaceTable,
    OSPFNetworkTable,
    OSPFRedistributionTable,
    OSPFVirtualLinkTable,
    OSPFSummaryAddressTable,
    OSPFAuthenticationKeyTable,
    OSPFNeighborTable,
    OSPFAreaRangeTable,
    OSPFPrefixSIDTable,
)
from netbox_routing_plugin.ui import *

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
    'OSPFVirtualLinkListView',
    'OSPFVirtualLinkView',
    'OSPFVirtualLinkEditView',
    'OSPFVirtualLinkBulkEditView',
    'OSPFVirtualLinkDeleteView',
    'OSPFVirtualLinkBulkDeleteView',
    'OSPFAuthenticationKeyListView',
    'OSPFAuthenticationKeyView',
    'OSPFAuthenticationKeyEditView',
    'OSPFAuthenticationKeyBulkEditView',
    'OSPFAuthenticationKeyDeleteView',
    'OSPFAuthenticationKeyBulkDeleteView',
    'OSPFSummaryAddressListView',
    'OSPFSummaryAddressView',
    'OSPFSummaryAddressEditView',
    'OSPFSummaryAddressBulkEditView',
    'OSPFSummaryAddressDeleteView',
    'OSPFSummaryAddressBulkDeleteView',
    'OSPFNeighborListView',
    'OSPFNeighborView',
    'OSPFNeighborEditView',
    'OSPFNeighborBulkEditView',
    'OSPFNeighborDeleteView',
    'OSPFNeighborBulkDeleteView',
    'OSPFAreaRangeListView',
    'OSPFAreaRangeView',
    'OSPFAreaRangeEditView',
    'OSPFAreaRangeBulkEditView',
    'OSPFAreaRangeDeleteView',
    'OSPFAreaRangeBulkDeleteView',
    'OSPFPrefixSIDListView',
    'OSPFPrefixSIDView',
    'OSPFPrefixSIDEditView',
    'OSPFPrefixSIDBulkEditView',
    'OSPFPrefixSIDDeleteView',
    'OSPFPrefixSIDBulkDeleteView',
)


#
# Instance
#
@register_model_view(OSPFInstance, name='list', path='', detail=False)
class OSPFInstanceListView(ObjectListView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    table = OSPFInstanceTable
    filterset = OSPFInstanceFilterSet
    filterset_form = OSPFInstanceFilterForm


@register_model_view(OSPFInstance)
class OSPFInstanceView(ObjectView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFInstancePanel(),
            OSPFInstanceAdvancedPanel(title=_('Advanced')),
            OSPFAuthenticationPanel(title=_('Authentication')),
            TagsPanel(),
        ],
        right_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFArea',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id'],
                title=_('Areas'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFRedistribution',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device'],
                title=_('Redistribution'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFVirtualLink',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device'],
                title=_('Virtual Links'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFSummaryAddress',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device'],
                title=_('Summary Addresses'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFPrefixSID',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device'],
                title=_('Prefix SIDs'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFAuthenticationKey',
                filters={'instance_id': lambda ctx: ctx['object'].pk},
                exclude_columns=[
                    'id',
                    'instance',
                    'area',
                    'ospf_interface',
                    'virtual_link',
                ],
                title=_('Additional Authentication Keys'),
            ),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFInstance, name='interfaces')
class OSPFInstanceInterfacesView(ObjectChildrenView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
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
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    form = OSPFInstanceForm


@register_model_view(OSPFInstance, name='delete')
class OSPFInstanceDeleteView(ObjectDeleteView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )


@register_model_view(OSPFInstance, name='bulk_edit', detail=False)
class OSPFInstanceBulkEditView(BulkEditView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    filterset = OSPFInstanceFilterSet
    table = OSPFInstanceTable
    form = OSPFInstanceBulkEditForm


@register_model_view(OSPFInstance, name='bulk_delete', detail=False)
class OSPFInstanceBulkDeleteView(BulkDeleteView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    filterset = OSPFInstanceFilterSet
    table = OSPFInstanceTable


@register_model_view(OSPFInstance, name='bulk_import', detail=False)
class OSPFInstanceBulkImportView(BulkImportView):
    queryset = OSPFInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
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
            OSPFAuthenticationPanel(title=_('Authentication')),
            TagsPanel(),
        ],
        right_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFAreaRange',
                filters={'area_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device', 'area'],
                title=_('Address Ranges'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFAuthenticationKey',
                filters={'area_id': lambda ctx: ctx['object'].pk},
                exclude_columns=[
                    'id',
                    'instance',
                    'area',
                    'ospf_interface',
                    'virtual_link',
                ],
                title=_('Additional Authentication Keys'),
            ),
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
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    table = OSPFInterfaceTable
    filterset = OSPFInterfaceFilterSet
    filterset_form = OSPFInterfaceFilterForm


@register_model_view(OSPFInterface)
class OSPFInterfaceView(ObjectView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFInterfacePanel(),
            OSPFInterfaceSettingsPanel(title=_('Interface Settings')),
            TagsPanel(),
        ],
        right_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFNeighbor',
                filters={'ospf_interface_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'instance', 'device', 'ospf_interface'],
                title=_('Neighbors'),
            ),
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFAuthenticationKey',
                filters={'ospf_interface_id': lambda ctx: ctx['object'].pk},
                exclude_columns=[
                    'id',
                    'instance',
                    'area',
                    'ospf_interface',
                    'virtual_link',
                ],
                title=_('Additional Authentication Keys'),
            ),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFInterface, name='add', detail=False)
@register_model_view(OSPFInterface, name='edit')
class OSPFInterfaceEditView(ObjectEditView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    form = OSPFInterfaceForm


@register_model_view(OSPFInterface, name='delete')
class OSPFInterfaceDeleteView(ObjectDeleteView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )


@register_model_view(OSPFInterface, name='bulk_import', detail=False)
class OSPFInterfaceBulkImportView(BulkImportView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    model_form = OSPFInterfaceImportForm


@register_model_view(OSPFInterface, name='bulk_edit', detail=False)
class OSPFInterfaceBulkEditView(BulkEditView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    filterset = OSPFInterfaceFilterSet
    table = OSPFInterfaceTable
    form = OSPFInterfaceBulkEditForm


@register_model_view(OSPFInterface, name='bulk_delete', detail=False)
class OSPFInterfaceBulkDeleteView(BulkDeleteView):
    queryset = OSPFInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'area__instance', 'interface__device'
    )
    filterset = OSPFInterfaceFilterSet
    table = OSPFInterfaceTable


#
# Network
#
NETWORK_SELECT_RELATED = (
    'ospf_interface__instance__device',
    'ospf_interface__instance__vrf',
    'ospf_interface__area__instance',
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


@register_model_view(OSPFNetwork, name='bulk_import', detail=False)
class OSPFNetworkBulkImportView(BulkImportView):
    queryset = OSPFNetwork.objects.select_related(*NETWORK_SELECT_RELATED)
    model_form = OSPFNetworkImportForm


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
    'bgp_source__device',
    'bgp_source__vrf',
    'bgp_source__asn',
    'isis_source__device',
    'route_policy',
)
REDISTRIBUTION_QUERYSET = OSPFRedistribution.objects.select_related(
    *REDISTRIBUTION_SELECT_RELATED
)


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


@register_model_view(OSPFRedistribution, name='bulk_import', detail=False)
class OSPFRedistributionBulkImportView(BulkImportView):
    queryset = REDISTRIBUTION_QUERYSET
    model_form = OSPFRedistributionImportForm


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


#
# Virtual link
#
VIRTUAL_LINK_QUERYSET = OSPFVirtualLink.objects.select_related(
    'instance__device', 'instance__vrf', 'transit_area__instance'
)


@register_model_view(OSPFVirtualLink, name='list', path='', detail=False)
class OSPFVirtualLinkListView(ObjectListView):
    queryset = VIRTUAL_LINK_QUERYSET
    table = OSPFVirtualLinkTable
    filterset = OSPFVirtualLinkFilterSet
    filterset_form = OSPFVirtualLinkFilterForm


@register_model_view(OSPFVirtualLink)
class OSPFVirtualLinkView(ObjectView):
    queryset = VIRTUAL_LINK_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFVirtualLinkPanel(),
            OSPFAuthenticationPanel(title=_('Authentication')),
            TagsPanel(),
        ],
        right_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_plugin.OSPFAuthenticationKey',
                filters={'virtual_link_id': lambda ctx: ctx['object'].pk},
                exclude_columns=[
                    'id',
                    'instance',
                    'area',
                    'ospf_interface',
                    'virtual_link',
                ],
                title=_('Additional Authentication Keys'),
            ),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFVirtualLink, name='add', detail=False)
@register_model_view(OSPFVirtualLink, name='edit')
class OSPFVirtualLinkEditView(ObjectEditView):
    queryset = VIRTUAL_LINK_QUERYSET
    form = OSPFVirtualLinkForm


@register_model_view(OSPFVirtualLink, name='delete')
class OSPFVirtualLinkDeleteView(ObjectDeleteView):
    queryset = VIRTUAL_LINK_QUERYSET


@register_model_view(OSPFVirtualLink, name='bulk_import', detail=False)
class OSPFVirtualLinkBulkImportView(BulkImportView):
    queryset = VIRTUAL_LINK_QUERYSET
    model_form = OSPFVirtualLinkImportForm


@register_model_view(OSPFVirtualLink, name='bulk_edit', detail=False)
class OSPFVirtualLinkBulkEditView(BulkEditView):
    queryset = VIRTUAL_LINK_QUERYSET
    filterset = OSPFVirtualLinkFilterSet
    table = OSPFVirtualLinkTable
    form = OSPFVirtualLinkBulkEditForm


@register_model_view(OSPFVirtualLink, name='bulk_delete', detail=False)
class OSPFVirtualLinkBulkDeleteView(BulkDeleteView):
    queryset = VIRTUAL_LINK_QUERYSET
    filterset = OSPFVirtualLinkFilterSet
    table = OSPFVirtualLinkTable


#
# Summary address
#
SUMMARY_ADDRESS_QUERYSET = OSPFSummaryAddress.objects.select_related(
    'instance__device', 'instance__vrf'
)


@register_model_view(OSPFSummaryAddress, name='list', path='', detail=False)
class OSPFSummaryAddressListView(ObjectListView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    table = OSPFSummaryAddressTable
    filterset = OSPFSummaryAddressFilterSet
    filterset_form = OSPFSummaryAddressFilterForm


@register_model_view(OSPFSummaryAddress)
class OSPFSummaryAddressView(ObjectView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFSummaryAddressPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFSummaryAddress, name='add', detail=False)
@register_model_view(OSPFSummaryAddress, name='edit')
class OSPFSummaryAddressEditView(ObjectEditView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    form = OSPFSummaryAddressForm


@register_model_view(OSPFSummaryAddress, name='delete')
class OSPFSummaryAddressDeleteView(ObjectDeleteView):
    queryset = SUMMARY_ADDRESS_QUERYSET


@register_model_view(OSPFSummaryAddress, name='bulk_import', detail=False)
class OSPFSummaryAddressBulkImportView(BulkImportView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    model_form = OSPFSummaryAddressImportForm


@register_model_view(OSPFSummaryAddress, name='bulk_edit', detail=False)
class OSPFSummaryAddressBulkEditView(BulkEditView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    filterset = OSPFSummaryAddressFilterSet
    table = OSPFSummaryAddressTable
    form = OSPFSummaryAddressBulkEditForm


@register_model_view(OSPFSummaryAddress, name='bulk_delete', detail=False)
class OSPFSummaryAddressBulkDeleteView(BulkDeleteView):
    queryset = SUMMARY_ADDRESS_QUERYSET
    filterset = OSPFSummaryAddressFilterSet
    table = OSPFSummaryAddressTable


#
# Neighbor
#
NEIGHBOR_QUERYSET = OSPFNeighbor.objects.select_related(
    'ospf_interface__instance__device',
    'ospf_interface__instance__vrf',
    'ospf_interface__area__instance',
    'ospf_interface__interface__device',
)


@register_model_view(OSPFNeighbor, name='list', path='', detail=False)
class OSPFNeighborListView(ObjectListView):
    queryset = NEIGHBOR_QUERYSET
    table = OSPFNeighborTable
    filterset = OSPFNeighborFilterSet
    filterset_form = OSPFNeighborFilterForm


@register_model_view(OSPFNeighbor)
class OSPFNeighborView(ObjectView):
    queryset = NEIGHBOR_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFNeighborPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFNeighbor, name='add', detail=False)
@register_model_view(OSPFNeighbor, name='edit')
class OSPFNeighborEditView(ObjectEditView):
    queryset = NEIGHBOR_QUERYSET
    form = OSPFNeighborForm


@register_model_view(OSPFNeighbor, name='delete')
class OSPFNeighborDeleteView(ObjectDeleteView):
    queryset = NEIGHBOR_QUERYSET


@register_model_view(OSPFNeighbor, name='bulk_import', detail=False)
class OSPFNeighborBulkImportView(BulkImportView):
    queryset = NEIGHBOR_QUERYSET
    model_form = OSPFNeighborImportForm


@register_model_view(OSPFNeighbor, name='bulk_edit', detail=False)
class OSPFNeighborBulkEditView(BulkEditView):
    queryset = NEIGHBOR_QUERYSET
    filterset = OSPFNeighborFilterSet
    table = OSPFNeighborTable
    form = OSPFNeighborBulkEditForm


@register_model_view(OSPFNeighbor, name='bulk_delete', detail=False)
class OSPFNeighborBulkDeleteView(BulkDeleteView):
    queryset = NEIGHBOR_QUERYSET
    filterset = OSPFNeighborFilterSet
    table = OSPFNeighborTable


#
# Area range
#
AREA_RANGE_QUERYSET = OSPFAreaRange.objects.select_related(
    'area__instance__device', 'area__instance__vrf'
)


@register_model_view(OSPFAreaRange, name='list', path='', detail=False)
class OSPFAreaRangeListView(ObjectListView):
    queryset = AREA_RANGE_QUERYSET
    table = OSPFAreaRangeTable
    filterset = OSPFAreaRangeFilterSet
    filterset_form = OSPFAreaRangeFilterForm


@register_model_view(OSPFAreaRange)
class OSPFAreaRangeView(ObjectView):
    queryset = AREA_RANGE_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFAreaRangePanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFAreaRange, name='add', detail=False)
@register_model_view(OSPFAreaRange, name='edit')
class OSPFAreaRangeEditView(ObjectEditView):
    queryset = AREA_RANGE_QUERYSET
    form = OSPFAreaRangeForm


@register_model_view(OSPFAreaRange, name='delete')
class OSPFAreaRangeDeleteView(ObjectDeleteView):
    queryset = AREA_RANGE_QUERYSET


@register_model_view(OSPFAreaRange, name='bulk_import', detail=False)
class OSPFAreaRangeBulkImportView(BulkImportView):
    queryset = AREA_RANGE_QUERYSET
    model_form = OSPFAreaRangeImportForm


@register_model_view(OSPFAreaRange, name='bulk_edit', detail=False)
class OSPFAreaRangeBulkEditView(BulkEditView):
    queryset = AREA_RANGE_QUERYSET
    filterset = OSPFAreaRangeFilterSet
    table = OSPFAreaRangeTable
    form = OSPFAreaRangeBulkEditForm


@register_model_view(OSPFAreaRange, name='bulk_delete', detail=False)
class OSPFAreaRangeBulkDeleteView(BulkDeleteView):
    queryset = AREA_RANGE_QUERYSET
    filterset = OSPFAreaRangeFilterSet
    table = OSPFAreaRangeTable


#
# Prefix SID
#
PREFIX_SID_QUERYSET = OSPFPrefixSID.objects.select_related(
    'instance__device', 'instance__vrf'
)


@register_model_view(OSPFPrefixSID, name='list', path='', detail=False)
class OSPFPrefixSIDListView(ObjectListView):
    queryset = PREFIX_SID_QUERYSET
    table = OSPFPrefixSIDTable
    filterset = OSPFPrefixSIDFilterSet
    filterset_form = OSPFPrefixSIDFilterForm


@register_model_view(OSPFPrefixSID)
class OSPFPrefixSIDView(ObjectView):
    queryset = PREFIX_SID_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFPrefixSIDPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(OSPFPrefixSID, name='add', detail=False)
@register_model_view(OSPFPrefixSID, name='edit')
class OSPFPrefixSIDEditView(ObjectEditView):
    queryset = PREFIX_SID_QUERYSET
    form = OSPFPrefixSIDForm


@register_model_view(OSPFPrefixSID, name='delete')
class OSPFPrefixSIDDeleteView(ObjectDeleteView):
    queryset = PREFIX_SID_QUERYSET


@register_model_view(OSPFPrefixSID, name='bulk_import', detail=False)
class OSPFPrefixSIDBulkImportView(BulkImportView):
    queryset = PREFIX_SID_QUERYSET
    model_form = OSPFPrefixSIDImportForm


@register_model_view(OSPFPrefixSID, name='bulk_edit', detail=False)
class OSPFPrefixSIDBulkEditView(BulkEditView):
    queryset = PREFIX_SID_QUERYSET
    filterset = OSPFPrefixSIDFilterSet
    table = OSPFPrefixSIDTable
    form = OSPFPrefixSIDBulkEditForm


@register_model_view(OSPFPrefixSID, name='bulk_delete', detail=False)
class OSPFPrefixSIDBulkDeleteView(BulkDeleteView):
    queryset = PREFIX_SID_QUERYSET
    filterset = OSPFPrefixSIDFilterSet
    table = OSPFPrefixSIDTable


#
# Authentication key
#
AUTHENTICATION_KEY_QUERYSET = OSPFAuthenticationKey.objects.select_related(
    'instance__device',
    'instance__vrf',
    'area__instance',
    'ospf_interface__instance',
    'ospf_interface__interface__device',
    'virtual_link__instance',
    'virtual_link__transit_area__instance',
)


@register_model_view(OSPFAuthenticationKey, name='list', path='', detail=False)
class OSPFAuthenticationKeyListView(ObjectListView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    table = OSPFAuthenticationKeyTable
    filterset = OSPFAuthenticationKeyFilterSet
    filterset_form = OSPFAuthenticationKeyFilterForm


@register_model_view(OSPFAuthenticationKey)
class OSPFAuthenticationKeyView(ObjectView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            OSPFAuthenticationKeyPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
        ],
    )


@register_model_view(OSPFAuthenticationKey, name='add', detail=False)
@register_model_view(OSPFAuthenticationKey, name='edit')
class OSPFAuthenticationKeyEditView(ObjectEditView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    form = OSPFAuthenticationKeyForm


@register_model_view(OSPFAuthenticationKey, name='delete')
class OSPFAuthenticationKeyDeleteView(ObjectDeleteView):
    queryset = AUTHENTICATION_KEY_QUERYSET


@register_model_view(OSPFAuthenticationKey, name='bulk_import', detail=False)
class OSPFAuthenticationKeyBulkImportView(BulkImportView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    model_form = OSPFAuthenticationKeyImportForm


@register_model_view(OSPFAuthenticationKey, name='bulk_edit', detail=False)
class OSPFAuthenticationKeyBulkEditView(BulkEditView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    filterset = OSPFAuthenticationKeyFilterSet
    table = OSPFAuthenticationKeyTable
    form = OSPFAuthenticationKeyBulkEditForm


@register_model_view(OSPFAuthenticationKey, name='bulk_delete', detail=False)
class OSPFAuthenticationKeyBulkDeleteView(BulkDeleteView):
    queryset = AUTHENTICATION_KEY_QUERYSET
    filterset = OSPFAuthenticationKeyFilterSet
    table = OSPFAuthenticationKeyTable
