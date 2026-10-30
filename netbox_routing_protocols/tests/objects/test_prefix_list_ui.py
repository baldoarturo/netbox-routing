import re
import uuid

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from ipam.models import Prefix
from netbox.context import current_request
from users.models import User
from extras.models import Tag
from utilities.testing import APITestCase

from netbox_routing_protocols.forms.objects import PrefixListEntryForm
from django.core.exceptions import ValidationError

from netbox_routing_protocols.helpers.prefix_list import (
    aspath_references,
    prefix_list_references,
    resequence,
)
from netbox_routing_protocols.models import BGPPeerAddressFamily
from netbox_routing_protocols.tests.bgp.base import create_peer_address_family
from netbox_routing_protocols.models.objects import *

__all__ = (
    'PrefixListOverlapFormTestCase',
    'PrefixListOverlapAPITestCase',
    'PrefixListViewsTestCase',
    'PrefixListDeleteWarningTestCase',
    'PrefixListDuplicateTestCase',
    'PrefixListResequenceTestCase',
    'PrefixListResequenceAPITestCase',
    'PrefixMatchViewTestCase',
)


def make_entry(prefix_list, sequence, prefix=None, **kwargs):
    if prefix is not None:
        prefix = Prefix.objects.filter(prefix=prefix).first() or Prefix.objects.create(
            prefix=prefix
        )
    return PrefixListEntry.objects.create(
        prefix_list=prefix_list,
        sequence=sequence,
        action=kwargs.pop('action', 'permit'),
        prefix=prefix,
        any_prefix=prefix is None,
        **kwargs,
    )


class PrefixListOverlapFormTestCase(TestCase):

    @staticmethod
    def request():
        request = RequestFactory().get('/')
        request.user = User.objects.create_superuser('form', 'form@example.com', 'x')
        request.id = uuid.uuid4()
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_saving_an_overlapping_entry_warns_but_saves(self):
        prefix_list = PrefixList.objects.create(name='List', family=4)
        make_entry(prefix_list, 10, '10.0.0.0/8', le=32)
        request = self.request()
        token = current_request.set(request)
        try:
            form = PrefixListEntryForm(
                data={
                    'prefix_list': prefix_list.pk,
                    'sequence': 20,
                    'action': 'deny',
                    'prefix': Prefix.objects.create(prefix='10.1.0.0/16').pk,
                    'le': 24,
                }
            )
            self.assertTrue(form.is_valid(), form.errors)
            entry = form.save()
        finally:
            current_request.reset(token)
        self.assertTrue(PrefixListEntry.objects.filter(pk=entry.pk).exists())
        texts = [str(message) for message in request._messages]
        self.assertEqual(len(texts), 1)
        self.assertIn('never reached', texts[0])
        self.assertIn('10 permit 10.0.0.0/8 le 32', texts[0])

    def test_no_warning_without_overlap(self):
        prefix_list = PrefixList.objects.create(name='List', family=4)
        make_entry(prefix_list, 10, '10.0.0.0/8')
        request = self.request()
        token = current_request.set(request)
        try:
            form = PrefixListEntryForm(
                data={
                    'prefix_list': prefix_list.pk,
                    'sequence': 20,
                    'action': 'permit',
                    'prefix': Prefix.objects.create(prefix='192.0.2.0/24').pk,
                }
            )
            self.assertTrue(form.is_valid(), form.errors)
            form.save()
        finally:
            current_request.reset(token)
        self.assertEqual(list(request._messages), [])


class PrefixListOverlapAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList.objects.create(name='List', family=4)
        cls.broad = make_entry(cls.prefix_list, 10, '10.0.0.0/8', le=32)

    def _url(self, name, obj=None):
        suffix = 'detail' if obj else 'list'
        kwargs = {'pk': obj.pk} if obj else {}
        return reverse(
            f'plugins-api:netbox_routing_protocols-api:{name}-{suffix}', kwargs=kwargs
        )

    def test_warnings_in_the_response_of_a_write(self):
        self.add_permissions(
            'netbox_routing_protocols.add_prefixlistentry',
            'netbox_routing_protocols.view_prefixlistentry',
        )
        prefix = Prefix.objects.create(prefix='10.1.0.0/16')
        response = self.client.post(
            self._url('prefixlistentry'),
            {
                'prefix_list': self.prefix_list.pk,
                'sequence': 20,
                'action': 'deny',
                'prefix': prefix.pk,
            },
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        warnings = response.data['warnings']
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]['kind'], 'shadowed')
        self.assertEqual(warnings[0]['entry']['id'], self.broad.pk)
        self.assertEqual(warnings[0]['entry']['sequence'], 10)
        self.assertIn('never reached', warnings[0]['message'])

    def test_no_overlap_gives_an_empty_list(self):
        self.add_permissions('netbox_routing_protocols.add_prefixlistentry')
        prefix = Prefix.objects.create(prefix='192.0.2.0/24')
        response = self.client.post(
            self._url('prefixlistentry'),
            {
                'prefix_list': self.prefix_list.pk,
                'sequence': 20,
                'action': 'deny',
                'prefix': prefix.pk,
            },
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['warnings'], [])

    def test_update_and_detail_and_list(self):
        self.add_permissions(
            'netbox_routing_protocols.view_prefixlistentry',
            'netbox_routing_protocols.change_prefixlistentry',
        )
        narrow = make_entry(self.prefix_list, 20, '10.1.0.0/16', action='deny')
        # a single entry reports them, also on a plain GET
        response = self.client.get(self._url('prefixlistentry', narrow), **self.header)
        self.assertHttpStatus(response, 200)
        self.assertEqual([w['kind'] for w in response.data['warnings']], ['shadowed'])
        # an update returns them
        response = self.client.patch(
            self._url('prefixlistentry', narrow),
            {'le': 24},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 200)
        self.assertEqual([w['kind'] for w in response.data['warnings']], ['shadowed'])
        # a list does not compute them per row
        response = self.client.get(self._url('prefixlistentry'), **self.header)
        self.assertHttpStatus(response, 200)
        self.assertTrue(
            all(row['warnings'] is None for row in response.data['results'])
        )


class SuperuserMixin:
    def login(self, username='root'):
        user = User.objects.create_superuser(username, f'{username}@example.com', 'x')
        self.client.force_login(user)
        return user


class PrefixListViewsTestCase(SuperuserMixin, TestCase):

    def test_entry_page_lists_the_overlapping_entries(self):
        self.login()
        prefix_list = PrefixList.objects.create(name='List', family=4)
        make_entry(prefix_list, 10, '10.0.0.0/8', le=32)
        narrow = make_entry(prefix_list, 20, '10.1.0.0/16', action='deny')
        make_entry(prefix_list, 30, '192.0.2.0/24')
        response = self.client.get(narrow.get_absolute_url())
        self.assertContains(response, 'Overlapping entries')
        self.assertContains(response, 'shadowed')
        self.assertNotContains(response, '192.0.2.0/24')
        # an entry with no overlap does not show the panel
        alone = PrefixListEntry.objects.get(sequence=30)
        self.assertNotContains(
            self.client.get(alone.get_absolute_url()), 'Overlapping entries'
        )

    def test_prefix_list_page_shows_where_it_is_used(self):
        self.login()
        prefix_list = PrefixList.objects.create(name='List', family=4)
        make_entry(prefix_list, 10, '10.0.0.0/8')
        route_policy = RoutePolicy.objects.create(name='Map')
        entry = RoutePolicyEntry.objects.create(
            route_policy=route_policy, sequence=10, action='permit'
        )
        entry.match_prefix_list.add(prefix_list)
        create_peer_address_family(prefixlist_in=prefix_list)
        response = self.client.get(prefix_list.get_absolute_url())
        self.assertContains(response, f'prefixlist_in_id={prefix_list.pk}')
        pk = prefix_list.pk
        for link in (
            f'/plugins/routing/objects/route-policy-entry/?match_prefix_list_id={pk}',
            f'/plugins/routing/bgp/peer-address-family/?prefixlist_in_id={pk}',
            f'/plugins/routing/objects/prefix-list-entry/?prefix_list_id={pk}',
        ):
            self.assertContains(response, link)

    def test_prefix_list_page_has_the_entries_and_an_add_button(self):
        self.login()
        prefix_list = PrefixList.objects.create(name='List', family=4)
        response = self.client.get(prefix_list.get_absolute_url())
        self.assertContains(
            response,
            f'/plugins/routing/objects/prefix-list-entry/add/?prefix_list={prefix_list.pk}',
        )
        # the entries table is loaded for this list only
        self.assertContains(
            response,
            f'/plugins/routing/objects/prefix-list-entry/?embedded=True&prefix_list_id={prefix_list.pk}',
        )
        # the form it opens has the list and the next sequence
        add = self.client.get(
            f'/plugins/routing/objects/prefix-list-entry/add/?prefix_list={prefix_list.pk}'
        )
        self.assertContains(add, 'value="10"')

    def test_the_add_page_preselects_permit(self):
        self.login()
        prefix_list = PrefixList.objects.create(name='List', family=4)
        base = '/plugins/routing/objects/prefix-list-entry/add/'
        for query, selected in (
            ('', 'permit'),
            (f'?prefix_list={prefix_list.pk}', 'permit'),
            ('?action=deny', 'deny'),
        ):
            with self.subTest(query):
                html = self.client.get(base + query).content.decode()
                select = html[html.index('name="action"') :]
                options = re.findall(r'<option value="(\w*)"(\s+selected)?', select)[:3]
                self.assertEqual([v for v, chosen in options if chosen], [selected])


class PrefixMatchViewTestCase(SuperuserMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.first = PrefixList.objects.create(name='First', family=4)
        cls.second = PrefixList.objects.create(name='Second', family=4)
        cls.v6 = PrefixList.objects.create(name='V6', family=6)
        make_entry(cls.first, 10, '10.1.0.0/16', le=24, action='deny')
        make_entry(cls.first, 20, '10.0.0.0/8', le=32)
        make_entry(cls.second, 5, '172.16.0.0/12', le=32)
        cls.url = reverse('plugins:netbox_routing_protocols:prefix_match')

    def test_the_page_has_a_realtime_search_box(self):
        self.login()
        response = self.client.get(self.url)
        self.assertContains(response, 'Prefix Match')
        self.assertContains(response, 'hx-get')
        self.assertContains(response, 'delay:250ms')

    def test_it_tells_the_sequence_of_each_matching_entry(self):
        self.login()
        response = self.client.get(self.url, {'q': '10.1.2.0/24'})
        self.assertContains(response, 'First')
        self.assertContains(response, '10 deny 10.1.0.0/16 le 24')
        self.assertContains(response, '20 permit 10.0.0.0/8 le 32')
        self.assertContains(response, 'first match')
        self.assertContains(response, 'also matches, not reached')
        self.assertNotContains(response, 'Second')

    def test_an_address_is_a_host_prefix(self):
        self.login()
        response = self.client.get(self.url, {'q': '172.16.5.9'})
        self.assertContains(response, 'Second')
        self.assertContains(response, '5 permit 172.16.0.0/12 le 32')
        self.assertNotContains(response, '10 deny')

    def test_htmx_gets_only_the_results(self):
        self.login()
        response = self.client.get(
            self.url, {'q': '10.1.2.0/24'}, HTTP_HX_REQUEST='true'
        )
        self.assertContains(response, 'first match')
        self.assertNotContains(response, '<html')

    def test_lists_with_no_match_can_be_included(self):
        self.login()
        response = self.client.get(self.url, {'q': '10.1.2.0/24', 'all': '1'})
        self.assertContains(response, 'Second')
        self.assertContains(response, 'deny (implicit)')
        self.assertNotContains(response, 'V6')

    def test_nothing_matches(self):
        self.login()
        response = self.client.get(self.url, {'q': '203.0.113.0/24'})
        self.assertContains(response, 'No prefix list entry matches')

    def test_invalid_input(self):
        self.login()
        response = self.client.get(self.url, {'q': 'not a prefix'})
        self.assertContains(response, 'is not a valid prefix or address')

    def test_any_entries_match_everything_of_the_family(self):
        self.login()
        make_entry(self.v6, 10, None, le=128)
        response = self.client.get(self.url, {'q': '2001:db8::/32'})
        self.assertContains(response, 'V6')
        self.assertContains(response, '10 permit any le 128')
        self.assertNotContains(self.client.get(self.url, {'q': '203.0.113.0/24'}), 'V6')

    def test_it_needs_the_view_permission(self):
        user = User.objects.create_user('plain', 'plain@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(
            self.client.get(self.url, {'q': '10.0.0.0/8'}).status_code, 403
        )


class PrefixListTablesTestCase(SuperuserMixin, TestCase):
    def test_the_tables_have_the_row_buttons(self):
        self.login()
        prefix_list = PrefixList.objects.create(name='Buttons', family=4)
        for name in ('prefixlist_list', 'prefixlistentry_list'):
            table = self.client.get(
                reverse(f'plugins:netbox_routing_protocols:{name}')
            ).context['table']
            self.assertIn('actions', [column.name for column in table.columns])
        # the description of an entry shows in the entries table without configuring it
        make_entry(prefix_list, 10, '10.0.0.0/8', description='Private use')
        for url in (
            reverse('plugins:netbox_routing_protocols:prefixlistentry_list'),
            prefix_list.get_absolute_url() + 'entries/',
        ):
            self.assertContains(self.client.get(url), 'Private use')


class PrefixListDeleteWarningTestCase(SuperuserMixin, TestCase):
    """A list in use can be deleted: the user is told what refers to it first"""

    @classmethod
    def setUpTestData(cls):
        cls.used = PrefixList.objects.create(name='Used', family=4)
        cls.free = PrefixList.objects.create(name='Free', family=4)
        cls.template = create_peer_address_family(prefixlist_in=cls.used)
        route_policy = RoutePolicy.objects.create(name='Map')
        cls.route_policy_entry = RoutePolicyEntry.objects.create(
            route_policy=route_policy, sequence=10, action='permit'
        )
        cls.route_policy_entry.match_prefix_list.add(cls.used)

    def test_references_of_any_model_are_found(self):
        models = {model for model, objects in prefix_list_references(self.used)}
        self.assertEqual(models, {BGPPeerAddressFamily, RoutePolicyEntry})
        self.assertEqual(prefix_list_references(self.free), [])

    def test_the_delete_dialog_names_what_refers_to_the_list(self):
        self.login()
        url = self.used.get_absolute_url() + 'delete/'
        for headers in ({}, {'HTTP_HX_REQUEST': 'true'}):
            with self.subTest(headers):
                response = self.client.get(url, **headers)
                self.assertContains(response, 'This prefix list is in use')
                self.assertContains(response, self.template.get_absolute_url())
                self.assertContains(
                    response, self.route_policy_entry.get_absolute_url()
                )

    def test_a_free_list_has_no_warning(self):
        self.login()
        response = self.client.get(self.free.get_absolute_url() + 'delete/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'is in use')

    def test_deleting_a_list_in_use_clears_the_references(self):
        self.login()
        response = self.client.post(
            self.used.get_absolute_url() + 'delete/', {'confirm': True}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PrefixList.objects.filter(pk=self.used.pk).exists())
        self.template.refresh_from_db()
        self.assertIsNone(self.template.prefixlist_in)
        self.assertFalse(
            RoutePolicyEntry.objects.get(implicit=False).match_prefix_list.exists()
        )

    def test_the_bulk_delete_confirmation_warns(self):
        self.login()
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:prefixlist_bulk_delete'),
            {'pk': [self.used.pk, self.free.pk]},
            follow=True,
        )
        texts = [str(message) for message in response.context['messages']]
        self.assertTrue(any('are in use' in text and 'Group' in text for text in texts))


class ASPathDeleteWarningTestCase(SuperuserMixin, TestCase):
    """An AS-path in use can be deleted: the user is told what refers to it first"""

    @classmethod
    def setUpTestData(cls):
        cls.used = ASPath.objects.create(name='Used')
        cls.free = ASPath.objects.create(name='Free')
        ASPathEntry.objects.create(
            aspath=cls.used, sequence=10, action='permit', pattern='^1$'
        )
        route_policy = RoutePolicy.objects.create(name='Map')
        cls.entry = RoutePolicyEntry.objects.create(
            route_policy=route_policy, sequence=10, action='permit'
        )
        cls.entry.match_aspath.add(cls.used)

    def test_references_exclude_the_entries_of_the_path(self):
        models = {model for model, objects in aspath_references(self.used)}
        self.assertEqual(models, {RoutePolicyEntry})
        self.assertEqual(aspath_references(self.free), [])

    def test_the_delete_dialog_names_what_refers_to_the_path(self):
        self.login()
        url = self.used.get_absolute_url() + 'delete/'
        for headers in ({}, {'HTTP_HX_REQUEST': 'true'}):
            with self.subTest(headers):
                response = self.client.get(url, **headers)
                self.assertContains(response, 'This AS-path is in use')
                self.assertContains(response, self.entry.get_absolute_url())

    def test_a_free_path_has_no_warning(self):
        self.login()
        response = self.client.get(self.free.get_absolute_url() + 'delete/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'is in use')

    def test_deleting_a_path_in_use_clears_the_references(self):
        self.login()
        response = self.client.post(
            self.used.get_absolute_url() + 'delete/', {'confirm': True}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ASPath.objects.filter(pk=self.used.pk).exists())
        self.assertFalse(
            RoutePolicyEntry.objects.get(implicit=False).match_aspath.exists()
        )

    def test_the_bulk_delete_confirmation_warns(self):
        self.login()
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:aspath_bulk_delete'),
            {'pk': [self.used.pk, self.free.pk]},
            follow=True,
        )
        texts = [str(message) for message in response.context['messages']]
        self.assertTrue(any('are in use' in text and 'Map' in text for text in texts))


class PrefixListDuplicateTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = PrefixList.objects.create(
            name='Source', family=4, description='d', comments='c'
        )
        cls.source.tags.add(Tag.objects.create(name='t', slug='t'))
        make_entry(cls.source, 10, '10.0.0.0/8', ge=16, le=24, description='one')
        make_entry(cls.source, 20, action='deny', le=32)
        cls.url = cls.source.get_absolute_url() + 'duplicate/'

    def test_the_page_has_the_button_and_suggests_a_name(self):
        self.login()
        self.assertContains(self.client.get(self.source.get_absolute_url()), self.url)
        response = self.client.get(self.url)
        self.assertContains(response, 'Source copy')
        self.assertContains(response, '2 entries')

    def test_the_copy_has_the_same_entries(self):
        self.login()
        response = self.client.post(self.url, {'name': 'Copy', 'description': 'new'})
        copy = PrefixList.objects.get(name='Copy')
        self.assertRedirects(response, copy.get_absolute_url())
        self.assertEqual(
            (copy.family, copy.description, copy.comments), (4, 'new', 'c')
        )
        self.assertEqual(list(copy.tags.names()), ['t'])
        fields = (
            'sequence',
            'action',
            'prefix',
            'any_prefix',
            'ge',
            'le',
            'description',
        )
        self.assertEqual(
            list(copy.prefix_list_entries.order_by('sequence').values_list(*fields)),
            list(
                self.source.prefix_list_entries.order_by('sequence').values_list(
                    *fields
                )
            ),
        )
        # the source is untouched
        self.assertEqual(self.source.prefix_list_entries.count(), 2)

    def test_the_name_must_be_new(self):
        self.login()
        response = self.client.post(self.url, {'name': 'source'})
        self.assertContains(response, 'already exists')
        self.assertEqual(PrefixList.objects.count(), 1)

    def test_it_needs_the_permission_to_add_lists_and_entries(self):
        user = User.objects.create_user('plain', 'p@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(PrefixList.objects.count(), 1)


class PrefixListResequenceTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList.objects.create(name='Reseq', family=4)
        for sequence, prefix in (
            (3, '10.0.0.0/8'),
            (4, '172.16.0.0/12'),
            (200, '192.168.0.0/16'),
        ):
            make_entry(cls.prefix_list, sequence, prefix)
        cls.url = cls.prefix_list.get_absolute_url() + 'resequence/'

    def sequences(self):
        return list(
            self.prefix_list.prefix_list_entries.order_by('sequence').values_list(
                'sequence', 'prefix__prefix'
            )
        )

    def test_the_order_is_kept_and_the_numbers_change(self):
        before = [str(prefix) for sequence, prefix in self.sequences()]
        self.assertEqual(resequence(self.prefix_list), 3)
        after = self.sequences()
        self.assertEqual([sequence for sequence, prefix in after], [10, 20, 30])
        self.assertEqual([str(prefix) for sequence, prefix in after], before)

    def test_start_and_step(self):
        resequence(self.prefix_list, start=100, step=5)
        self.assertEqual([s for s, p in self.sequences()], [100, 105, 110])

    def test_entries_that_have_their_number_are_not_touched(self):
        resequence(self.prefix_list)
        self.assertEqual(resequence(self.prefix_list), 0)
        # moving up over the numbers other entries still have does not collide
        resequence(self.prefix_list, start=20, step=10)
        self.assertEqual([s for s, p in self.sequences()], [20, 30, 40])

    def test_the_limit_is_checked_before_changing_anything(self):
        with self.assertRaises(ValidationError):
            resequence(self.prefix_list, start=4294967290, step=10)
        with self.assertRaises(ValidationError):
            resequence(self.prefix_list, start=0)
        self.assertEqual([s for s, p in self.sequences()], [3, 4, 200])

    def test_the_page_has_the_button_and_the_form_works(self):
        self.login()
        self.assertContains(
            self.client.get(self.prefix_list.get_absolute_url()), self.url
        )
        self.assertContains(self.client.get(self.url), '3 entries')
        response = self.client.post(self.url, {'start': 10, 'step': 10})
        self.assertRedirects(response, self.prefix_list.get_absolute_url())
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


class PrefixListResequenceAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.prefix_list = PrefixList.objects.create(name='Reseq', family=4)
        make_entry(self.prefix_list, 3, '10.0.0.0/8')
        make_entry(self.prefix_list, 4, '172.16.0.0/12')
        self.url = reverse(
            'plugins-api:netbox_routing_protocols-api:prefixlist-resequence',
            kwargs={'pk': self.prefix_list.pk},
        )

    def sequences(self):
        return list(
            self.prefix_list.prefix_list_entries.order_by('sequence').values_list(
                'sequence', flat=True
            )
        )

    def test_resequence_with_defaults_and_values(self):
        self.add_permissions(
            'netbox_routing_protocols.change_prefixlist',
            'netbox_routing_protocols.view_prefixlist',
            'netbox_routing_protocols.change_prefixlistentry',
        )
        response = self.client.patch(self.url, {}, format='json', **self.header)
        self.assertHttpStatus(response, 200)
        self.assertEqual(response.data, {'changed': 2})
        self.assertEqual(self.sequences(), [10, 20])
        response = self.client.patch(
            self.url, {'start': 100, 'step': 50}, format='json', **self.header
        )
        self.assertEqual(self.sequences(), [100, 150])

    def test_invalid_values(self):
        self.add_permissions(
            'netbox_routing_protocols.change_prefixlist',
            'netbox_routing_protocols.view_prefixlist',
            'netbox_routing_protocols.change_prefixlistentry',
        )
        for data in ({'start': 'x'}, {'step': -1}, {'start': 4294967294, 'step': 10}):
            with self.subTest(data):
                response = self.client.patch(
                    self.url, data, format='json', **self.header
                )
                self.assertHttpStatus(response, 400)
        self.assertEqual(self.sequences(), [3, 4])

    def test_it_needs_the_permission_to_change_entries(self):
        self.add_permissions(
            'netbox_routing_protocols.change_prefixlist',
            'netbox_routing_protocols.view_prefixlist',
        )
        response = self.client.patch(self.url, {}, format='json', **self.header)
        self.assertHttpStatus(response, 403)
        self.assertEqual(self.sequences(), [3, 4])
