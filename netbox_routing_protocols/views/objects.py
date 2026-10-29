import netaddr
from django.db.models import Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from extras.ui.panels import TagsPanel
from netbox.views.generic import (
    ObjectListView,
    ObjectView,
    ObjectEditView,
    ObjectDeleteView,
    ObjectChildrenView,
    BulkDeleteView,
    BulkEditView,
    BulkImportView,
)
from netbox.ui import actions, panels, layout
from utilities.query import count_related
from utilities.views import (
    ContentTypePermissionRequiredMixin,
    GetRelatedModelsMixin,
    ViewTab,
    register_model_view,
)
from netbox_routing_protocols.helpers.prefix_list import (
    describe_entry,
    evaluate_prefix,
    find_overlaps,
)
from netbox_routing_protocols.filtersets.objects import *
from netbox_routing_protocols.forms.objects import *
from netbox_routing_protocols.models import Community, CommunityList
from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.tables.objects import *
from netbox_routing_protocols.ui import *


#
# Prefix List
#
@register_model_view(PrefixList, name='list', path='', detail=False)
class PrefixListListView(ObjectListView):
    queryset = PrefixList.objects.annotate(
        entry_count=count_related(PrefixListEntry, 'prefix_list')
    )
    table = PrefixListTable
    filterset = PrefixListFilterSet
    filterset_form = PrefixListFilterForm


@register_model_view(PrefixList)
class PrefixListView(GetRelatedModelsMixin, ObjectView):
    queryset = PrefixList.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            PrefixListPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
        bottom_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_protocols.PrefixListEntry',
                title=_('Entries'),
                filters={'prefix_list_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'prefix_list'],
                actions=[
                    actions.AddObject(
                        'netbox_routing_protocols.PrefixListEntry',
                        label=_('Add entry'),
                        url_params={'prefix_list': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        # Where the list is used: its entries, the route map entries that match it and
        # the BGP policy templates and peer address families that filter with it
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                # a many to many relation is not detected by NetBox
                extra=(
                    (
                        RouteMapEntry.objects.restrict(request.user, 'view').filter(
                            match_prefix_list=instance
                        ),
                        'match_prefix_list_id',
                    ),
                ),
            )
        }


@register_model_view(PrefixList, name='entries')
class PrefixListEntriesView(ObjectChildrenView):
    queryset = PrefixList.objects.all()
    child_model = PrefixListEntry
    table = PrefixListEntryTable
    filterset = PrefixListEntryFilterSet
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: PrefixListEntry.objects.filter(prefix_list=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(prefix_list=parent).select_related(
            'prefix_list', 'prefix'
        )

    def get_extra_context(self, request, instance):
        return {
            'url_parent': 'plugins:netbox_routing_protocols:prefixlist_entries',
            'url_add': 'plugins:netbox_routing_protocols:prefixlistentry_add',
            'url_bulk_edit': 'plugins:netbox_routing_protocols:prefixlistentry_bulk_edit',
            'url_bulk_delete': 'plugins:netbox_routing_protocols:prefixlistentry_bulk_delete',
            'parent_name': 'prefix_list',
            'parent_view': 'prefixlist',
            'parent_view_path': 'entries',
            'view': 'prefixlistentry',
        }


@register_model_view(PrefixList, name='add', detail=False)
@register_model_view(PrefixList, name='edit')
class PrefixListEditView(ObjectEditView):
    queryset = PrefixList.objects.all()
    form = PrefixListForm


@register_model_view(PrefixList, name='delete')
class PrefixListDeleteView(ObjectDeleteView):
    queryset = PrefixList.objects.all()


@register_model_view(PrefixList, name='bulk_import', detail=False)
class PrefixListBulkImportView(BulkImportView):
    queryset = PrefixList.objects.all()
    model_form = PrefixListImportForm


@register_model_view(PrefixList, name='bulk_edit', detail=False)
class PrefixListBulkEditView(BulkEditView):
    queryset = PrefixList.objects.annotate(
        entry_count=count_related(PrefixListEntry, 'prefix_list')
    )
    filterset = PrefixListFilterSet
    form = PrefixListBulkEditForm
    table = PrefixListTable


@register_model_view(PrefixList, name='bulk_delete', detail=False)
class PrefixListBulkDeleteView(BulkDeleteView):
    queryset = PrefixList.objects.annotate(
        entry_count=count_related(PrefixListEntry, 'prefix_list')
    )
    filterset = PrefixListFilterSet
    table = PrefixListTable


#
# Prefix List Entry
#


@register_model_view(PrefixListEntry, name='list', path='', detail=False)
class PrefixListEntryListView(ObjectListView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    table = PrefixListEntryTable
    filterset = PrefixListEntryFilterSet
    filterset_form = PrefixListEntryFilterForm


@register_model_view(PrefixListEntry)
class PrefixListEntryView(ObjectView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            PrefixListEntryPanel(),
            TagsPanel(),
        ],
        right_panels=[
            OverlapsPanel(title=_('Overlapping entries')),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )

    def get_extra_context(self, request, instance):
        return {'overlaps': find_overlaps(instance)}


@register_model_view(PrefixListEntry, name='add', detail=False)
@register_model_view(PrefixListEntry, name='edit')
class PrefixListEntryEditView(ObjectEditView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    form = PrefixListEntryForm


@register_model_view(PrefixListEntry, name='bulk_import', detail=False)
class PrefixListEntryBulkImportView(BulkImportView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    model_form = PrefixListEntryImportForm


@register_model_view(PrefixListEntry, name='delete')
class PrefixListEntryDeleteView(ObjectDeleteView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')


@register_model_view(PrefixListEntry, name='bulk_edit', detail=False)
class PrefixListEntryBulkEditView(BulkEditView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    filterset = PrefixListEntryFilterSet
    table = PrefixListEntryTable
    form = PrefixListEntryBulkEditForm


@register_model_view(PrefixListEntry, name='bulk_delete', detail=False)
class PrefixListEntryBulkDeleteView(BulkDeleteView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    filterset = PrefixListEntryFilterSet
    table = PrefixListEntryTable


#
# Prefix match: which entries of the prefix lists match a prefix
#
class PrefixMatchView(ContentTypePermissionRequiredMixin, View):
    template_name = 'netbox_routing_protocols/prefix_match.html'
    partial_name = 'netbox_routing_protocols/prefix_match_results.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.view_prefixlistentry'

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
            prefix = netaddr.IPNetwork(query).cidr
        except (netaddr.AddrFormatError, ValueError, TypeError):
            return {
                'error': _('"%(query)s" is not a valid prefix or address.')
                % {'query': query}
            }

        lists = PrefixList.objects.restrict(request.user, 'view').filter(
            family=prefix.version
        )
        entries = (
            PrefixListEntry.objects.restrict(request.user, 'view')
            .filter(prefix_list__in=lists)
            .filter(
                Q(any_prefix=True)
                | Q(prefix__prefix__net_contains_or_equals=str(prefix))
            )
            .select_related('prefix_list', 'prefix')
        )
        results = [
            {
                'prefix_list': prefix_list,
                'rows': [
                    {
                        'entry': entry,
                        'effective': effective,
                        'text': describe_entry(entry),
                    }
                    for entry, effective in rows
                ],
            }
            for prefix_list, rows in evaluate_prefix(prefix, entries)
        ]
        context = {'prefix': prefix, 'results': results}
        if show_all:
            matched = [result['prefix_list'].pk for result in results]
            context['unmatched'] = lists.exclude(pk__in=matched)
        return context


#
# Route Map
#
@register_model_view(RouteMap, name='list', path='', detail=False)
class RouteMapListView(ObjectListView):
    queryset = RouteMap.objects.all()
    table = RouteMapTable
    filterset = RouteMapFilterSet
    filterset_form = RouteMapFilterForm


@register_model_view(RouteMap)
class RouteMapView(ObjectView):
    queryset = RouteMap.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RouteMapPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(RouteMap, name='entries')
class RouteMapEntriesView(ObjectChildrenView):
    queryset = RouteMap.objects.all()
    child_model = RouteMapEntry
    table = RouteMapEntryTable
    filterset = RouteMapEntryFilterSet
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: RouteMapEntry.objects.filter(route_map=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(route_map=parent)

    def get_extra_context(self, request, instance):
        return {
            'url_parent': 'plugins:netbox_routing_protocols:routemap_entries',
            'url_add': 'plugins:netbox_routing_protocols:routemapentry_add',
            'url_bulk_edit': 'plugins:netbox_routing_protocols:routemapentry_bulk_edit',
            'url_bulk_delete': 'plugins:netbox_routing_protocols:routemapentry_bulk_delete',
            'parent_name': 'route_map',
            'parent_view': 'routemap',
            'parent_view_path': 'entries',
            'view': 'routemapentry',
        }


@register_model_view(RouteMap, name='add', detail=False)
@register_model_view(RouteMap, name='edit')
class RouteMapEditView(ObjectEditView):
    queryset = RouteMap.objects.all()
    form = RouteMapForm


@register_model_view(RouteMap, name='delete')
class RouteMapDeleteView(ObjectDeleteView):
    queryset = RouteMap.objects.all()


@register_model_view(RouteMap, name='bulk_edit', detail=False)
class RouteMapBulkEditView(BulkEditView):
    queryset = RouteMap.objects.all()
    filterset = RouteMapFilterSet
    form = RouteMapBulkEditForm
    table = RouteMapTable


@register_model_view(RouteMap, name='bulk_delete', detail=False)
class RouteMapBulkDeleteView(BulkDeleteView):
    queryset = RouteMap.objects.all()
    filterset = RouteMapFilterSet
    table = RouteMapTable


#
# Route Map Entry
#
@register_model_view(RouteMapEntry, name='list', path='', detail=False)
class RouteMapEntryListView(ObjectListView):
    queryset = RouteMapEntry.objects.select_related('route_map')
    table = RouteMapEntryTable
    filterset = RouteMapEntryFilterSet
    filterset_form = RouteMapEntryFilterForm


@register_model_view(RouteMapEntry)
class RouteMapEntryView(GetRelatedModelsMixin, ObjectView):
    queryset = RouteMapEntry.objects.select_related('route_map')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RouteMapEntryPanel(title=_('Route Map Entry')),
            RouteMapEntryMatchPanel(title=_('Match Actions')),
            panels.JSONPanel('match', title=_('Match Parameters'), copy_button=True),
            RouteMapEntrySetPanel(title=_('Set Actions')),
            panels.JSONPanel('set', title=_('Set Parameters'), copy_button=True),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )

    def get_extra_context(self, request, instance):
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                omit='route_map',
                extra=(
                    (
                        PrefixList.objects.restrict(request.user, 'view').filter(
                            route_map_entries=instance
                        ),
                        'route_map_entry_id',
                    ),
                    (
                        CommunityList.objects.restrict(request.user, 'view').filter(
                            route_map_entries=instance
                        ),
                        'route_map_entry_id',
                    ),
                    (
                        Community.objects.restrict(request.user, 'view').filter(
                            route_map_entries=instance
                        ),
                        'route_map_entry_id',
                    ),
                    (
                        ASPath.objects.restrict(request.user, 'view').filter(
                            route_map_entries=instance
                        ),
                        'route_map_entry_id',
                    ),
                ),
            ),
        }


@register_model_view(RouteMapEntry, name='add', detail=False)
@register_model_view(RouteMapEntry, name='edit')
class RouteMapEntryEditView(ObjectEditView):
    queryset = RouteMapEntry.objects.select_related('route_map')
    form = RouteMapEntryForm


@register_model_view(RouteMapEntry, name='delete')
class RouteMapEntryDeleteView(ObjectDeleteView):
    queryset = RouteMapEntry.objects.select_related('route_map')


@register_model_view(RouteMapEntry, name='bulk_edit', detail=False)
class RouteMapEntryBulkEditView(BulkEditView):
    queryset = RouteMapEntry.objects.select_related('route_map')
    filterset = RouteMapEntryFilterSet
    table = RouteMapEntryTable
    form = RouteMapEntryBulkEditForm


@register_model_view(RouteMapEntry, name='bulk_delete', detail=False)
class RouteMapEntryBulkDeleteView(BulkDeleteView):
    queryset = RouteMapEntry.objects.select_related('route_map')
    filterset = RouteMapEntryFilterSet
    table = RouteMapEntryTable


#
# AS Path
#
@register_model_view(ASPath, name='list', path='', detail=False)
class ASPathListView(ObjectListView):
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    filterset_form = ASPathFilterForm
    table = ASPathTable


@register_model_view(ASPath)
class ASPathView(ObjectView):
    queryset = ASPath.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            ASPathPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(ASPath, name='add', detail=False)
@register_model_view(ASPath, name='edit')
class ASPathEditView(ObjectEditView):
    queryset = ASPath.objects.all()
    form = ASPathForm


@register_model_view(ASPath, name='delete')
class ASPathDeleteView(ObjectDeleteView):
    queryset = ASPath.objects.all()


@register_model_view(ASPath, name='bulk_edit', detail=False)
class ASPathBulkEditView(BulkEditView):
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    form = ASPathBulkEditForm
    table = ASPathTable


@register_model_view(ASPath, name='bulk_delete', detail=False)
class ASPathBulkDeleteView(BulkDeleteView):
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    table = ASPathTable


@register_model_view(ASPath, name='entries')
class ASPathEntriesView(ObjectChildrenView):
    queryset = ASPath.objects.all()
    child_model = ASPathEntry
    table = ASPathEntryTable
    filterset = ASPathEntryFilterSet
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: ASPathEntry.objects.filter(aspath=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(aspath=parent)

    def get_extra_context(self, request, instance):
        print(self.actions)

        return {
            'url_parent': 'plugins:netbox_routing_protocols:aspath_entries',
            'url_add': 'plugins:netbox_routing_protocols:aspathentry_add',
            'url_bulk_edit': 'plugins:netbox_routing_protocols:aspathentry_bulk_edit',
            'url_bulk_delete': 'plugins:netbox_routing_protocols:aspathentry_bulk_delete',
            'parent_name': 'aspath',
            'parent_view': 'aspath',
            'parent_view_path': 'entries',
            'view': 'aspathentry',
        }


#
# Route Map Entry
#
@register_model_view(ASPathEntry, name='list', path='', detail=False)
class ASPathEntryListView(ObjectListView):
    queryset = ASPathEntry.objects.select_related('aspath')
    table = ASPathEntryTable
    filterset = ASPathEntryFilterSet
    filterset_form = ASPathEntryFilterForm


@register_model_view(ASPathEntry)
class ASPathEntryView(ObjectView):
    queryset = ASPathEntry.objects.select_related('aspath')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            ASPathEntryPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(ASPathEntry, name='add', detail=False)
@register_model_view(ASPathEntry, name='edit')
class ASPathEntryEditView(ObjectEditView):
    queryset = ASPathEntry.objects.select_related('aspath')
    form = ASPathEntryForm


@register_model_view(ASPathEntry, name='delete')
class ASPathEntryDeleteView(ObjectDeleteView):
    queryset = ASPathEntry.objects.select_related('aspath')


@register_model_view(ASPathEntry, name='bulk_edit', detail=False)
class ASPathEntryBulkEditView(BulkEditView):
    queryset = ASPathEntry.objects.select_related('aspath')
    filterset = ASPathEntryFilterSet
    table = ASPathEntryTable
    form = ASPathEntryBulkEditForm


@register_model_view(ASPathEntry, name='bulk_delete', detail=False)
class ASPathEntryBulkDeleteView(BulkDeleteView):
    queryset = ASPathEntry.objects.select_related('aspath')
    filterset = ASPathEntryFilterSet
    table = ASPathEntryTable
