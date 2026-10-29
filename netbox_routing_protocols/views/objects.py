import netaddr
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

from extras.ui.panels import TagsPanel
from netbox.object_actions import CloneObject, DeleteObject, EditObject, ObjectAction
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
from netbox.ui import panels, layout
from netbox.ui.actions import AddObject
from utilities.query import count_related
from utilities.views import (
    ContentTypePermissionRequiredMixin,
    GetRelatedModelsMixin,
    ViewTab,
    register_model_view,
)
from netbox_routing_protocols.helpers import aspath as aspath_helpers
from netbox_routing_protocols.helpers.prefix_list import (
    describe_entry,
    evaluate_prefix,
    find_overlaps,
    import_overlaps,
    aspath_references,
    prefix_list_references,
    resequence,
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


class DuplicatePrefixList(ObjectAction):
    """A copy of the prefix list with its entries"""

    name = 'duplicate'
    label = _('Duplicate')
    permissions_required = {'add'}
    url_kwargs = ['pk']
    template_name = 'netbox_routing_protocols/buttons/duplicate.html'


class DuplicateASPath(DuplicatePrefixList):
    """A copy of the AS-path with its entries"""


class ResequencePrefixList(ObjectAction):
    """Renumber the entries of the list"""

    name = 'resequence'
    label = _('Resequence')
    permissions_required = {'change'}
    url_kwargs = ['pk']
    template_name = 'netbox_routing_protocols/buttons/resequence.html'


@register_model_view(PrefixList)
class PrefixListView(GetRelatedModelsMixin, ObjectView):
    queryset = PrefixList.objects.all()
    actions = (
        DuplicatePrefixList,
        ResequencePrefixList,
        CloneObject,
        EditObject,
        DeleteObject,
    )
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
                    AddObject(
                        'netbox_routing_protocols.PrefixListEntry',
                        label=_('Add entry'),
                        url_params={'prefix_list': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        # Where the list is used: its entries, the route policy entries that match it and
        # the BGP policy templates and peer address families that filter with it
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                # a many to many relation is not detected by NetBox
                extra=(
                    (
                        RoutePolicyEntry.objects.restrict(request.user, 'view').filter(
                            match_prefix_list=instance
                        ),
                        'match_prefix_list_id',
                    ),
                ),
            )
        }


@register_model_view(PrefixList, name='duplicate')
class PrefixListDuplicateView(ContentTypePermissionRequiredMixin, View):
    """Copy a prefix list with its entries, in one transaction"""

    template_name = 'netbox_routing_protocols/prefixlist_duplicate.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.add_prefixlist'

    def _source(self, request, pk):
        return get_object_or_404(
            PrefixList.objects.restrict(request.user, 'view'), pk=pk
        )

    def _render(self, request, source, form):
        return render(
            request,
            self.template_name,
            {
                'object': source,
                'form': form,
                'count': source.prefix_list_entries.count(),
            },
        )

    def get(self, request, pk):
        source = self._source(request, pk)
        form = PrefixListDuplicateForm(
            initial={
                'name': _('%(name)s copy') % {'name': source.name},
                'description': source.description,
            }
        )
        return self._render(request, source, form)

    def post(self, request, pk):
        source = self._source(request, pk)
        form = PrefixListDuplicateForm(request.POST)
        if not request.user.has_perm('netbox_routing_protocols.add_prefixlistentry'):
            messages.error(request, _('You cannot add prefix list entries.'))
            return redirect(source.get_absolute_url())
        if not form.is_valid():
            return self._render(request, source, form)

        with transaction.atomic():
            copy = PrefixList(
                name=form.cleaned_data['name'],
                family=source.family,
                description=form.cleaned_data['description'],
                comments=source.comments,
                owner=source.owner,
            )
            copy.full_clean()
            copy.save()
            copy.tags.set(source.tags.all())
            for entry in source.prefix_list_entries.all():
                new_entry = PrefixListEntry(
                    prefix_list=copy,
                    sequence=entry.sequence,
                    action=entry.action,
                    prefix=entry.prefix,
                    any_prefix=entry.any_prefix,
                    ge=entry.ge,
                    le=entry.le,
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
                'count': source.prefix_list_entries.count(),
            },
        )
        return redirect(copy.get_absolute_url())


@register_model_view(PrefixList, name='resequence')
class PrefixListResequenceView(ContentTypePermissionRequiredMixin, View):
    """Renumber the entries of a prefix list keeping their order"""

    template_name = 'netbox_routing_protocols/prefixlist_resequence.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.change_prefixlistentry'

    def _source(self, request, pk):
        return get_object_or_404(
            PrefixList.objects.restrict(request.user, 'view'), pk=pk
        )

    def _render(self, request, prefix_list, form):
        return render(
            request,
            self.template_name,
            {
                'object': prefix_list,
                'form': form,
                'count': prefix_list.prefix_list_entries.count(),
            },
        )

    def get(self, request, pk):
        prefix_list = self._source(request, pk)
        return self._render(request, prefix_list, PrefixListResequenceForm())

    def post(self, request, pk):
        prefix_list = self._source(request, pk)
        form = PrefixListResequenceForm(request.POST)
        if form.is_valid():
            try:
                changed = resequence(
                    prefix_list, form.cleaned_data['start'], form.cleaned_data['step']
                )
            except ValidationError as e:
                form.add_error(None, e)
            else:
                messages.success(
                    request,
                    _('Resequenced %(list)s: %(count)d entries renumbered.')
                    % {'list': prefix_list, 'count': changed},
                )
                return redirect(prefix_list.get_absolute_url())
        return self._render(request, prefix_list, form)


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


# How many objects of each type are named in the warning of a delete
REFERENCES_SHOWN = 10


def reference_groups(request, objs, references=prefix_list_references):
    """
    The objects that refer to the prefix lists or AS-paths, of any model, as a list of dicts (name,
    count, the objects the user can view up to REFERENCES_SHOWN, and how many more).
    """
    pks = {}
    for obj in objs:
        for model, objects in references(obj):
            pks.setdefault(model, set()).update(objects.values_list('pk', flat=True))
    groups = []
    for model, model_pks in pks.items():
        manager = model._default_manager
        if hasattr(manager, 'restrict'):
            manager = manager.restrict(request.user, 'view')
        shown = list(manager.filter(pk__in=model_pks)[:REFERENCES_SHOWN])
        meta = model._meta
        groups.append(
            {
                'name': (
                    meta.verbose_name
                    if len(model_pks) == 1
                    else meta.verbose_name_plural
                ),
                'count': len(model_pks),
                'objects': shown,
                'more': len(model_pks) - len(shown),
            }
        )
    return groups


def references_message(groups, kind='prefix lists'):
    """The references of reference_groups as one line of text, for a message"""
    parts = []
    for group in groups:
        names = ', '.join(str(obj) for obj in group['objects'])
        if group['more']:
            names += ' and {} more'.format(group['more'])
        parts.append('{} {} ({})'.format(group['count'], group['name'], names))
    return (
        f'The selected {kind} are in use. Deleting them leaves these references '
        'empty: ' + '; '.join(parts) + '.'
    )


@register_model_view(PrefixList, name='delete')
class PrefixListDeleteView(ObjectDeleteView):
    queryset = PrefixList.objects.all()

    def get(self, request, *args, **kwargs):
        # A list in use can be deleted: the confirmation says what stops referencing it
        response = super().get(request, *args, **kwargs)
        groups = reference_groups(request, [self.get_object(**kwargs)])
        marker = b'<div class="modal-body">'
        if groups and getattr(response, 'content', None) and marker in response.content:
            warning = render_to_string(
                'netbox_routing_protocols/panels/prefix_list_references.html',
                {'groups': groups, 'kind': _('prefix list')},
                request=request,
            )
            response.content = response.content.replace(
                marker, marker + warning.encode(), 1
            )
        return response


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

    def post(self, request, **kwargs):
        # The confirmation page of the selection says what stops referencing the lists
        if '_confirm' not in request.POST:
            if request.POST.get('_all'):
                lists = self.filterset(request.GET, PrefixList.objects.all()).qs
            else:
                pks = [int(pk) for pk in request.POST.getlist('pk')]
                lists = PrefixList.objects.filter(pk__in=pks)
            groups = reference_groups(request, lists)
            if groups:
                messages.warning(request, references_message(groups))
        return super().post(request, **kwargs)


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


# How many lists and examples of each list the summary of an import names
IMPORT_LISTS_SHOWN = 5
IMPORT_EXAMPLES_SHOWN = 3


@register_model_view(PrefixListEntry, name='bulk_import', detail=False)
class PrefixListEntryBulkImportView(BulkImportView):
    queryset = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
    model_form = PrefixListEntryImportForm

    def create_and_update_objects(self, form, request):
        saved = super().create_and_update_objects(form, request)
        # The entries are saved anyway: overlaps are legitimate, the user is just told
        summaries = import_overlaps(saved)
        for prefix_list, kinds, examples in summaries[:IMPORT_LISTS_SHOWN]:
            counts = ', '.join(
                f'{count} {kind}' for kind, count in sorted(kinds.items())
            )
            shown = examples[:IMPORT_EXAMPLES_SHOWN]
            more = len(examples) - len(shown)
            text = f'Prefix list {prefix_list}: the import has overlapping entries ({counts}). '
            text += ' '.join(f'{example}.' for example in shown)
            if more:
                text += f' And {more} more.'
            messages.warning(request, text, fail_silently=True)
        if len(summaries) > IMPORT_LISTS_SHOWN:
            messages.warning(
                request,
                f'{len(summaries) - IMPORT_LISTS_SHOWN} more prefix lists have overlapping entries.',
                fail_silently=True,
            )
        return saved


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
# Route Policy
#
@register_model_view(RoutePolicy, name='list', path='', detail=False)
class RoutePolicyListView(ObjectListView):
    queryset = RoutePolicy.objects.all()
    table = RoutePolicyTable
    filterset = RoutePolicyFilterSet
    filterset_form = RoutePolicyFilterForm


@register_model_view(RoutePolicy)
class RoutePolicyView(ObjectView):
    queryset = RoutePolicy.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RoutePolicyPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(RoutePolicy, name='entries')
class RoutePolicyEntriesView(ObjectChildrenView):
    queryset = RoutePolicy.objects.all()
    child_model = RoutePolicyEntry
    table = RoutePolicyEntryTable
    filterset = RoutePolicyEntryFilterSet
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: RoutePolicyEntry.objects.filter(route_policy=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(route_policy=parent)

    def get_extra_context(self, request, instance):
        return {
            'url_parent': 'plugins:netbox_routing_protocols:routepolicy_entries',
            'url_add': 'plugins:netbox_routing_protocols:routepolicyentry_add',
            'url_bulk_edit': 'plugins:netbox_routing_protocols:routepolicyentry_bulk_edit',
            'url_bulk_delete': 'plugins:netbox_routing_protocols:routepolicyentry_bulk_delete',
            'parent_name': 'route_policy',
            'parent_view': 'routepolicy',
            'parent_view_path': 'entries',
            'view': 'routepolicyentry',
        }


@register_model_view(RoutePolicy, name='add', detail=False)
@register_model_view(RoutePolicy, name='edit')
class RoutePolicyEditView(ObjectEditView):
    queryset = RoutePolicy.objects.all()
    form = RoutePolicyForm


@register_model_view(RoutePolicy, name='delete')
class RoutePolicyDeleteView(ObjectDeleteView):
    queryset = RoutePolicy.objects.all()


@register_model_view(RoutePolicy, name='bulk_edit', detail=False)
class RoutePolicyBulkEditView(BulkEditView):
    queryset = RoutePolicy.objects.all()
    filterset = RoutePolicyFilterSet
    form = RoutePolicyBulkEditForm
    table = RoutePolicyTable


@register_model_view(RoutePolicy, name='bulk_delete', detail=False)
class RoutePolicyBulkDeleteView(BulkDeleteView):
    queryset = RoutePolicy.objects.all()
    filterset = RoutePolicyFilterSet
    table = RoutePolicyTable


#
# Route Policy Entry
#
@register_model_view(RoutePolicyEntry, name='list', path='', detail=False)
class RoutePolicyEntryListView(ObjectListView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    table = RoutePolicyEntryTable
    filterset = RoutePolicyEntryFilterSet
    filterset_form = RoutePolicyEntryFilterForm


@register_model_view(RoutePolicyEntry)
class RoutePolicyEntryView(GetRelatedModelsMixin, ObjectView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RoutePolicyEntryPanel(title=_('Route Policy Entry')),
            RoutePolicyEntryMatchPanel(title=_('Match Actions')),
            panels.JSONPanel('match', title=_('Match Parameters'), copy_button=True),
            RoutePolicyEntrySetPanel(title=_('Set Actions')),
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
                omit='route_policy',
                extra=(
                    (
                        PrefixList.objects.restrict(request.user, 'view').filter(
                            route_policy_entries=instance
                        ),
                        'route_policy_entry_id',
                    ),
                    (
                        CommunityList.objects.restrict(request.user, 'view').filter(
                            route_policy_entries=instance
                        ),
                        'route_policy_entry_id',
                    ),
                    (
                        Community.objects.restrict(request.user, 'view').filter(
                            route_policy_entries=instance
                        ),
                        'route_policy_entry_id',
                    ),
                    (
                        ASPath.objects.restrict(request.user, 'view').filter(
                            route_policy_entries=instance
                        ),
                        'route_policy_entry_id',
                    ),
                ),
            ),
        }


@register_model_view(RoutePolicyEntry, name='add', detail=False)
@register_model_view(RoutePolicyEntry, name='edit')
class RoutePolicyEntryEditView(ObjectEditView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    form = RoutePolicyEntryForm


@register_model_view(RoutePolicyEntry, name='delete')
class RoutePolicyEntryDeleteView(ObjectDeleteView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')


@register_model_view(RoutePolicyEntry, name='bulk_edit', detail=False)
class RoutePolicyEntryBulkEditView(BulkEditView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    filterset = RoutePolicyEntryFilterSet
    table = RoutePolicyEntryTable
    form = RoutePolicyEntryBulkEditForm


@register_model_view(RoutePolicyEntry, name='bulk_delete', detail=False)
class RoutePolicyEntryBulkDeleteView(BulkDeleteView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    filterset = RoutePolicyEntryFilterSet
    table = RoutePolicyEntryTable


#
# AS Path
#
@register_model_view(ASPath, name='list', path='', detail=False)
class ASPathListView(ObjectListView):
    queryset = ASPath.objects.annotate(entry_count=count_related(ASPathEntry, 'aspath'))
    filterset = ASPathFilterSet
    filterset_form = ASPathFilterForm
    table = ASPathTable


@register_model_view(ASPath)
class ASPathView(GetRelatedModelsMixin, ObjectView):
    queryset = ASPath.objects.all()
    actions = (
        DuplicateASPath,
        CloneObject,
        EditObject,
        DeleteObject,
    )
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
        bottom_panels=[
            panels.ObjectsTablePanel(
                model='netbox_routing_protocols.ASPathEntry',
                title=_('Entries'),
                filters={'aspath_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'aspath'],
                actions=[
                    AddObject(
                        'netbox_routing_protocols.ASPathEntry',
                        label=_('Add entry'),
                        url_params={'aspath': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        # Where the AS-path is used: the route policy entries that match it (a many to
        # many relation is not detected by NetBox)
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                extra=(
                    (
                        RoutePolicyEntry.objects.restrict(request.user, 'view').filter(
                            match_aspath=instance
                        ),
                        'match_aspath_id',
                    ),
                ),
            )
        }


@register_model_view(ASPath, name='duplicate')
class ASPathDuplicateView(ContentTypePermissionRequiredMixin, View):
    """Copy an AS-path with its entries, in one transaction"""

    template_name = 'netbox_routing_protocols/aspath_duplicate.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.add_aspath'

    def _source(self, request, pk):
        return get_object_or_404(ASPath.objects.restrict(request.user, 'view'), pk=pk)

    def _render(self, request, source, form):
        return render(
            request,
            self.template_name,
            {
                'object': source,
                'form': form,
                'count': source.aspath_entries.count(),
            },
        )

    def get(self, request, pk):
        source = self._source(request, pk)
        form = ASPathDuplicateForm(
            initial={
                'name': _('%(name)s copy') % {'name': source.name},
                'description': source.description,
            }
        )
        return self._render(request, source, form)

    def post(self, request, pk):
        source = self._source(request, pk)
        form = ASPathDuplicateForm(request.POST)
        if not request.user.has_perm('netbox_routing_protocols.add_aspathentry'):
            messages.error(request, _('You cannot add AS-path entries.'))
            return redirect(source.get_absolute_url())
        if not form.is_valid():
            return self._render(request, source, form)

        with transaction.atomic():
            copy = ASPath(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                comments=source.comments,
                owner=source.owner,
            )
            copy.full_clean()
            copy.save()
            copy.tags.set(source.tags.all())
            for entry in source.aspath_entries.all():
                new_entry = ASPathEntry(
                    aspath=copy,
                    sequence=entry.sequence,
                    action=entry.action,
                    pattern=entry.pattern,
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
                'count': source.aspath_entries.count(),
            },
        )
        return redirect(copy.get_absolute_url())


@register_model_view(ASPath, name='add', detail=False)
@register_model_view(ASPath, name='edit')
class ASPathEditView(ObjectEditView):
    queryset = ASPath.objects.all()
    form = ASPathForm


@register_model_view(ASPath, name='delete')
class ASPathDeleteView(ObjectDeleteView):
    queryset = ASPath.objects.all()

    def get(self, request, *args, **kwargs):
        # An AS-path in use can be deleted: the confirmation says what stops referencing it
        response = super().get(request, *args, **kwargs)
        groups = reference_groups(
            request, [self.get_object(**kwargs)], references=aspath_references
        )
        marker = b'<div class="modal-body">'
        if groups and getattr(response, 'content', None) and marker in response.content:
            warning = render_to_string(
                'netbox_routing_protocols/panels/prefix_list_references.html',
                {'groups': groups, 'kind': _('AS-path')},
                request=request,
            )
            response.content = response.content.replace(
                marker, marker + warning.encode(), 1
            )
        return response


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

    def post(self, request, **kwargs):
        # The confirmation page of the selection says what stops referencing the AS-paths
        if '_confirm' not in request.POST:
            if request.POST.get('_all'):
                aspaths = self.filterset(request.GET, ASPath.objects.all()).qs
            else:
                pks = [int(pk) for pk in request.POST.getlist('pk')]
                aspaths = ASPath.objects.filter(pk__in=pks)
            groups = reference_groups(request, aspaths, references=aspath_references)
            if groups:
                messages.warning(request, references_message(groups, kind='AS-paths'))
        return super().post(request, **kwargs)


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
        return self.child_model.objects.filter(aspath=parent).select_related('aspath')

    def get_extra_context(self, request, instance):
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
# Route Policy Entry
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
            OverlapsPanel(title=_('Entries with the same pattern')),
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )

    def get_extra_context(self, request, instance):
        return {'overlaps': aspath_helpers.find_duplicates(instance)}


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
