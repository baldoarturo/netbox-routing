from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from extras.models import Tag
from users.models import User

from netbox_routing_protocols.filtersets.objects import (
    ASPathEntryFilterSet,
    ASPathFilterSet,
)
from netbox_routing_protocols.forms.objects import (
    ASPathEntryBulkEditForm,
    ASPathEntryFilterForm,
    ASPathEntryForm,
)
from netbox_routing_protocols.models.objects import *

NS = 'plugins:netbox_routing_protocols:'


def make_entry(aspath, sequence, pattern, action='permit', **kwargs):
    return ASPathEntry.objects.create(
        aspath=aspath, sequence=sequence, action=action, pattern=pattern, **kwargs
    )


class SuperuserMixin:
    def login(self):
        User.objects.create_superuser('root', 'root@example.com', 'x')
        self.client.login(username='root', password='x')


class ASPathTablesTestCase(SuperuserMixin, TestCase):
    def test_tables_have_buttons_pattern_and_no_asn(self):
        self.login()
        aspath = ASPath.objects.create(name='Path', description='Customers')
        make_entry(aspath, 10, '^65001_', description='Customer one')
        for name in ('aspath_list', 'aspathentry_list'):
            table = self.client.get(reverse(NS + name)).context['table']
            names = [column.name for column in table.columns]
            self.assertIn('actions', names)
            self.assertNotIn('asn', names)
        response = self.client.get(reverse(NS + 'aspathentry_list'))
        self.assertContains(response, 'Customer one')
        self.assertContains(self.client.get(reverse(NS + 'aspath_list')), 'Customers')

    def test_the_list_counts_entries_without_a_query_per_row(self):
        self.login()
        for index in range(3):
            make_entry(ASPath.objects.create(name=f'P{index}'), 10, '^1$')
        url = reverse(NS + 'aspath_list')
        with self.assertNumQueries(self._count(url)):
            self.client.get(url)
        for index in range(3, 8):
            make_entry(ASPath.objects.create(name=f'P{index}'), 10, '^1$')
        with self.assertNumQueries(self._count(url)):
            self.client.get(url)

    def _count(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            self.client.get(url)
        # the first call of a test client logs in: measure once more
        with CaptureQueriesContext(connection) as queries:
            self.client.get(url)
        return len(queries)

    def test_the_entries_tab_has_no_query_per_row(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.login()
        aspath = ASPath.objects.create(name='Path')
        url = aspath.get_absolute_url() + 'entries/'
        for sequence in (10, 20):
            make_entry(aspath, sequence, f'^{sequence}$')
        self.client.get(url)
        with CaptureQueriesContext(connection) as few:
            self.client.get(url)
        for sequence in range(30, 90, 10):
            make_entry(aspath, sequence, f'^{sequence}$')
        with CaptureQueriesContext(connection) as many:
            self.client.get(url)
        self.assertEqual(len(few), len(many))


class ASPathPageTestCase(SuperuserMixin, TestCase):
    def test_the_page_has_the_entries_panel_and_buttons(self):
        self.login()
        aspath = ASPath.objects.create(name='Path')
        make_entry(aspath, 10, '^65001_')
        response = self.client.get(aspath.get_absolute_url())
        self.assertContains(
            response, f'{reverse(NS + "aspathentry_add")}?aspath={aspath.pk}'
        )
        self.assertContains(response, aspath.get_absolute_url() + 'duplicate/')

    def test_the_page_lists_the_route_policy_entries_that_use_it(self):
        self.login()
        aspath = ASPath.objects.create(name='Path')
        entry = RoutePolicyEntry.objects.create(
            route_policy=RoutePolicy.objects.create(name='Map'),
            sequence=10,
            action='permit',
        )
        entry.match_aspath.add(aspath)
        self.assertContains(
            self.client.get(aspath.get_absolute_url()), f'match_aspath_id={aspath.pk}'
        )


class ASPathEntryFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Path')

    def test_a_new_entry_permits_by_default(self):
        form = ASPathEntryForm(initial={'aspath': self.aspath.pk})
        self.assertEqual(form.initial['action'], 'permit')
        form = ASPathEntryForm(initial={'action': 'deny'})
        self.assertEqual(form.initial['action'], 'deny')

    def test_the_sequence_of_an_existing_entry_is_required(self):
        entry = make_entry(self.aspath, 10, '^1$')
        form = ASPathEntryForm(
            instance=entry,
            data={
                'aspath': self.aspath.pk,
                'action': 'permit',
                'pattern': '^1$',
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('sequence', form.errors)


class ASPathDuplicateTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = ASPath.objects.create(name='Source', description='d', comments='c')
        cls.source.tags.add(Tag.objects.create(name='t', slug='t'))
        make_entry(cls.source, 10, '^1$', description='one')
        make_entry(cls.source, 20, '^2$', action='deny')
        cls.url = cls.source.get_absolute_url() + 'duplicate/'

    def test_the_form_suggests_a_name(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, 'Source copy')
        self.assertContains(response, '2 entries')

    def test_it_copies_the_aspath_with_its_entries(self):
        self.login()
        response = self.client.post(self.url, {'name': 'Copy', 'description': 'new'})
        copy = ASPath.objects.get(name='Copy')
        self.assertRedirects(response, copy.get_absolute_url())
        self.assertEqual(copy.description, 'new')
        self.assertEqual(copy.comments, 'c')
        self.assertEqual(list(copy.tags.names()), ['t'])
        self.assertEqual(
            list(
                copy.aspath_entries.values_list(
                    'sequence', 'action', 'pattern', 'description'
                )
            ),
            [(10, 'permit', '^1$', 'one'), (20, 'deny', '^2$', '')],
        )
        self.assertEqual(self.source.aspath_entries.count(), 2)

    def test_a_taken_name_is_rejected_and_nothing_is_created(self):
        self.login()
        response = self.client.post(self.url, {'name': 'source'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ASPath.objects.count(), 1)

    def test_it_needs_the_add_permission(self):
        user = User.objects.create_user('plain', 'plain@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)


class ASPathFiltersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.one = ASPath.objects.create(name='One', description='customers')
        cls.two = ASPath.objects.create(name='Two')
        cls.e1 = make_entry(cls.one, 10, '^65001_', description='first')
        cls.e2 = make_entry(cls.one, 20, '^65002_', action='deny')
        cls.e3 = make_entry(cls.two, 10, '^65003_')

    def ids(self, filterset, params):
        data = QueryDict(mutable=True)
        for key, value in params.items():
            data.setlist(key, value if isinstance(value, list) else [value])
        return set(filterset(data, filterset.Meta.model.objects.all()).qs)

    def test_aspath_filters(self):
        self.assertEqual(self.ids(ASPathFilterSet, {'name': ['One']}), {self.one})
        self.assertEqual(
            self.ids(ASPathFilterSet, {'description': ['customers']}), {self.one}
        )
        self.assertEqual(self.ids(ASPathFilterSet, {'q': 'custom'}), {self.one})

    def test_entry_filters(self):
        f = ASPathEntryFilterSet
        self.assertEqual(self.ids(f, {'sequence': [20]}), {self.e2})
        self.assertEqual(self.ids(f, {'action': ['deny']}), {self.e2})
        self.assertEqual(self.ids(f, {'pattern': ['^65003_']}), {self.e3})
        self.assertEqual(self.ids(f, {'description': ['first']}), {self.e1})
        self.assertEqual(self.ids(f, {'q': 'first'}), {self.e1})
        self.assertEqual(self.ids(f, {'aspath_id': [self.two.pk]}), {self.e3})

    def test_filter_form_and_bulk_edit_fields(self):
        form = ASPathEntryFilterForm()
        for field in ('aspath_id', 'action', 'sequence', 'pattern', 'tag'):
            self.assertIn(field, form.fields)
        self.assertIn('action', ASPathEntryBulkEditForm(ASPathEntry).fields)
