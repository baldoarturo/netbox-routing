from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from extras.models import Tag
from users.models import User

from netbox_routing_protocols.filtersets.bgp import BGPPeerAddressFamilyFilterSet
from netbox_routing_protocols.tests.bgp.base import create_peer_address_family
from netbox_routing_protocols.filtersets.objects import (
    ASPathEntryFilterSet,
    ASPathFilterSet,
    RoutePolicyFilterSet,
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


class ASPathUsedByTestCase(SuperuserMixin, TestCase):
    """The page of an AS-path shows who uses it, through the route policies"""

    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Used')
        cls.free = ASPath.objects.create(name='Free')
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.other_policy = RoutePolicy.objects.create(name='Other')
        entry = RoutePolicyEntry.objects.create(
            route_policy=cls.policy, sequence=10, action='permit'
        )
        entry.match_aspath.add(cls.aspath)
        cls.inbound = create_peer_address_family(import_policy=cls.policy)
        cls.outbound = create_peer_address_family(export_policy=cls.policy)
        cls.unrelated = create_peer_address_family(import_policy=cls.other_policy)
        # the policy also set on the instance, the peer group and a peer
        instance = cls.inbound.address_family.instance
        instance.import_policy = cls.policy
        instance.save()
        group = cls.inbound.peer_group
        group.export_policy = cls.policy
        group.save()
        from ipam.models import IPAddress
        from netaddr import IPNetwork

        from netbox_routing_protocols.models import BGPPeer

        cls.peer = BGPPeer.objects.create(
            instance=instance,
            peer=IPAddress.objects.create(address=IPNetwork('10.5.5.5/24')),
            remote_as=group.remote_as or instance.asn,
            import_policy=cls.policy,
        )

    @staticmethod
    def policy_list():
        return reverse(NS + 'bgppeeraddressfamily_list')

    def test_route_policy_filter(self):
        qs = RoutePolicyFilterSet(
            QueryDict(f'match_aspath_id={self.aspath.pk}'), RoutePolicy.objects.all()
        ).qs
        self.assertEqual(set(qs), {self.policy})

    def test_bgp_filter_by_aspath_in_or_out(self):
        queryset = type(self.inbound).objects.all()
        qs = BGPPeerAddressFamilyFilterSet(
            QueryDict(f'aspath_id={self.aspath.pk}'), queryset
        ).qs
        self.assertEqual(set(qs), {self.inbound, self.outbound})
        qs = BGPPeerAddressFamilyFilterSet(
            QueryDict(f'aspath_id={self.free.pk}'), queryset
        ).qs
        self.assertEqual(set(qs), set())

    def test_the_page_links_to_each_kind_of_user(self):
        self.login()
        page = self.client.get(self.aspath.get_absolute_url())
        self.assertContains(page, f'match_aspath_id={self.aspath.pk}')
        self.assertContains(page, f'{self.policy_list()}?aspath_id={self.aspath.pk}')
        for name in (
            'routepolicy_list',
            'routepolicyentry_list',
            'bgppeeraddressfamily_list',
            'bgpinstance_list',
            'bgppeergroup_list',
            'bgppeer_list',
        ):
            self.assertContains(page, reverse(NS + name))

    def test_an_unused_aspath_lists_nothing(self):
        self.login()
        page = self.client.get(self.free.get_absolute_url())
        self.assertNotContains(page, f'{self.policy_list()}?aspath_id={self.free.pk}')
        self.assertNotContains(page, f'match_aspath_id={self.free.pk}')


class ASPathResequenceTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Reseq')
        for sequence, pattern in ((3, '^1$'), (4, '^2$'), (200, '^3$')):
            make_entry(cls.aspath, sequence, pattern)
        cls.url = cls.aspath.get_absolute_url() + 'resequence/'

    def sequences(self):
        return list(
            self.aspath.aspath_entries.order_by('sequence').values_list(
                'sequence', 'pattern'
            )
        )

    def test_the_order_is_kept_and_the_numbers_change(self):
        from netbox_routing_protocols.helpers.aspath import resequence

        before = [pattern for sequence, pattern in self.sequences()]
        self.assertEqual(resequence(self.aspath), 3)
        after = self.sequences()
        self.assertEqual([sequence for sequence, pattern in after], [10, 20, 30])
        self.assertEqual([pattern for sequence, pattern in after], before)
        self.assertEqual(resequence(self.aspath), 0)
        resequence(self.aspath, start=100, step=5)
        self.assertEqual([s for s, p in self.sequences()], [100, 105, 110])

    def test_the_limit_is_checked_before_changing_anything(self):
        from django.core.exceptions import ValidationError
        from netbox_routing_protocols.helpers.aspath import resequence

        for kwargs in ({'start': 4294967290, 'step': 10}, {'start': 0}):
            with self.assertRaises(ValidationError):
                resequence(self.aspath, **kwargs)
        self.assertEqual([s for s, p in self.sequences()], [3, 4, 200])

    def test_the_page_has_the_button_and_the_form_works(self):
        self.login()
        self.assertContains(self.client.get(self.aspath.get_absolute_url()), self.url)
        self.assertContains(self.client.get(self.url), '3 entries')
        response = self.client.post(self.url, {'start': 10, 'step': 10})
        self.assertRedirects(response, self.aspath.get_absolute_url())
        self.assertEqual([s for s, p in self.sequences()], [10, 20, 30])

    def test_an_error_is_shown_in_the_form(self):
        self.login()
        response = self.client.post(self.url, {'start': 4294967290, 'step': 10})
        self.assertContains(response, 'over the maximum')
        self.assertEqual([s for s, p in self.sequences()], [3, 4, 200])

    def test_it_needs_the_permission_to_change_entries(self):
        self.client.force_login(User.objects.create_user('plain', 'p@example.com', 'x'))
        self.assertEqual(
            self.client.post(self.url, {'start': 10, 'step': 10}).status_code, 403
        )
        self.assertEqual([s for s, p in self.sequences()], [3, 4, 200])
