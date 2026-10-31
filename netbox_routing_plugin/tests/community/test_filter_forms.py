from django.http import QueryDict
from django.test import TestCase

from ipam.models import Role
from netbox_routing_plugin.filtersets.community import *
from netbox_routing_plugin.forms.filtersets.community import *
from netbox_routing_plugin.models.community import *

__all__ = ('CommunityFilterFormTestCase', 'CommunityListEntryFilterFormTestCase')


def _fields_of_fieldsets(form_class):
    names = []
    for fieldset in form_class.fieldsets:
        names.extend(item for item in fieldset.items if isinstance(item, str))
    return names


class FilterFormMatchesFilterSetMixin:
    form = None
    filterset = None

    def test_fieldset_fields_exist(self):
        form = self.form()
        for name in _fields_of_fieldsets(self.form):
            self.assertIn(name, form.fields)

    def test_fields_are_filters(self):
        # every field of the form (but the NetBox generic ones) is a filter
        generic = {'q', 'filter_id', 'tag'}
        for name in self.form().fields:
            if name not in generic:
                self.assertIn(name, self.filterset.base_filters)


class CommunityFilterFormTestCase(FilterFormMatchesFilterSetMixin, TestCase):
    form = CommunityFilterForm
    filterset = CommunityFilterSet

    def test_filter_by_role_and_community(self):
        role = Role.objects.create(name='Role', slug='role')
        Community.objects.create(community='65000:1', role=role)
        Community.objects.create(community='65000:2')
        data = QueryDict(f'role_id={role.pk}&community=65000:1')
        self.assertTrue(self.form(data).is_valid())
        qs = self.filterset(data, Community.objects.all()).qs
        self.assertEqual(list(qs.values_list('community', flat=True)), ['65000:1'])


class CommunityListEntryFilterFormTestCase(FilterFormMatchesFilterSetMixin, TestCase):
    form = CommunityListEntryFilterForm
    filterset = CommunityListEntryFilterSet

    def test_filter_by_community_list_community_and_action(self):
        lists = [CommunityList.objects.create(name=f'L{i}') for i in (1, 2)]
        comms = [Community.objects.create(community=f'65000:{i}') for i in (1, 2)]
        for lst in lists:
            for sequence, (comm, action) in enumerate(
                zip(comms, ('permit', 'deny')), start=1
            ):
                CommunityListEntry.objects.create(
                    community_list=lst, sequence=sequence, community=comm, action=action
                )
        data = QueryDict(
            f'community_list_id={lists[0].pk}&community_id={comms[1].pk}&action=deny'
        )
        self.assertTrue(self.form(data).is_valid())
        qs = self.filterset(data, CommunityListEntry.objects.all()).qs
        self.assertEqual(qs.count(), 1)
        entry = qs.get()
        self.assertEqual((entry.community_list, entry.community), (lists[0], comms[1]))

        qs = self.filterset({'action': 'permit'}, CommunityListEntry.objects.all()).qs
        self.assertEqual(qs.count(), 2)
