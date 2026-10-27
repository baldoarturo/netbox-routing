from extras.ui.panels import TagsPanel
from netbox.views.generic import (
    ObjectListView,
    ObjectView,
    ObjectEditView,
    ObjectDeleteView,
    ObjectChildrenView,
    BulkEditView,
    BulkDeleteView,
    BulkImportView,
)
from netbox.ui import panels, layout
from utilities.views import register_model_view, ViewTab

from netbox_routing.filtersets.community import *
from netbox_routing.forms.community import *
from netbox_routing.models.community import *
from netbox_routing.tables.community import *
from netbox_routing.ui import *

__all__ = (
    'CommunityListListView',
    'CommunityListDetailView',
    'CommunityListEditView',
    'CommunityListDeleteView',
    'CommunityListEntriesView',
    'CommunityListBulkEditView',
    'CommunityListBulkDeleteView',
    'CommunityListBulkImportView',
    'CommunityListView',
    'CommunityDetailView',
    'CommunityEditView',
    'CommunityDeleteView',
    'CommunityBulkEditView',
    'CommunityBulkDeleteView',
    'CommunityBulkImportView',
    'CommunityListEntryListView',
    'CommunityListEntryDetailView',
    'CommunityListEntryEditView',
    'CommunityListEntryDeleteView',
    'CommunityListEntryBulkEditView',
    'CommunityListEntryBulkDeleteView',
    'CommunityListEntryBulkImportView',
)


#
# Prefix List
#
@register_model_view(CommunityList, name='list', path='', detail=False)
class CommunityListListView(ObjectListView):
    queryset = CommunityList.objects.select_related('tenant')
    table = CommunityListTable
    filterset = CommunityListFilterSet
    filterset_form = CommunityListFilterForm


@register_model_view(CommunityList)
class CommunityListDetailView(ObjectView):
    queryset = CommunityList.objects.select_related('tenant')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            CommunityListPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(CommunityList, name='add', detail=False)
@register_model_view(CommunityList, name='edit')
class CommunityListEditView(ObjectEditView):
    queryset = CommunityList.objects.select_related('tenant')
    form = CommunityListForm


@register_model_view(CommunityList, name='delete')
class CommunityListDeleteView(ObjectDeleteView):
    queryset = CommunityList.objects.select_related('tenant')


@register_model_view(CommunityList, name='entries')
class CommunityListEntriesView(ObjectChildrenView):
    queryset = CommunityList.objects.select_related('tenant')
    child_model = CommunityListEntry
    table = CommunityListEntryTable
    filterset = CommunityListEntryFilterSet
    filterset_form = CommunityListEntryFilterForm
    actions = ObjectChildrenView.actions
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: CommunityListEntriesView.child_model.objects.filter(
            community_list=obj
        ).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(community_list=parent)


@register_model_view(CommunityList, name='bulk_edit', detail=False)
class CommunityListBulkEditView(BulkEditView):
    queryset = CommunityList.objects.select_related('tenant')
    filterset = CommunityListFilterForm
    form = CommunityListBulkEditForm
    table = CommunityListTable


@register_model_view(CommunityList, name='bulk_delete', detail=False)
class CommunityListBulkDeleteView(BulkDeleteView):
    queryset = CommunityList.objects.select_related('tenant')
    filterset = CommunityListFilterForm
    table = CommunityListTable


@register_model_view(CommunityList, name='bulk_import', detail=False)
class CommunityListBulkImportView(BulkImportView):
    queryset = CommunityList.objects.select_related('tenant')
    model_form = CommunityListImportForm


#
# Community
#


@register_model_view(Community, name='list', path='', detail=False)
class CommunityListView(ObjectListView):
    queryset = Community.objects.select_related('role', 'tenant')
    table = CommunityTable
    filterset = CommunityFilterSet
    filterset_form = CommunityFilterForm


@register_model_view(Community)
class CommunityDetailView(ObjectView):
    queryset = Community.objects.select_related('role', 'tenant')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            CommunityPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(Community, name='add', detail=False)
@register_model_view(Community, name='edit')
class CommunityEditView(ObjectEditView):
    queryset = Community.objects.select_related('role', 'tenant')
    form = CommunityForm


@register_model_view(Community, name='delete')
class CommunityDeleteView(ObjectDeleteView):
    queryset = Community.objects.select_related('role', 'tenant')


@register_model_view(Community, name='bulk_edit', detail=False)
class CommunityBulkEditView(BulkEditView):
    queryset = Community.objects.select_related('role', 'tenant')
    filterset = CommunityFilterForm
    form = CommunityBulkEditForm
    table = CommunityTable


@register_model_view(Community, name='bulk_delete', detail=False)
class CommunityBulkDeleteView(BulkDeleteView):
    queryset = Community.objects.select_related('role', 'tenant')
    filterset = CommunityFilterForm
    table = CommunityTable


@register_model_view(Community, name='bulk_import', detail=False)
class CommunityBulkImportView(BulkImportView):
    queryset = Community.objects.select_related('role', 'tenant')
    model_form = CommunityImportForm


#
# Community List Entry
#


@register_model_view(CommunityListEntry, name='list', path='', detail=False)
class CommunityListEntryListView(ObjectListView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    table = CommunityListEntryTable
    filterset = CommunityListEntryFilterSet
    filterset_form = CommunityListEntryFilterForm


@register_model_view(CommunityListEntry)
class CommunityListEntryDetailView(ObjectView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            CommunityListEntryPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(CommunityListEntry, name='add', detail=False)
@register_model_view(CommunityListEntry, name='edit')
class CommunityListEntryEditView(ObjectEditView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    form = CommunityListEntryForm


@register_model_view(CommunityListEntry, name='delete')
class CommunityListEntryDeleteView(ObjectDeleteView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')


@register_model_view(CommunityListEntry, name='bulk_edit', detail=False)
class CommunityListEntryBulkEditView(BulkEditView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    filterset = CommunityListEntryFilterForm
    form = CommunityListEntryBulkEditForm
    table = CommunityListEntryTable


@register_model_view(CommunityListEntry, name='bulk_delete', detail=False)
class CommunityListEntryBulkDeleteView(BulkDeleteView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    filterset = CommunityListEntryFilterForm
    table = CommunityListEntryTable


@register_model_view(CommunityListEntry, name='bulk_import', detail=False)
class CommunityListEntryBulkImportView(BulkImportView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    model_form = CommunityListEntryImportForm
