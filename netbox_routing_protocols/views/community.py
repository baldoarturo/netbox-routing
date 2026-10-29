from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

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

from netbox_routing_protocols.filtersets.community import *
from netbox_routing_protocols.helpers.prefix_list import community_list_references
from netbox_routing_protocols.views.objects import (
    reference_groups,
    references_message,
)
from netbox_routing_protocols.forms.community import *
from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.tables.community import *
from netbox_routing_protocols.ui import *

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

    def get(self, request, *args, **kwargs):
        # A list in use can be deleted: the confirmation says what stops referencing it
        response = super().get(request, *args, **kwargs)
        groups = reference_groups(
            request, [self.get_object(**kwargs)], references=community_list_references
        )
        marker = b'<div class="modal-body">'
        if groups and getattr(response, 'content', None) and marker in response.content:
            warning = render_to_string(
                'netbox_routing_protocols/panels/prefix_list_references.html',
                {'groups': groups, 'kind': _('community list')},
                request=request,
            )
            response.content = response.content.replace(
                marker, marker + warning.encode(), 1
            )
        return response


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
    filterset = CommunityListFilterSet
    form = CommunityListBulkEditForm
    table = CommunityListTable


@register_model_view(CommunityList, name='bulk_delete', detail=False)
class CommunityListBulkDeleteView(BulkDeleteView):
    queryset = CommunityList.objects.select_related('tenant')
    filterset = CommunityListFilterSet
    table = CommunityListTable

    def post(self, request, **kwargs):
        # The confirmation page of the selection says what stops referencing the lists
        if '_confirm' not in request.POST:
            if request.POST.get('_all'):
                lists = self.filterset(request.GET, CommunityList.objects.all()).qs
            else:
                pks = [int(pk) for pk in request.POST.getlist('pk')]
                lists = CommunityList.objects.filter(pk__in=pks)
            groups = reference_groups(
                request, lists, references=community_list_references
            )
            if groups:
                messages.warning(
                    request, references_message(groups, kind='community lists')
                )
        return super().post(request, **kwargs)


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
    filterset = CommunityFilterSet
    form = CommunityBulkEditForm
    table = CommunityTable


@register_model_view(Community, name='bulk_delete', detail=False)
class CommunityBulkDeleteView(BulkDeleteView):
    queryset = Community.objects.select_related('role', 'tenant')
    filterset = CommunityFilterSet
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
    filterset = CommunityListEntryFilterSet
    form = CommunityListEntryBulkEditForm
    table = CommunityListEntryTable


@register_model_view(CommunityListEntry, name='bulk_delete', detail=False)
class CommunityListEntryBulkDeleteView(BulkDeleteView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    filterset = CommunityListEntryFilterSet
    table = CommunityListEntryTable


@register_model_view(CommunityListEntry, name='bulk_import', detail=False)
class CommunityListEntryBulkImportView(BulkImportView):
    queryset = CommunityListEntry.objects.select_related('community_list', 'community')
    model_form = CommunityListEntryImportForm
