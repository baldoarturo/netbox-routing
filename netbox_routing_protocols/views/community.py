from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from extras.ui.panels import TagsPanel
from netbox.object_actions import CloneObject, DeleteObject, EditObject
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
from netbox.ui.actions import AddObject
from utilities.query import count_related
from utilities.views import (
    ContentTypePermissionRequiredMixin,
    GetRelatedModelsMixin,
    ViewTab,
    register_model_view,
)

from netbox_routing_protocols.filtersets.community import *
from netbox_routing_protocols.helpers import community as community_helpers
from netbox_routing_protocols.helpers.prefix_list import community_list_references
from netbox_routing_protocols.models.objects import RoutePolicyEntry
from netbox_routing_protocols.views.objects import (
    DuplicatePrefixList,
    reference_groups,
    references_message,
)
from netbox_routing_protocols.forms.community import *
from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.tables.community import *
from netbox_routing_protocols.ui import *

__all__ = (
    'CommunityMatchView',
    'CommunityListDuplicateView',
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
    queryset = CommunityList.objects.select_related('tenant').annotate(
        entry_count=count_related(CommunityListEntry, 'community_list'),
        route_policy_entry_count=count_related(
            RoutePolicyEntry, 'match_community_list'
        ),
    )
    table = CommunityListTable
    filterset = CommunityListFilterSet
    filterset_form = CommunityListFilterForm


class DuplicateCommunityList(DuplicatePrefixList):
    """A copy of the community list with its entries"""


@register_model_view(CommunityList)
class CommunityListDetailView(GetRelatedModelsMixin, ObjectView):
    queryset = CommunityList.objects.select_related('tenant')
    actions = (
        DuplicateCommunityList,
        CloneObject,
        EditObject,
        DeleteObject,
    )
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
        bottom_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_protocols.CommunityListEntry',
                title=_('Entries'),
                filters={'community_list_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'community_list'],
                actions=[
                    AddObject(
                        'netbox_routing_protocols.CommunityListEntry',
                        label=_('Add entry'),
                        url_params={'community_list': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        # Where the list is used: the route policy entries that match it (a many to many
        # relation is not detected by NetBox)
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                extra=(
                    (
                        RoutePolicyEntry.objects.restrict(request.user, 'view').filter(
                            match_community_list=instance
                        ),
                        'match_community_list_id',
                    ),
                ),
            )
        }


@register_model_view(CommunityList, name='duplicate')
class CommunityListDuplicateView(ContentTypePermissionRequiredMixin, View):
    """Copy a community list with its entries, in one transaction"""

    template_name = 'netbox_routing_protocols/communitylist_duplicate.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.add_communitylist'

    def _source(self, request, pk):
        return get_object_or_404(
            CommunityList.objects.restrict(request.user, 'view'), pk=pk
        )

    def _render(self, request, source, form):
        return render(
            request,
            self.template_name,
            {
                'object': source,
                'form': form,
                'count': source.communitylistentries.count(),
            },
        )

    def get(self, request, pk):
        source = self._source(request, pk)
        form = CommunityListDuplicateForm(
            initial={
                'name': _('%(name)s copy') % {'name': source.name},
                'description': source.description,
            }
        )
        return self._render(request, source, form)

    def post(self, request, pk):
        source = self._source(request, pk)
        form = CommunityListDuplicateForm(request.POST)
        if not request.user.has_perm('netbox_routing_protocols.add_communitylistentry'):
            messages.error(request, _('You cannot add community list entries.'))
            return redirect(source.get_absolute_url())
        if not form.is_valid():
            return self._render(request, source, form)

        with transaction.atomic():
            copy = CommunityList(
                name=form.cleaned_data['name'],
                type=source.type,
                tenant=source.tenant,
                description=form.cleaned_data['description'],
                comments=source.comments,
                owner=source.owner,
            )
            copy.full_clean()
            copy.save()
            copy.tags.set(source.tags.all())
            for entry in source.communitylistentries.all():
                new_entry = CommunityListEntry(
                    community_list=copy,
                    sequence=entry.sequence,
                    action=entry.action,
                    community=entry.community,
                    description=entry.description,
                    comments=entry.comments,
                    owner=entry.owner,
                )
                new_entry.full_clean()
                new_entry.save()
                new_entry.tags.set(entry.tags.all())
        messages.success(
            request,
            _('Duplicated %(source)s as %(copy)s with %(count)d entries.')
            % {
                'source': source,
                'copy': copy,
                'count': source.communitylistentries.count(),
            },
        )
        return redirect(copy.get_absolute_url())


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
        return self.child_model.objects.filter(community_list=parent).select_related(
            'community_list', 'community'
        )


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
    queryset = Community.objects.select_related('role', 'tenant').annotate(
        entry_count=count_related(CommunityListEntry, 'community'),
        route_policy_entry_count=count_related(RoutePolicyEntry, 'match_community'),
    )
    table = CommunityTable
    filterset = CommunityFilterSet
    filterset_form = CommunityFilterForm


@register_model_view(Community)
class CommunityDetailView(GetRelatedModelsMixin, ObjectView):
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

    def get_extra_context(self, request, instance):
        # Where the community is used: the lists that contain it and the route policy
        # entries that match it (the entries of the lists are found by NetBox; a many to
        # many relation is not)
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                extra=(
                    (
                        CommunityList.objects.restrict(request.user, 'view')
                        .filter(communitylistentries__community=instance)
                        .distinct(),
                        'community_id',
                    ),
                    (
                        RoutePolicyEntry.objects.restrict(request.user, 'view').filter(
                            match_community=instance
                        ),
                        'match_community_id',
                    ),
                ),
            )
        }


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


#
# Community match: which entries of the community lists match the communities of a route
#
class CommunityMatchView(ContentTypePermissionRequiredMixin, View):
    template_name = 'netbox_routing_protocols/community_match.html'
    partial_name = 'netbox_routing_protocols/community_match_results.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.view_communitylistentry'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        show_all = request.GET.get('all') in ('1', 'on', 'true')
        context = {'q': query, 'show_all': show_all}
        if query:
            context.update(self.evaluate(request, query, show_all))
        # HTMX asks for the results only, a normal request for the whole page
        template = self.partial_name if request.htmx else self.template_name
        return render(request, template, context)

    @staticmethod
    def evaluate(request, query, show_all):
        try:
            values = community_helpers.parse_communities(query)
        except ValidationError as e:
            return {'error': e.messages[0]}

        lists = CommunityList.objects.restrict(request.user, 'view')
        entries = (
            CommunityListEntry.objects.restrict(request.user, 'view')
            .filter(community_list__in=lists, community__community__in=values)
            .select_related('community_list', 'community')
        )
        results = [
            {
                'community_list': community_list,
                'rows': [
                    {'entry': entry, 'effective': effective}
                    for entry, effective in rows
                ],
            }
            for community_list, rows in community_helpers.evaluate_communities(
                values, entries
            )
        ]
        context = {'communities': values, 'results': results}
        if show_all:
            matched = [result['community_list'].pk for result in results]
            context['unmatched'] = lists.exclude(pk__in=matched)
        return context
