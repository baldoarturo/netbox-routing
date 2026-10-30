# SPDX-License-Identifier: Apache-2.0

from django.utils.translation import gettext_lazy as _

from extras.ui.panels import TagsPanel
from netbox.views.generic import (
    BulkDeleteView,
    BulkEditView,
    BulkImportView,
    ObjectChildrenView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from netbox.ui import panels, layout
from utilities.views import ViewTab, register_model_view

from netbox_routing_protocols.choices import ISISSettingChoices
from netbox_routing_protocols.filtersets.isis import (
    ISISInstanceFilterSet,
    ISISInterfaceFilterSet,
    ISISSettingFilterSet,
    ISISLevelFilterSet,
    ISISInterfaceLevelFilterSet,
    ISISSegmentRoutingFilterSet,
    ISISFlexAlgoFilterSet,
    ISISPrefixSIDFilterSet,
    ISISSRv6LocatorFilterSet,
    ISISAddressFamilyFilterSet,
    ISISSRMappingEntryFilterSet,
    ISISAdjacencySIDFilterSet,
    ISISRedistributionFilterSet,
    ISISSummaryAddressFilterSet,
    ISISRouteLeakFilterSet,
    ISISAreaAddressFilterSet,
)
from netbox_routing_protocols.forms import *
from netbox_routing_protocols.models import (
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
    ISISAreaAddress,
    ISISSRMappingEntry,
    ISISAdjacencySID,
    ISISAddressFamily,
)
from netbox_routing_protocols.tables.isis import (
    ISISInstanceTable,
    ISISInterfaceTable,
    ISISSettingTable,
    ISISLevelTable,
    ISISInterfaceLevelTable,
    ISISSegmentRoutingTable,
    ISISFlexAlgoTable,
    ISISPrefixSIDTable,
    ISISSRv6LocatorTable,
    ISISAddressFamilyTable,
    ISISSRMappingEntryTable,
    ISISAdjacencySIDTable,
    ISISAreaAddressTable,
    ISISRedistributionTable,
    ISISSummaryAddressTable,
    ISISRouteLeakTable,
)
from netbox_routing_protocols.ui import *

__all__ = (
    'ISISSettingListView',
    'ISISSettingView',
    'ISISSettingEditView',
    'ISISSettingDeleteView',
    'ISISSettingBulkEditView',
    'ISISSettingBulkDeleteView',
    'ISISSettingBulkImportView',
    'ISISLevelListView',
    'ISISLevelView',
    'ISISLevelEditView',
    'ISISLevelDeleteView',
    'ISISLevelBulkDeleteView',
    'ISISLevelBulkImportView',
    'ISISInterfaceLevelListView',
    'ISISInterfaceLevelView',
    'ISISInterfaceLevelEditView',
    'ISISInterfaceLevelDeleteView',
    'ISISInterfaceLevelBulkDeleteView',
    'ISISInterfaceLevelBulkImportView',
    'ISISSegmentRoutingListView',
    'ISISSegmentRoutingView',
    'ISISSegmentRoutingEditView',
    'ISISSegmentRoutingDeleteView',
    'ISISSegmentRoutingBulkDeleteView',
    'ISISSegmentRoutingBulkImportView',
    'ISISFlexAlgoListView',
    'ISISFlexAlgoView',
    'ISISFlexAlgoEditView',
    'ISISFlexAlgoDeleteView',
    'ISISFlexAlgoBulkDeleteView',
    'ISISFlexAlgoBulkImportView',
    'ISISPrefixSIDListView',
    'ISISPrefixSIDView',
    'ISISPrefixSIDEditView',
    'ISISPrefixSIDDeleteView',
    'ISISPrefixSIDBulkDeleteView',
    'ISISPrefixSIDBulkImportView',
    'ISISSRv6LocatorListView',
    'ISISSRv6LocatorView',
    'ISISSRv6LocatorEditView',
    'ISISSRv6LocatorDeleteView',
    'ISISSRv6LocatorBulkDeleteView',
    'ISISSRv6LocatorBulkImportView',
    'ISISAddressFamilyListView',
    'ISISAddressFamilyView',
    'ISISAddressFamilyEditView',
    'ISISAddressFamilyBulkEditView',
    'ISISAddressFamilyDeleteView',
    'ISISAddressFamilyBulkDeleteView',
    'ISISAddressFamilyBulkImportView',
    'ISISInstanceAddressFamiliesView',
    'ISISSRMappingEntryListView',
    'ISISSRMappingEntryView',
    'ISISSRMappingEntryEditView',
    'ISISSRMappingEntryBulkEditView',
    'ISISSRMappingEntryDeleteView',
    'ISISSRMappingEntryBulkDeleteView',
    'ISISSRMappingEntryBulkImportView',
    'ISISAdjacencySIDListView',
    'ISISAdjacencySIDView',
    'ISISAdjacencySIDEditView',
    'ISISAdjacencySIDBulkEditView',
    'ISISAdjacencySIDDeleteView',
    'ISISAdjacencySIDBulkDeleteView',
    'ISISAdjacencySIDBulkImportView',
    'ISISInstanceSRMappingEntriesView',
    'ISISInterfaceAdjacencySidsView',
    'ISISAreaAddressListView',
    'ISISAreaAddressView',
    'ISISAreaAddressEditView',
    'ISISAreaAddressDeleteView',
    'ISISAreaAddressBulkDeleteView',
    'ISISAreaAddressBulkImportView',
    'ISISInstanceAreaAddressesView',
    'ISISRedistributionListView',
    'ISISRedistributionView',
    'ISISRedistributionEditView',
    'ISISRedistributionBulkEditView',
    'ISISRedistributionDeleteView',
    'ISISRedistributionBulkDeleteView',
    'ISISRedistributionBulkImportView',
    'ISISSummaryAddressListView',
    'ISISSummaryAddressView',
    'ISISSummaryAddressEditView',
    'ISISSummaryAddressBulkEditView',
    'ISISSummaryAddressDeleteView',
    'ISISSummaryAddressBulkDeleteView',
    'ISISSummaryAddressBulkImportView',
    'ISISRouteLeakListView',
    'ISISRouteLeakView',
    'ISISRouteLeakEditView',
    'ISISRouteLeakBulkEditView',
    'ISISRouteLeakDeleteView',
    'ISISRouteLeakBulkDeleteView',
    'ISISRouteLeakBulkImportView',
    'ISISInstanceLevelsView',
    'ISISInstanceFlexAlgosView',
    'ISISInstanceRedistributionsView',
    'ISISInstanceSummaryAddressesView',
    'ISISInstanceRouteLeaksView',
    'ISISInstanceSRv6LocatorsView',
    'ISISInterfaceLevelsView',
    'ISISInterfacePrefixSidsView',
    'ISISInstanceListView',
    'ISISInstanceView',
    'ISISInstanceInterfacesView',
    'ISISInstanceEditView',
    'ISISInstanceBulkEditView',
    'ISISInstanceDeleteView',
    'ISISInstanceBulkDeleteView',
    'ISISInstanceBulkImportView',
    'ISISInterfaceListView',
    'ISISInterfaceView',
    'ISISInterfaceEditView',
    'ISISInterfaceBulkEditView',
    'ISISInterfaceDeleteView',
    'ISISInterfaceBulkDeleteView',
    'ISISInterfaceBulkImportView',
)


# IS-IS Settings (EAV)


@register_model_view(ISISSetting, name='list', path='', detail=False)
class ISISSettingListView(ObjectListView):
    queryset = ISISSetting.objects.select_related(
        'assigned_object_type'
    ).prefetch_related('assigned_object')
    filterset = ISISSettingFilterSet
    filterset_form = ISISSettingFilterForm
    table = ISISSettingTable


@register_model_view(ISISSetting)
class ISISSettingView(ObjectView):
    queryset = ISISSetting.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            ISISSettingPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(ISISSetting, name='add', detail=False)
@register_model_view(ISISSetting, name='edit')
class ISISSettingEditView(ObjectEditView):
    queryset = ISISSetting.objects.all()
    form = ISISSettingForm


@register_model_view(ISISSetting, name='delete')
class ISISSettingDeleteView(ObjectDeleteView):
    queryset = ISISSetting.objects.all()


@register_model_view(ISISSetting, name='bulk_import', detail=False)
class ISISSettingBulkImportView(BulkImportView):
    queryset = ISISSetting.objects.all()
    model_form = ISISSettingImportForm


@register_model_view(ISISSetting, name='bulk_edit', detail=False)
class ISISSettingBulkEditView(BulkEditView):
    queryset = ISISSetting.objects.all()
    filterset = ISISSettingFilterSet
    table = ISISSettingTable
    form = ISISSettingBulkEditForm


@register_model_view(ISISSetting, name='bulk_delete', detail=False)
class ISISSettingBulkDeleteView(BulkDeleteView):
    queryset = ISISSetting.objects.all()
    filterset = ISISSettingFilterSet
    table = ISISSettingTable


# IS-IS Level (per-level instance tuning)


@register_model_view(ISISLevel, name='list', path='', detail=False)
class ISISLevelListView(ObjectListView):
    queryset = ISISLevel.objects.select_related('instance__device')
    filterset = ISISLevelFilterSet
    filterset_form = ISISLevelFilterForm
    table = ISISLevelTable


@register_model_view(ISISLevel)
class ISISLevelView(ObjectView):
    queryset = ISISLevel.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISLevelPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISLevel, name='add', detail=False)
@register_model_view(ISISLevel, name='edit')
class ISISLevelEditView(ObjectEditView):
    queryset = ISISLevel.objects.all()
    form = ISISLevelForm


@register_model_view(ISISLevel, name='delete')
class ISISLevelDeleteView(ObjectDeleteView):
    queryset = ISISLevel.objects.all()


@register_model_view(ISISLevel, name='bulk_import', detail=False)
class ISISLevelBulkImportView(BulkImportView):
    queryset = ISISLevel.objects.all()
    model_form = ISISLevelImportForm


@register_model_view(ISISLevel, name='bulk_edit', detail=False)
class ISISLevelBulkEditView(BulkEditView):
    queryset = ISISLevel.objects.all()
    filterset = ISISLevelFilterSet
    table = ISISLevelTable
    form = ISISLevelBulkEditForm


@register_model_view(ISISLevel, name='bulk_delete', detail=False)
class ISISLevelBulkDeleteView(BulkDeleteView):
    queryset = ISISLevel.objects.all()
    filterset = ISISLevelFilterSet
    table = ISISLevelTable


# IS-IS Interface Level (per-level interface tuning)


@register_model_view(ISISInterfaceLevel, name='list', path='', detail=False)
class ISISInterfaceLevelListView(ObjectListView):
    queryset = ISISInterfaceLevel.objects.select_related('interface__interface')
    filterset = ISISInterfaceLevelFilterSet
    filterset_form = ISISInterfaceLevelFilterForm
    table = ISISInterfaceLevelTable


@register_model_view(ISISInterfaceLevel)
class ISISInterfaceLevelView(ObjectView):
    queryset = ISISInterfaceLevel.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISInterfaceLevelPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISInterfaceLevel, name='add', detail=False)
@register_model_view(ISISInterfaceLevel, name='edit')
class ISISInterfaceLevelEditView(ObjectEditView):
    queryset = ISISInterfaceLevel.objects.all()
    form = ISISInterfaceLevelForm


@register_model_view(ISISInterfaceLevel, name='delete')
class ISISInterfaceLevelDeleteView(ObjectDeleteView):
    queryset = ISISInterfaceLevel.objects.all()


@register_model_view(ISISInterfaceLevel, name='bulk_import', detail=False)
class ISISInterfaceLevelBulkImportView(BulkImportView):
    queryset = ISISInterfaceLevel.objects.all()
    model_form = ISISInterfaceLevelImportForm


@register_model_view(ISISInterfaceLevel, name='bulk_edit', detail=False)
class ISISInterfaceLevelBulkEditView(BulkEditView):
    queryset = ISISInterfaceLevel.objects.all()
    filterset = ISISInterfaceLevelFilterSet
    table = ISISInterfaceLevelTable
    form = ISISInterfaceLevelBulkEditForm


@register_model_view(ISISInterfaceLevel, name='bulk_delete', detail=False)
class ISISInterfaceLevelBulkDeleteView(BulkDeleteView):
    queryset = ISISInterfaceLevel.objects.all()
    filterset = ISISInterfaceLevelFilterSet
    table = ISISInterfaceLevelTable


# IS-IS Segment Routing (1:1 with instance)


@register_model_view(ISISSegmentRouting, name='list', path='', detail=False)
class ISISSegmentRoutingListView(ObjectListView):
    queryset = ISISSegmentRouting.objects.select_related('instance__device')
    filterset = ISISSegmentRoutingFilterSet
    filterset_form = ISISSegmentRoutingFilterForm
    table = ISISSegmentRoutingTable


@register_model_view(ISISSegmentRouting)
class ISISSegmentRoutingView(ObjectView):
    queryset = ISISSegmentRouting.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISSegmentRoutingPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISSegmentRouting, name='add', detail=False)
@register_model_view(ISISSegmentRouting, name='edit')
class ISISSegmentRoutingEditView(ObjectEditView):
    queryset = ISISSegmentRouting.objects.all()
    form = ISISSegmentRoutingForm


@register_model_view(ISISSegmentRouting, name='delete')
class ISISSegmentRoutingDeleteView(ObjectDeleteView):
    queryset = ISISSegmentRouting.objects.all()


@register_model_view(ISISSegmentRouting, name='bulk_import', detail=False)
class ISISSegmentRoutingBulkImportView(BulkImportView):
    queryset = ISISSegmentRouting.objects.all()
    model_form = ISISSegmentRoutingImportForm


@register_model_view(ISISSegmentRouting, name='bulk_edit', detail=False)
class ISISSegmentRoutingBulkEditView(BulkEditView):
    queryset = ISISSegmentRouting.objects.all()
    filterset = ISISSegmentRoutingFilterSet
    table = ISISSegmentRoutingTable
    form = ISISSegmentRoutingBulkEditForm


@register_model_view(ISISSegmentRouting, name='bulk_delete', detail=False)
class ISISSegmentRoutingBulkDeleteView(BulkDeleteView):
    queryset = ISISSegmentRouting.objects.all()
    filterset = ISISSegmentRoutingFilterSet
    table = ISISSegmentRoutingTable


# IS-IS Flex-Algo


@register_model_view(ISISFlexAlgo, name='list', path='', detail=False)
class ISISFlexAlgoListView(ObjectListView):
    queryset = ISISFlexAlgo.objects.select_related('instance__device')
    filterset = ISISFlexAlgoFilterSet
    filterset_form = ISISFlexAlgoFilterForm
    table = ISISFlexAlgoTable


@register_model_view(ISISFlexAlgo)
class ISISFlexAlgoView(ObjectView):
    queryset = ISISFlexAlgo.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISFlexAlgoPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISFlexAlgo, name='add', detail=False)
@register_model_view(ISISFlexAlgo, name='edit')
class ISISFlexAlgoEditView(ObjectEditView):
    queryset = ISISFlexAlgo.objects.all()
    form = ISISFlexAlgoForm


@register_model_view(ISISFlexAlgo, name='delete')
class ISISFlexAlgoDeleteView(ObjectDeleteView):
    queryset = ISISFlexAlgo.objects.all()


@register_model_view(ISISFlexAlgo, name='bulk_import', detail=False)
class ISISFlexAlgoBulkImportView(BulkImportView):
    queryset = ISISFlexAlgo.objects.all()
    model_form = ISISFlexAlgoImportForm


@register_model_view(ISISFlexAlgo, name='bulk_edit', detail=False)
class ISISFlexAlgoBulkEditView(BulkEditView):
    queryset = ISISFlexAlgo.objects.all()
    filterset = ISISFlexAlgoFilterSet
    table = ISISFlexAlgoTable
    form = ISISFlexAlgoBulkEditForm


@register_model_view(ISISFlexAlgo, name='bulk_delete', detail=False)
class ISISFlexAlgoBulkDeleteView(BulkDeleteView):
    queryset = ISISFlexAlgo.objects.all()
    filterset = ISISFlexAlgoFilterSet
    table = ISISFlexAlgoTable


# IS-IS Prefix-SID (per-interface node-SID)


@register_model_view(ISISPrefixSID, name='list', path='', detail=False)
class ISISPrefixSIDListView(ObjectListView):
    queryset = ISISPrefixSID.objects.select_related('interface__interface')
    filterset = ISISPrefixSIDFilterSet
    filterset_form = ISISPrefixSIDFilterForm
    table = ISISPrefixSIDTable


@register_model_view(ISISPrefixSID)
class ISISPrefixSIDView(ObjectView):
    queryset = ISISPrefixSID.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISPrefixSIDPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISPrefixSID, name='add', detail=False)
@register_model_view(ISISPrefixSID, name='edit')
class ISISPrefixSIDEditView(ObjectEditView):
    queryset = ISISPrefixSID.objects.all()
    form = ISISPrefixSIDForm


@register_model_view(ISISPrefixSID, name='delete')
class ISISPrefixSIDDeleteView(ObjectDeleteView):
    queryset = ISISPrefixSID.objects.all()


@register_model_view(ISISPrefixSID, name='bulk_import', detail=False)
class ISISPrefixSIDBulkImportView(BulkImportView):
    queryset = ISISPrefixSID.objects.all()
    model_form = ISISPrefixSIDImportForm


@register_model_view(ISISPrefixSID, name='bulk_edit', detail=False)
class ISISPrefixSIDBulkEditView(BulkEditView):
    queryset = ISISPrefixSID.objects.all()
    filterset = ISISPrefixSIDFilterSet
    table = ISISPrefixSIDTable
    form = ISISPrefixSIDBulkEditForm


@register_model_view(ISISPrefixSID, name='bulk_delete', detail=False)
class ISISPrefixSIDBulkDeleteView(BulkDeleteView):
    queryset = ISISPrefixSID.objects.all()
    filterset = ISISPrefixSIDFilterSet
    table = ISISPrefixSIDTable


# IS-IS SRv6 Locator (per-instance locator)


@register_model_view(ISISSRv6Locator, name='list', path='', detail=False)
class ISISSRv6LocatorListView(ObjectListView):
    queryset = ISISSRv6Locator.objects.select_related('instance__device')
    filterset = ISISSRv6LocatorFilterSet
    filterset_form = ISISSRv6LocatorFilterForm
    table = ISISSRv6LocatorTable


@register_model_view(ISISSRv6Locator)
class ISISSRv6LocatorView(ObjectView):
    queryset = ISISSRv6Locator.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISSRv6LocatorPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISSRv6Locator, name='add', detail=False)
@register_model_view(ISISSRv6Locator, name='edit')
class ISISSRv6LocatorEditView(ObjectEditView):
    queryset = ISISSRv6Locator.objects.all()
    form = ISISSRv6LocatorForm


@register_model_view(ISISSRv6Locator, name='delete')
class ISISSRv6LocatorDeleteView(ObjectDeleteView):
    queryset = ISISSRv6Locator.objects.all()


@register_model_view(ISISSRv6Locator, name='bulk_import', detail=False)
class ISISSRv6LocatorBulkImportView(BulkImportView):
    queryset = ISISSRv6Locator.objects.all()
    model_form = ISISSRv6LocatorImportForm


@register_model_view(ISISSRv6Locator, name='bulk_edit', detail=False)
class ISISSRv6LocatorBulkEditView(BulkEditView):
    queryset = ISISSRv6Locator.objects.all()
    filterset = ISISSRv6LocatorFilterSet
    table = ISISSRv6LocatorTable
    form = ISISSRv6LocatorBulkEditForm


@register_model_view(ISISSRv6Locator, name='bulk_delete', detail=False)
class ISISSRv6LocatorBulkDeleteView(BulkDeleteView):
    queryset = ISISSRv6Locator.objects.all()
    filterset = ISISSRv6LocatorFilterSet
    table = ISISSRv6LocatorTable


@register_model_view(ISISInstance, name='list', path='', detail=False)
class ISISInstanceListView(ObjectListView):
    queryset = ISISInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    table = ISISInstanceTable
    filterset = ISISInstanceFilterSet
    filterset_form = ISISInstanceFilterForm


@register_model_view(ISISInstance)
class ISISInstanceView(ObjectView):
    queryset = ISISInstance.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            ISISInstancePanel(),
            ISISInstanceSettingsPanel(title=_('Attributes')),
            SettingsChoicePanel(title=_('Settings'), choices=ISISSettingChoices),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(ISISInstance, name='interfaces')
class ISISInstanceInterfacesView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISInterface
    table = ISISInterfaceTable
    filterset = ISISInterfaceFilterSet
    tab = ViewTab(
        label=_('Interfaces'),
        badge=lambda obj: ISISInterface.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent).select_related(
            'instance__device', 'instance__vrf', 'interface'
        )

    def get_extra_context(self, request, instance):
        return {
            'form_interface_assignment': 'instance',
        }


@register_model_view(ISISInstance, name='levels')
class ISISInstanceLevelsView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISLevel
    table = ISISLevelTable
    filterset = ISISLevelFilterSet
    tab = ViewTab(
        label=_('Levels'),
        badge=lambda obj: ISISLevel.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent).select_related(
            'instance__device'
        )


@register_model_view(ISISInstance, name='flex-algos')
class ISISInstanceFlexAlgosView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISFlexAlgo
    table = ISISFlexAlgoTable
    filterset = ISISFlexAlgoFilterSet
    tab = ViewTab(
        label=_('Flex-Algos'),
        badge=lambda obj: ISISFlexAlgo.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent).select_related(
            'instance__device'
        )


@register_model_view(ISISInstance, name='srv6-locators')
class ISISInstanceSRv6LocatorsView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISSRv6Locator
    table = ISISSRv6LocatorTable
    filterset = ISISSRv6LocatorFilterSet
    tab = ViewTab(
        label=_('SRv6 Locators'),
        badge=lambda obj: ISISSRv6Locator.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent).select_related(
            'instance__device'
        )


@register_model_view(ISISInstance, 'add', detail=False)
@register_model_view(ISISInstance, name='edit')
class ISISInstanceEditView(ObjectEditView):
    queryset = ISISInstance.objects.all()
    form = ISISInstanceForm


@register_model_view(ISISInstance, name='delete')
class ISISInstanceDeleteView(ObjectDeleteView):
    queryset = ISISInstance.objects.all()


@register_model_view(ISISInstance, name='bulk_edit', detail=False)
class ISISInstanceBulkEditView(BulkEditView):
    queryset = ISISInstance.objects.all()
    filterset = ISISInstanceFilterSet
    table = ISISInstanceTable
    form = ISISInstanceBulkEditForm


@register_model_view(ISISInstance, name='bulk_delete', detail=False)
class ISISInstanceBulkDeleteView(BulkDeleteView):
    queryset = ISISInstance.objects.all()
    filterset = ISISInstanceFilterSet
    table = ISISInstanceTable


@register_model_view(ISISInstance, name='bulk_import', detail=False)
class ISISInstanceBulkImportView(BulkImportView):
    queryset = ISISInstance.objects.all()
    model_form = ISISInstanceImportForm


@register_model_view(ISISInterface, name='list', path='', detail=False)
class ISISInterfaceListView(ObjectListView):
    queryset = ISISInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'interface'
    )
    table = ISISInterfaceTable
    filterset = ISISInterfaceFilterSet
    filterset_form = ISISInterfaceFilterForm


@register_model_view(ISISInterface)
class ISISInterfaceView(ObjectView):
    queryset = ISISInterface.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            ISISInterfacePanel(),
            ISISInterfaceSettingsPanel(title=_('Interface Settings')),
            SettingsChoicePanel(title=_('Settings'), choices=ISISSettingChoices),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(ISISInterface, name='levels')
class ISISInterfaceLevelsView(ObjectChildrenView):
    queryset = ISISInterface.objects.all()
    child_model = ISISInterfaceLevel
    table = ISISInterfaceLevelTable
    filterset = ISISInterfaceLevelFilterSet
    tab = ViewTab(
        label=_('Levels'),
        badge=lambda obj: ISISInterfaceLevel.objects.filter(interface=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(interface=parent).select_related(
            'interface__interface'
        )


@register_model_view(ISISInterface, name='prefix-sids')
class ISISInterfacePrefixSidsView(ObjectChildrenView):
    queryset = ISISInterface.objects.all()
    child_model = ISISPrefixSID
    table = ISISPrefixSIDTable
    filterset = ISISPrefixSIDFilterSet
    tab = ViewTab(
        label=_('Prefix-SIDs'),
        badge=lambda obj: ISISPrefixSID.objects.filter(interface=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(interface=parent).select_related(
            'interface__interface'
        )


@register_model_view(ISISInterface, name='add', detail=False)
@register_model_view(ISISInterface, name='edit')
class ISISInterfaceEditView(ObjectEditView):
    queryset = ISISInterface.objects.all()
    form = ISISInterfaceForm


@register_model_view(ISISInterface, name='delete')
class ISISInterfaceDeleteView(ObjectDeleteView):
    queryset = ISISInterface.objects.all()


@register_model_view(ISISInterface, name='bulk_import', detail=False)
class ISISInterfaceBulkImportView(BulkImportView):
    queryset = ISISInterface.objects.all()
    model_form = ISISInterfaceImportForm


@register_model_view(ISISInterface, name='bulk_edit', detail=False)
class ISISInterfaceBulkEditView(BulkEditView):
    queryset = ISISInterface.objects.all()
    filterset = ISISInterfaceFilterSet
    table = ISISInterfaceTable
    form = ISISInterfaceBulkEditForm


@register_model_view(ISISInterface, name='bulk_delete', detail=False)
class ISISInterfaceBulkDeleteView(BulkDeleteView):
    queryset = ISISInterface.objects.all()
    filterset = ISISInterfaceFilterSet
    table = ISISInterfaceTable


ISISREDISTRIBUTION_QUERYSET = ISISRedistribution.objects.select_related(
    'instance__device',
    'instance__vrf',
    'ospf_source__device',
    'eigrp_source__device',
    'bgp_source__asn',
    'isis_source__device',
).prefetch_related('bgp_source__assigned_object')


@register_model_view(ISISRedistribution, name='list', path='', detail=False)
class ISISRedistributionListView(ObjectListView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    filterset = ISISRedistributionFilterSet
    filterset_form = ISISRedistributionFilterForm
    table = ISISRedistributionTable


@register_model_view(ISISRedistribution)
class ISISRedistributionView(ObjectView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISRedistributionPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISRedistribution, name='add', detail=False)
@register_model_view(ISISRedistribution, name='edit')
class ISISRedistributionEditView(ObjectEditView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    form = ISISRedistributionForm


@register_model_view(ISISRedistribution, name='delete')
class ISISRedistributionDeleteView(ObjectDeleteView):
    queryset = ISISREDISTRIBUTION_QUERYSET


@register_model_view(ISISRedistribution, name='bulk_import', detail=False)
class ISISRedistributionBulkImportView(BulkImportView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    model_form = ISISRedistributionImportForm


@register_model_view(ISISRedistribution, name='bulk_edit', detail=False)
class ISISRedistributionBulkEditView(BulkEditView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    filterset = ISISRedistributionFilterSet
    table = ISISRedistributionTable
    form = ISISRedistributionBulkEditForm


@register_model_view(ISISRedistribution, name='bulk_delete', detail=False)
class ISISRedistributionBulkDeleteView(BulkDeleteView):
    queryset = ISISREDISTRIBUTION_QUERYSET
    filterset = ISISRedistributionFilterSet
    table = ISISRedistributionTable


ISISSUMMARYADDRESS_QUERYSET = ISISSummaryAddress.objects.select_related(
    'instance__device', 'instance__vrf'
)


@register_model_view(ISISSummaryAddress, name='list', path='', detail=False)
class ISISSummaryAddressListView(ObjectListView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    filterset = ISISSummaryAddressFilterSet
    filterset_form = ISISSummaryAddressFilterForm
    table = ISISSummaryAddressTable


@register_model_view(ISISSummaryAddress)
class ISISSummaryAddressView(ObjectView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISSummaryAddressPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISSummaryAddress, name='add', detail=False)
@register_model_view(ISISSummaryAddress, name='edit')
class ISISSummaryAddressEditView(ObjectEditView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    form = ISISSummaryAddressForm


@register_model_view(ISISSummaryAddress, name='delete')
class ISISSummaryAddressDeleteView(ObjectDeleteView):
    queryset = ISISSUMMARYADDRESS_QUERYSET


@register_model_view(ISISSummaryAddress, name='bulk_import', detail=False)
class ISISSummaryAddressBulkImportView(BulkImportView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    model_form = ISISSummaryAddressImportForm


@register_model_view(ISISSummaryAddress, name='bulk_edit', detail=False)
class ISISSummaryAddressBulkEditView(BulkEditView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    filterset = ISISSummaryAddressFilterSet
    table = ISISSummaryAddressTable
    form = ISISSummaryAddressBulkEditForm


@register_model_view(ISISSummaryAddress, name='bulk_delete', detail=False)
class ISISSummaryAddressBulkDeleteView(BulkDeleteView):
    queryset = ISISSUMMARYADDRESS_QUERYSET
    filterset = ISISSummaryAddressFilterSet
    table = ISISSummaryAddressTable


ISISROUTELEAK_QUERYSET = ISISRouteLeak.objects.select_related(
    'instance__device', 'instance__vrf'
)


@register_model_view(ISISRouteLeak, name='list', path='', detail=False)
class ISISRouteLeakListView(ObjectListView):
    queryset = ISISROUTELEAK_QUERYSET
    filterset = ISISRouteLeakFilterSet
    filterset_form = ISISRouteLeakFilterForm
    table = ISISRouteLeakTable


@register_model_view(ISISRouteLeak)
class ISISRouteLeakView(ObjectView):
    queryset = ISISROUTELEAK_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISRouteLeakPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISRouteLeak, name='add', detail=False)
@register_model_view(ISISRouteLeak, name='edit')
class ISISRouteLeakEditView(ObjectEditView):
    queryset = ISISROUTELEAK_QUERYSET
    form = ISISRouteLeakForm


@register_model_view(ISISRouteLeak, name='delete')
class ISISRouteLeakDeleteView(ObjectDeleteView):
    queryset = ISISROUTELEAK_QUERYSET


@register_model_view(ISISRouteLeak, name='bulk_import', detail=False)
class ISISRouteLeakBulkImportView(BulkImportView):
    queryset = ISISROUTELEAK_QUERYSET
    model_form = ISISRouteLeakImportForm


@register_model_view(ISISRouteLeak, name='bulk_edit', detail=False)
class ISISRouteLeakBulkEditView(BulkEditView):
    queryset = ISISROUTELEAK_QUERYSET
    filterset = ISISRouteLeakFilterSet
    table = ISISRouteLeakTable
    form = ISISRouteLeakBulkEditForm


@register_model_view(ISISRouteLeak, name='bulk_delete', detail=False)
class ISISRouteLeakBulkDeleteView(BulkDeleteView):
    queryset = ISISROUTELEAK_QUERYSET
    filterset = ISISRouteLeakFilterSet
    table = ISISRouteLeakTable


@register_model_view(ISISInstance, name='redistributions')
class ISISInstanceRedistributionsView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISRedistribution
    table = ISISRedistributionTable
    filterset = ISISRedistributionFilterSet
    tab = ViewTab(
        label=_('Redistribution'),
        badge=lambda obj: ISISRedistribution.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISREDISTRIBUTION_QUERYSET.filter(instance=parent)


@register_model_view(ISISInstance, name='summary-addresses')
class ISISInstanceSummaryAddressesView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISSummaryAddress
    table = ISISSummaryAddressTable
    filterset = ISISSummaryAddressFilterSet
    tab = ViewTab(
        label=_('Summary Addresses'),
        badge=lambda obj: ISISSummaryAddress.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISSUMMARYADDRESS_QUERYSET.filter(instance=parent)


@register_model_view(ISISInstance, name='route-leaks')
class ISISInstanceRouteLeaksView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISRouteLeak
    table = ISISRouteLeakTable
    filterset = ISISRouteLeakFilterSet
    tab = ViewTab(
        label=_('Route Leaking'),
        badge=lambda obj: ISISRouteLeak.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISROUTELEAK_QUERYSET.filter(instance=parent)


AREA_ADDRESS_QUERYSET = ISISAreaAddress.objects.select_related('instance__device')


@register_model_view(ISISAreaAddress, name='list', path='', detail=False)
class ISISAreaAddressListView(ObjectListView):
    queryset = AREA_ADDRESS_QUERYSET
    filterset = ISISAreaAddressFilterSet
    filterset_form = ISISAreaAddressFilterForm
    table = ISISAreaAddressTable


@register_model_view(ISISAreaAddress)
class ISISAreaAddressView(ObjectView):
    queryset = AREA_ADDRESS_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISAreaAddressPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISAreaAddress, name='add', detail=False)
@register_model_view(ISISAreaAddress, name='edit')
class ISISAreaAddressEditView(ObjectEditView):
    queryset = AREA_ADDRESS_QUERYSET
    form = ISISAreaAddressForm


@register_model_view(ISISAreaAddress, name='delete')
class ISISAreaAddressDeleteView(ObjectDeleteView):
    queryset = AREA_ADDRESS_QUERYSET


@register_model_view(ISISAreaAddress, name='bulk_import', detail=False)
class ISISAreaAddressBulkImportView(BulkImportView):
    queryset = AREA_ADDRESS_QUERYSET
    model_form = ISISAreaAddressImportForm


@register_model_view(ISISAreaAddress, name='bulk_delete', detail=False)
class ISISAreaAddressBulkDeleteView(BulkDeleteView):
    queryset = AREA_ADDRESS_QUERYSET
    filterset = ISISAreaAddressFilterSet
    table = ISISAreaAddressTable


@register_model_view(ISISInstance, name='area-addresses')
class ISISInstanceAreaAddressesView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISAreaAddress
    table = ISISAreaAddressTable
    filterset = ISISAreaAddressFilterSet
    tab = ViewTab(
        label=_('Area Addresses'),
        badge=lambda obj: ISISAreaAddress.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return AREA_ADDRESS_QUERYSET.filter(instance=parent)


ISISSRMAPPINGENTRY_QUERYSET = ISISSRMappingEntry.objects.select_related(
    'instance__device'
)


@register_model_view(ISISSRMappingEntry, name='list', path='', detail=False)
class ISISSRMappingEntryListView(ObjectListView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    filterset = ISISSRMappingEntryFilterSet
    filterset_form = ISISSRMappingEntryFilterForm
    table = ISISSRMappingEntryTable


@register_model_view(ISISSRMappingEntry)
class ISISSRMappingEntryView(ObjectView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISSRMappingEntryPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISSRMappingEntry, name='add', detail=False)
@register_model_view(ISISSRMappingEntry, name='edit')
class ISISSRMappingEntryEditView(ObjectEditView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    form = ISISSRMappingEntryForm


@register_model_view(ISISSRMappingEntry, name='delete')
class ISISSRMappingEntryDeleteView(ObjectDeleteView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET


@register_model_view(ISISSRMappingEntry, name='bulk_import', detail=False)
class ISISSRMappingEntryBulkImportView(BulkImportView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    model_form = ISISSRMappingEntryImportForm


@register_model_view(ISISSRMappingEntry, name='bulk_edit', detail=False)
class ISISSRMappingEntryBulkEditView(BulkEditView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    filterset = ISISSRMappingEntryFilterSet
    table = ISISSRMappingEntryTable
    form = ISISSRMappingEntryBulkEditForm


@register_model_view(ISISSRMappingEntry, name='bulk_delete', detail=False)
class ISISSRMappingEntryBulkDeleteView(BulkDeleteView):
    queryset = ISISSRMAPPINGENTRY_QUERYSET
    filterset = ISISSRMappingEntryFilterSet
    table = ISISSRMappingEntryTable


ISISADJACENCYSID_QUERYSET = ISISAdjacencySID.objects.select_related(
    'interface__interface'
)


@register_model_view(ISISAdjacencySID, name='list', path='', detail=False)
class ISISAdjacencySIDListView(ObjectListView):
    queryset = ISISADJACENCYSID_QUERYSET
    filterset = ISISAdjacencySIDFilterSet
    filterset_form = ISISAdjacencySIDFilterForm
    table = ISISAdjacencySIDTable


@register_model_view(ISISAdjacencySID)
class ISISAdjacencySIDView(ObjectView):
    queryset = ISISADJACENCYSID_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISAdjacencySIDPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISAdjacencySID, name='add', detail=False)
@register_model_view(ISISAdjacencySID, name='edit')
class ISISAdjacencySIDEditView(ObjectEditView):
    queryset = ISISADJACENCYSID_QUERYSET
    form = ISISAdjacencySIDForm


@register_model_view(ISISAdjacencySID, name='delete')
class ISISAdjacencySIDDeleteView(ObjectDeleteView):
    queryset = ISISADJACENCYSID_QUERYSET


@register_model_view(ISISAdjacencySID, name='bulk_import', detail=False)
class ISISAdjacencySIDBulkImportView(BulkImportView):
    queryset = ISISADJACENCYSID_QUERYSET
    model_form = ISISAdjacencySIDImportForm


@register_model_view(ISISAdjacencySID, name='bulk_edit', detail=False)
class ISISAdjacencySIDBulkEditView(BulkEditView):
    queryset = ISISADJACENCYSID_QUERYSET
    filterset = ISISAdjacencySIDFilterSet
    table = ISISAdjacencySIDTable
    form = ISISAdjacencySIDBulkEditForm


@register_model_view(ISISAdjacencySID, name='bulk_delete', detail=False)
class ISISAdjacencySIDBulkDeleteView(BulkDeleteView):
    queryset = ISISADJACENCYSID_QUERYSET
    filterset = ISISAdjacencySIDFilterSet
    table = ISISAdjacencySIDTable


@register_model_view(ISISInstance, name='sr-mapping-entries')
class ISISInstanceSRMappingEntriesView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISSRMappingEntry
    table = ISISSRMappingEntryTable
    filterset = ISISSRMappingEntryFilterSet
    tab = ViewTab(
        label=_('SR Mapping Entries'),
        badge=lambda obj: ISISSRMappingEntry.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISSRMAPPINGENTRY_QUERYSET.filter(instance=parent)


@register_model_view(ISISInterface, name='adjacency-sids')
class ISISInterfaceAdjacencySidsView(ObjectChildrenView):
    queryset = ISISInterface.objects.all()
    child_model = ISISAdjacencySID
    table = ISISAdjacencySIDTable
    filterset = ISISAdjacencySIDFilterSet
    tab = ViewTab(
        label=_('Adjacency-SIDs'),
        badge=lambda obj: ISISAdjacencySID.objects.filter(interface=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISADJACENCYSID_QUERYSET.filter(interface=parent)


ISISADDRESSFAMILY_QUERYSET = ISISAddressFamily.objects.select_related(
    'instance__device'
)


@register_model_view(ISISAddressFamily, name='list', path='', detail=False)
class ISISAddressFamilyListView(ObjectListView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    filterset = ISISAddressFamilyFilterSet
    filterset_form = ISISAddressFamilyFilterForm
    table = ISISAddressFamilyTable


@register_model_view(ISISAddressFamily)
class ISISAddressFamilyView(ObjectView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[ISISAddressFamilyPanel(), TagsPanel()],
        right_panels=[panels.CommentsPanel(), panels.RelatedObjectsPanel()],
    )


@register_model_view(ISISAddressFamily, name='add', detail=False)
@register_model_view(ISISAddressFamily, name='edit')
class ISISAddressFamilyEditView(ObjectEditView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    form = ISISAddressFamilyForm


@register_model_view(ISISAddressFamily, name='delete')
class ISISAddressFamilyDeleteView(ObjectDeleteView):
    queryset = ISISADDRESSFAMILY_QUERYSET


@register_model_view(ISISAddressFamily, name='bulk_import', detail=False)
class ISISAddressFamilyBulkImportView(BulkImportView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    model_form = ISISAddressFamilyImportForm


@register_model_view(ISISAddressFamily, name='bulk_edit', detail=False)
class ISISAddressFamilyBulkEditView(BulkEditView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    filterset = ISISAddressFamilyFilterSet
    table = ISISAddressFamilyTable
    form = ISISAddressFamilyBulkEditForm


@register_model_view(ISISAddressFamily, name='bulk_delete', detail=False)
class ISISAddressFamilyBulkDeleteView(BulkDeleteView):
    queryset = ISISADDRESSFAMILY_QUERYSET
    filterset = ISISAddressFamilyFilterSet
    table = ISISAddressFamilyTable


@register_model_view(ISISInstance, name='address-families')
class ISISInstanceAddressFamiliesView(ObjectChildrenView):
    queryset = ISISInstance.objects.all()
    child_model = ISISAddressFamily
    table = ISISAddressFamilyTable
    filterset = ISISAddressFamilyFilterSet
    tab = ViewTab(
        label=_('Address Families'),
        badge=lambda obj: ISISAddressFamily.objects.filter(instance=obj).count(),
        hide_if_empty=False,
    )

    def get_children(self, request, parent):
        return ISISADDRESSFAMILY_QUERYSET.filter(instance=parent)
