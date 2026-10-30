import netaddr
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
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
from netbox_routing_protocols.choices import OriginChoices
from netbox_routing_protocols.helpers import community as community_helpers
from netbox_routing_protocols.helpers import route_policy as route_policy_helpers
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
from netbox_routing_protocols.models import (
    BGPPeerAddressFamily,
    CommunityList,
)
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


class ResequenceASPath(ObjectAction):
    """Renumber the entries of the AS-path"""

    name = 'resequence'
    label = _('Resequence')
    permissions_required = {'change'}
    url_kwargs = ['pk']
    template_name = 'netbox_routing_protocols/buttons/resequence.html'


class DuplicateRoutePolicy(DuplicatePrefixList):
    """A copy of the route policy with its entries"""


class ResequenceRoutePolicy(ResequenceASPath):
    """Renumber the entries of the route policy"""


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
        # the BGP peer address families that filter with it
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
                'model': meta.model_name,
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
# AS-path match: which entries of the AS-paths match an AS_PATH
#
class ASPathMatchView(ContentTypePermissionRequiredMixin, View):
    template_name = 'netbox_routing_protocols/aspath_match.html'
    partial_name = 'netbox_routing_protocols/aspath_match_results.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.view_aspathentry'

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
            path = aspath_helpers.parse_as_path(query)
        except ValidationError as e:
            return {'error': e.messages[0]}

        aspaths = ASPath.objects.restrict(request.user, 'view')
        entries = (
            ASPathEntry.objects.restrict(request.user, 'view')
            .filter(aspath__in=aspaths)
            .select_related('aspath')
        )
        matched, timed_out, not_evaluated = aspath_helpers.evaluate_path(path, entries)
        results = [
            {
                'aspath': aspath,
                'rows': [
                    {
                        'entry': entry,
                        'effective': effective,
                        'text': aspath_helpers.describe_entry(entry),
                    }
                    for entry, effective in rows
                ],
            }
            for aspath, rows in matched
        ]
        context = {
            'path': path,
            'results': results,
            'timed_out': timed_out,
            'not_evaluated': not_evaluated,
        }
        if show_all:
            matched = [result['aspath'].pk for result in results]
            context['unmatched'] = aspaths.exclude(pk__in=matched)
        return context


#
# Route policy match: which entry of a route policy decides a route
#
class RoutePolicyMatchView(ContentTypePermissionRequiredMixin, View):
    template_name = 'netbox_routing_protocols/routepolicy_match.html'
    partial_name = 'netbox_routing_protocols/routepolicy_match_results.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.view_routepolicyentry'

    def get(self, request):
        data = request.GET
        fields = (
            'prefix',
            'as_path',
            'communities',
            'next_hop',
            'metric',
            'origin',
            'tag',
            'weight',
        )
        values = {name: data.get(name, '').strip() for name in fields}
        policies = RoutePolicy.objects.restrict(request.user, 'view')
        context = {
            'values': values,
            'policy_id': data.get('policy', ''),
            'policies': policies,
            'origins': OriginChoices,
        }
        if any(values.values()):
            context.update(
                self.evaluate(request, values, data.get('policy', ''), policies)
            )
        # HTMX asks for the results only, a normal request for the whole page
        template = self.partial_name if request.htmx else self.template_name
        return render(request, template, context)

    @staticmethod
    def parse(values):
        """The route typed by the user, or the first error"""
        route = route_policy_helpers.Route()
        try:
            if values['prefix']:
                route.prefix = netaddr.IPNetwork(values['prefix'])
            if values['as_path']:
                route.as_path = aspath_helpers.parse_as_path(values['as_path'])
            if values['communities']:
                route.communities = community_helpers.parse_communities(
                    values['communities']
                )
            if values['next_hop']:
                route.next_hop = netaddr.IPAddress(values['next_hop'])
            for name, high in (
                ('metric', 4294967295),
                ('tag', 4294967295),
                ('weight', 65535),
            ):
                if values[name]:
                    number = int(values[name])
                    if not 0 <= number <= high:
                        raise ValueError(name)
                    setattr(route, name, number)
        except (netaddr.AddrFormatError, ValueError, TypeError) as e:
            return None, _('"%(value)s" is not valid.') % {'value': e}
        except ValidationError as e:
            return None, e.messages[0]
        if values['origin']:
            if values['origin'] not in OriginChoices.values():
                return None, _('The origin must be igp, egp or incomplete.')
            route.origin = values['origin']
        return route, None

    def evaluate(self, request, values, policy_id, policies):
        route, error = self.parse(values)
        if error:
            return {'error': error}
        if policy_id.isdigit():
            policies = policies.filter(pk=policy_id)
        results = []
        for policy in policies.order_by('name'):
            outcome = route_policy_helpers.evaluate(policy, route)
            outcome['policy'] = policy
            results.append(outcome)
        return {'results': results}


#
# Route Policy
#
@register_model_view(RoutePolicy, name='list', path='', detail=False)
class RoutePolicyListView(ObjectListView):
    queryset = RoutePolicy.objects.annotate(
        entry_count=Count(
            'route_policy_entries', filter=Q(route_policy_entries__implicit=False)
        )
    )
    table = RoutePolicyTable
    filterset = RoutePolicyFilterSet
    filterset_form = RoutePolicyFilterForm


@register_model_view(RoutePolicy)
class RoutePolicyView(GetRelatedModelsMixin, ObjectView):
    queryset = RoutePolicy.objects.all()
    template_name = 'generic/object.html'
    actions = (
        DuplicateRoutePolicy,
        ResequenceRoutePolicy,
        CloneObject,
        EditObject,
        DeleteObject,
    )
    layout = layout.SimpleLayout(
        left_panels=[
            RoutePolicyPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
        bottom_panels=[
            UnreachablePanel(title=_('Entries never evaluated')),
            panels.ObjectsTablePanel(
                model='netbox_routing_protocols.RoutePolicyEntry',
                title=_('Entries'),
                filters={'route_policy_id': lambda ctx: ctx['object'].pk},
                exclude_columns=['id', 'route_policy'],
                actions=[
                    AddObject(
                        'netbox_routing_protocols.RoutePolicyEntry',
                        label=_('Add entry'),
                        url_params={'route_policy': lambda ctx: ctx['object'].pk},
                    ),
                ],
            ),
        ],
    )

    def get_extra_context(self, request, instance):
        # An entry without conditions decides every route that reaches it: the ones below it
        # are never evaluated. Allowed, but the user is told
        unreachable = instance.unreachable_entries()
        return {
            'unreachable': [entry for entry, _stopper in unreachable],
            'stopper': unreachable[0][1] if unreachable else None,
            # Where the policy is used: the BGP objects, the import and export of the
            # protocol instances and the entries of other policies that jump to it
            'related_models': self.get_related_models(request, instance),
        }


@register_model_view(RoutePolicy, name='entries')
class RoutePolicyEntriesView(ObjectChildrenView):
    queryset = RoutePolicy.objects.all()
    child_model = RoutePolicyEntry
    table = RoutePolicyEntryTable
    filterset = RoutePolicyEntryFilterSet
    tab = ViewTab(
        label='Entries',
        badge=lambda obj: route_policy_helpers.user_entries(obj).count(),
    )

    def get_children(self, request, parent):
        return (
            self.child_model.objects.filter(route_policy=parent)
            .select_related(
                'route_policy',
                'jump_policy',
                'match_next_hop',
                'set_next_hop',
                'set_community_list',
            )
            .prefetch_related(
                'match_prefix_list', 'match_aspath', 'match_community_list'
            )
        )

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


@register_model_view(RoutePolicy, name='duplicate')
class RoutePolicyDuplicateView(ContentTypePermissionRequiredMixin, View):
    """Copy a route policy with its entries, in one transaction"""

    template_name = 'netbox_routing_protocols/routepolicy_duplicate.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.add_routepolicy'

    def _source(self, request, pk):
        return get_object_or_404(
            RoutePolicy.objects.restrict(request.user, 'view'), pk=pk
        )

    def _render(self, request, source, form):
        return render(
            request,
            self.template_name,
            {
                'object': source,
                'form': form,
                'count': route_policy_helpers.user_entries(source).count(),
            },
        )

    def get(self, request, pk):
        source = self._source(request, pk)
        form = RoutePolicyDuplicateForm(
            initial={
                'name': _('%(name)s copy') % {'name': source.name},
                'description': source.description,
            }
        )
        return self._render(request, source, form)

    def post(self, request, pk):
        source = self._source(request, pk)
        form = RoutePolicyDuplicateForm(request.POST)
        if not request.user.has_perm('netbox_routing_protocols.add_routepolicyentry'):
            messages.error(request, _('You cannot add route policy entries.'))
            return redirect(source.get_absolute_url())
        if not form.is_valid():
            return self._render(request, source, form)

        # Everything an entry has but its identity; the lists are copied apart
        skip = {
            'id',
            'route_policy',
            'implicit',
            'created',
            'last_updated',
            'custom_field_data',
        }
        copied = [
            field.name
            for field in RoutePolicyEntry._meta.concrete_fields
            if field.name not in skip
        ]
        lists = ('match_prefix_list', 'match_aspath', 'match_community_list')
        with transaction.atomic():
            copy = RoutePolicy(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                comments=source.comments,
                owner=source.owner,
            )
            copy.full_clean()
            copy.save()
            copy.tags.set(source.tags.all())
            for entry in route_policy_helpers.user_entries(source):
                new_entry = RoutePolicyEntry(
                    route_policy=copy,
                    **{name: getattr(entry, name) for name in copied},
                )
                new_entry.full_clean()
                new_entry.save()
                new_entry.tags.set(entry.tags.all())
                for name in lists:
                    getattr(new_entry, name).set(getattr(entry, name).all())
        messages.success(
            request,
            _('Duplicated %(source)s as %(copy)s with %(count)d entries.')
            % {
                'source': source,
                'copy': copy,
                'count': route_policy_helpers.user_entries(source).count(),
            },
        )
        return redirect(copy.get_absolute_url())


@register_model_view(RoutePolicy, name='resequence')
class RoutePolicyResequenceView(ContentTypePermissionRequiredMixin, View):
    """Renumber the entries of a route policy keeping their order"""

    template_name = 'netbox_routing_protocols/routepolicy_resequence.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.change_routepolicyentry'

    def _source(self, request, pk):
        return get_object_or_404(
            RoutePolicy.objects.restrict(request.user, 'view'), pk=pk
        )

    def _render(self, request, route_policy, form):
        return render(
            request,
            self.template_name,
            {
                'object': route_policy,
                'form': form,
                'count': route_policy_helpers.user_entries(route_policy).count(),
            },
        )

    def get(self, request, pk):
        route_policy = self._source(request, pk)
        return self._render(request, route_policy, RoutePolicyResequenceForm())

    def post(self, request, pk):
        route_policy = self._source(request, pk)
        form = RoutePolicyResequenceForm(request.POST)
        if form.is_valid():
            try:
                changed = route_policy_helpers.resequence(
                    route_policy, form.cleaned_data['start'], form.cleaned_data['step']
                )
            except ValidationError as e:
                form.add_error(None, e)
            else:
                messages.success(
                    request,
                    _('Resequenced %(policy)s: %(count)d entries renumbered.')
                    % {'policy': route_policy, 'count': changed},
                )
                return redirect(route_policy.get_absolute_url())
        return self._render(request, route_policy, form)


@register_model_view(RoutePolicy, name='bulk_import', detail=False)
class RoutePolicyBulkImportView(BulkImportView):
    queryset = RoutePolicy.objects.all()
    model_form = RoutePolicyImportForm


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
    queryset = RoutePolicyEntry.objects.select_related(
        'route_policy',
        'jump_policy',
        'match_next_hop',
        'set_next_hop',
        'set_community_list',
    ).prefetch_related('match_prefix_list', 'match_aspath', 'match_community_list')
    table = RoutePolicyEntryTable
    filterset = RoutePolicyEntryFilterSet
    filterset_form = RoutePolicyEntryFilterForm


@register_model_view(RoutePolicyEntry)
class RoutePolicyEntryView(GetRelatedModelsMixin, ObjectView):
    queryset = RoutePolicyEntry.objects.select_related(
        'route_policy', 'match_next_hop', 'set_next_hop', 'set_community_list'
    ).prefetch_related(
        'match_prefix_list',
        'match_community_list',
        'match_aspath',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RoutePolicyEntryPanel(title=_('Route Policy Entry')),
            RoutePolicyEntryMatchPanel(title=_('Match Actions')),
            RoutePolicyEntrySetPanel(title=_('Set Actions')),
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


@register_model_view(RoutePolicyEntry, name='bulk_import', detail=False)
class RoutePolicyEntryBulkImportView(BulkImportView):
    queryset = RoutePolicyEntry.objects.select_related('route_policy')
    model_form = RoutePolicyEntryImportForm


@register_model_view(RoutePolicyEntry, name='bulk_edit', detail=False)
class RoutePolicyEntryBulkEditView(BulkEditView):
    # the final deny of a policy is not chosen nor changed in bulk
    queryset = RoutePolicyEntry.objects.select_related('route_policy').filter(
        implicit=False
    )
    filterset = RoutePolicyEntryFilterSet
    table = RoutePolicyEntryTable
    form = RoutePolicyEntryBulkEditForm


@register_model_view(RoutePolicyEntry, name='bulk_delete', detail=False)
class RoutePolicyEntryBulkDeleteView(BulkDeleteView):
    # the final deny of a policy is not chosen nor changed in bulk
    queryset = RoutePolicyEntry.objects.select_related('route_policy').filter(
        implicit=False
    )
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
        ResequenceASPath,
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
        # Where the AS-path is used: the route policy entries that match it, their route
        # policies and the BGP objects that apply those (a many to many relation is not
        # detected by NetBox)
        policies = RoutePolicy.objects.filter(
            route_policy_entries__match_aspath=instance
        )
        in_use = Q(import_policy__in=policies) | Q(export_policy__in=policies)
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
                    (
                        RoutePolicy.objects.restrict(request.user, 'view')
                        .filter(route_policy_entries__match_aspath=instance)
                        .distinct(),
                        'match_aspath_id',
                    ),
                    (
                        BGPPeerAddressFamily.objects.restrict(request.user, 'view')
                        .filter(in_use)
                        .distinct(),
                        'aspath_id',
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


@register_model_view(ASPath, name='resequence')
class ASPathResequenceView(ContentTypePermissionRequiredMixin, View):
    """Renumber the entries of an AS-path keeping their order"""

    template_name = 'netbox_routing_protocols/aspath_resequence.html'

    def get_required_permission(self):
        return 'netbox_routing_protocols.change_aspathentry'

    def _source(self, request, pk):
        return get_object_or_404(ASPath.objects.restrict(request.user, 'view'), pk=pk)

    def _render(self, request, aspath, form):
        return render(
            request,
            self.template_name,
            {
                'object': aspath,
                'form': form,
                'count': aspath.aspath_entries.count(),
            },
        )

    def get(self, request, pk):
        aspath = self._source(request, pk)
        return self._render(request, aspath, ASPathResequenceForm())

    def post(self, request, pk):
        aspath = self._source(request, pk)
        form = ASPathResequenceForm(request.POST)
        if form.is_valid():
            try:
                changed = aspath_helpers.resequence(
                    aspath, form.cleaned_data['start'], form.cleaned_data['step']
                )
            except ValidationError as e:
                form.add_error(None, e)
            else:
                messages.success(
                    request,
                    _('Resequenced %(aspath)s: %(count)d entries renumbered.')
                    % {'aspath': aspath, 'count': changed},
                )
                return redirect(aspath.get_absolute_url())
        return self._render(request, aspath, form)


@register_model_view(ASPath, name='bulk_import', detail=False)
class ASPathBulkImportView(BulkImportView):
    queryset = ASPath.objects.all()
    model_form = ASPathImportForm


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


@register_model_view(ASPathEntry, name='bulk_import', detail=False)
class ASPathEntryBulkImportView(BulkImportView):
    queryset = ASPathEntry.objects.select_related('aspath')
    model_form = ASPathEntryImportForm


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
