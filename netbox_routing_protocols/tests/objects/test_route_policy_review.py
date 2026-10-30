import re
import uuid

from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from extras.models import Tag
from ipam.models import IPAddress, VRF
from users.models import User
from utilities.testing import APITestCase

from netbox_routing_protocols.filtersets import (
    RoutePolicyEntryFilterSet,
    RoutePolicyFilterSet,
)
from netbox_routing_protocols.forms.bulk_import import (
    RoutePolicyEntryImportForm,
    RoutePolicyImportForm,
)
from netbox_routing_protocols.forms.objects import RoutePolicyEntryForm
from netbox_routing_protocols.helpers import route_policy as helpers
from netbox_routing_protocols.models import (
    ASPath,
    CommunityList,
    PrefixList,
    RoutePolicy,
    RoutePolicyEntry,
)


def make_entry(policy, sequence, action='permit', **fields):
    return RoutePolicyEntry.objects.create(
        route_policy=policy, sequence=sequence, action=action, **fields
    )


class SuperuserMixin:
    def login(self):
        user = User.objects.filter(username='su').first() or (
            User.objects.create_superuser('su', 'su@example.com', 'x')
        )
        self.client.force_login(user)


class NextSequenceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')

    def test_next_sequence(self):
        self.assertEqual(helpers.next_sequence(self.policy), 10)
        make_entry(self.policy, 10)
        self.assertEqual(helpers.next_sequence(self.policy), 20)
        make_entry(self.policy, 25)
        self.assertEqual(helpers.next_sequence(self.policy), 30)
        self.assertEqual(helpers.next_sequence(self.policy, after=40), 50)

    def test_the_maximum_is_respected(self):
        make_entry(self.policy, 4294967290)
        with self.assertRaises(ValidationError):
            helpers.next_sequence(self.policy)


class RoutePolicyEntryFormTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')

    def request(self):
        request = RequestFactory().get('/')
        request.user = User.objects.create_superuser('f', 'f@example.com', 'x')
        request.id = uuid.uuid4()
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_a_new_entry_permits_and_the_sequence_is_suggested(self):
        make_entry(self.policy, 10)
        form = RoutePolicyEntryForm(initial={'route_policy': self.policy.pk})
        self.assertEqual(form.initial['action'], 'permit')
        self.assertEqual(form.initial['sequence'], 20)
        self.assertFalse(form.fields['sequence'].required)

    def test_an_empty_sequence_takes_the_next_one(self):
        make_entry(self.policy, 10)
        form = RoutePolicyEntryForm(
            data={'route_policy': self.policy.pk, 'action': 'permit', 'sequence': ''}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 20)

    def test_any_value_is_still_accepted_and_an_existing_entry_needs_it(self):
        form = RoutePolicyEntryForm(
            data={'route_policy': self.policy.pk, 'action': 'deny', 'sequence': 7}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 7)
        entry = RoutePolicyEntry.objects.get()
        form = RoutePolicyEntryForm(
            data={'route_policy': self.policy.pk, 'action': 'deny', 'sequence': ''},
            instance=entry,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('sequence', form.errors)


class RoutePolicyAPIFieldsTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.policy = RoutePolicy.objects.create(name='Policy')
        self.tag = Tag.objects.create(name='Tag', slug='tag')
        self.add_permissions(
            'extras.view_tag',
            *(
                f'netbox_routing_protocols.{action}_{model}'
                for action in ('add', 'view', 'change')
                for model in ('routepolicy', 'routepolicyentry')
            ),
        )

    def url(self, name, *args):
        return reverse(f'plugins-api:netbox_routing_protocols-api:{name}', args=args)

    def test_tags_custom_fields_owner_and_timestamps(self):
        response = self.client.post(
            self.url('routepolicy-list'),
            {'name': 'New', 'tags': [{'name': 'Tag'}]},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        for field in ('tags', 'custom_fields', 'owner', 'created', 'last_updated'):
            self.assertIn(field, response.data)
        self.assertEqual([t['name'] for t in response.data['tags']], ['Tag'])
        response = self.client.post(
            self.url('routepolicyentry-list'),
            {
                'route_policy': self.policy.pk,
                'sequence': 5,
                'action': 'permit',
                'tags': [{'name': 'Tag'}],
            },
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        for field in ('tags', 'custom_fields', 'owner', 'created', 'last_updated'):
            self.assertIn(field, response.data)
        self.assertEqual([t['name'] for t in response.data['tags']], ['Tag'])

    def test_a_missing_sequence_is_assigned(self):
        make_entry(self.policy, 10)
        response = self.client.post(
            self.url('routepolicyentry-list'),
            {'route_policy': self.policy.pk, 'action': 'permit'},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['sequence'], 20)

    def test_a_bulk_request_gets_consecutive_sequences(self):
        data = [{'route_policy': self.policy.pk, 'action': 'permit'} for _ in range(3)]
        response = self.client.post(
            self.url('routepolicyentry-list'), data, format='json', **self.header
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual([e['sequence'] for e in response.data], [10, 20, 30])


class RoutePolicyImportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.prefix_list = PrefixList.objects.create(name='Prefixes', family=4)
        cls.aspath = ASPath.objects.create(name='Path')
        cls.communities = CommunityList.objects.create(name='Communities')
        cls.v4 = IPAddress.objects.create(address='192.0.2.1/24')
        cls.v6 = IPAddress.objects.create(address='2001:db8::1/64')

    def entry(self, **kwargs):
        data = {'route_policy': 'Policy', 'action': 'permit'}
        data.update(kwargs)
        return RoutePolicyEntryImportForm(data=data)

    def test_the_policy(self):
        form = RoutePolicyImportForm(data={'name': 'New', 'description': 'Text'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().description, 'Text')

    def test_the_entry_takes_the_next_sequence_and_the_lists_by_name(self):
        make_entry(self.policy, 10)
        form = self.entry(
            match_prefix_list='Prefixes',
            match_aspath='Path',
            match_community_list='Communities',
            match_origin='igp',
            match_metric='5',
        )
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual(entry.sequence, 20)
        self.assertEqual(list(entry.match_prefix_list.all()), [self.prefix_list])
        self.assertEqual(list(entry.match_aspath.all()), [self.aspath])
        self.assertEqual(list(entry.match_community_list.all()), [self.communities])
        self.assertEqual((entry.match_origin, entry.match_metric), ('igp', 5))

    def test_the_settings_and_the_addresses(self):
        form = self.entry(
            sequence='5',
            match_next_hop='192.0.2.1',
            set_next_hop='2001:db8::1',
            set_aspath_prepend='65001 65001',
            set_community_list='Communities',
            set_community_mode='additive',
            set_metric='10',
            set_metric_mode='subtract',
            set_origin='egp',
            set_local_preference='200',
        )
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual(entry.match_next_hop, self.v4)
        self.assertEqual(entry.set_next_hop, self.v6)
        self.assertEqual(entry.set_aspath_prepend, [65001, 65001])
        self.assertEqual(entry.set_community_mode, 'additive')
        self.assertEqual(entry.set_metric_mode, 'subtract')
        self.assertEqual(entry.set_local_preference, 200)

    def test_an_unknown_address_or_a_bad_prepend_is_an_error(self):
        form = self.entry(match_next_hop='198.51.100.1')
        self.assertFalse(form.is_valid())
        self.assertIn('match_next_hop', form.errors)
        form = self.entry(set_aspath_prepend='65001 x')
        self.assertFalse(form.is_valid())
        self.assertIn('set_aspath_prepend', form.errors)

    def test_the_same_address_in_two_vrfs_needs_the_vrf(self):
        vrf = VRF.objects.create(name='VRF')
        other = IPAddress.objects.create(address='192.0.2.1/24', vrf=vrf)
        form = self.entry(match_next_hop='192.0.2.1')
        self.assertFalse(form.is_valid())
        self.assertIn('match_next_hop', form.errors)
        form = self.entry(match_next_hop='192.0.2.1', vrf='VRF')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().match_next_hop, other)

    def test_a_deny_entry_cannot_set(self):
        form = self.entry(action='deny', set_metric='1')
        self.assertFalse(form.is_valid())
        self.assertIn('set_metric', form.errors)

    def test_the_import_views(self):
        user = User.objects.create_superuser('imp', 'i@example.com', 'x')
        self.client.force_login(user)
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:routepolicy_bulk_import'),
            {'data': 'name\nOne\nTwo', 'format': 'csv', 'csv_delimiter': ','},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoutePolicy.objects.filter(name__in=('One', 'Two')).count(), 2)
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_bulk_import'),
            {
                'data': 'route_policy,action,match_origin,set_tag\nOne,permit,igp,5\nOne,deny,egp,',
                'format': 'csv',
                'csv_delimiter': ',',
            },
        )
        self.assertEqual(response.status_code, 302, response.content[:300])
        self.assertEqual(
            list(
                RoutePolicyEntry.objects.filter(route_policy__name='One')
                .order_by('sequence')
                .values_list('sequence', 'action', 'set_tag')
            ),
            [(10, 'permit', 5), (20, 'deny', None)],
        )


class RoutePolicyPagesTestCase(SuperuserMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.tag = Tag.objects.create(name='Tag', slug='tag')
        cls.prefix_list = PrefixList.objects.create(name='Prefixes', family=4)
        cls.communities = CommunityList.objects.create(name='Communities')
        cls.v4 = IPAddress.objects.create(address='192.0.2.1/24')
        cls.entry = make_entry(
            cls.policy,
            10,
            description='First',
            set_next_hop=cls.v4,
            set_aspath_prepend=[65001, 65001],
            set_community_list=cls.communities,
            set_community_mode='additive',
            set_metric=5,
            set_metric_mode='add',
            set_tag=9,
        )
        cls.entry.match_prefix_list.add(cls.prefix_list)
        cls.entry.tags.add(cls.tag)
        make_entry(cls.policy, 20, 'deny', match_tag=3)

    def test_the_page_has_the_entries_panel_and_the_buttons(self):
        self.login()
        response = self.client.get(self.policy.get_absolute_url())
        self.assertContains(response, 'Add entry')
        self.assertContains(
            response,
            reverse('plugins:netbox_routing_protocols:routepolicyentry_add')
            + f'?route_policy={self.policy.pk}',
        )
        self.assertContains(response, 'duplicate')
        # the panel loads its table by HTMX: the rows have the buttons of the table
        panel = re.search(
            r'hx-get="([^"]*route-policy-entry[^"]*)"', response.content.decode()
        )
        self.assertIsNotNone(panel, 'no entries panel')
        rows = self.client.get(
            panel.group(1).replace('&amp;', '&'), HTTP_HX_REQUEST='true'
        )
        self.assertContains(rows, self.entry.get_absolute_url())
        self.assertContains(rows, self.entry.get_absolute_url() + 'edit/')
        self.assertContains(rows, self.entry.get_absolute_url() + 'changelog/')

    def test_the_add_form_opens_with_the_policy_permit_and_the_sequence(self):
        self.login()
        response = self.client.get(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_add')
            + f'?route_policy={self.policy.pk}'
        )
        form = response.context['form']
        self.assertEqual(form.initial['action'], 'permit')
        self.assertEqual(form.initial['sequence'], 30)

    def test_the_list_tables_have_counts_and_row_buttons(self):
        self.login()
        response = self.client.get(
            reverse('plugins:netbox_routing_protocols:routepolicy_list')
        )
        row = next(r for r in response.context['table'].data if r.pk == self.policy.pk)
        self.assertEqual(row.entry_count, 2)
        self.assertContains(response, self.policy.get_absolute_url() + 'edit/')
        response = self.client.get(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_list')
        )
        self.assertContains(response, self.entry.get_absolute_url() + 'edit/')

    def test_duplicate(self):
        self.login()
        url = self.policy.get_absolute_url() + 'duplicate/'
        response = self.client.get(url)
        self.assertContains(response, 'Policy copy')
        response = self.client.post(url, {'name': 'Policy', 'description': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
        response = self.client.post(url, {'name': 'Copy', 'description': 'Copied'})
        self.assertEqual(response.status_code, 302)
        copy = RoutePolicy.objects.get(name='Copy')
        self.assertEqual(copy.description, 'Copied')
        self.assertEqual(
            list(copy.route_policy_entries.values_list('sequence', 'action')),
            [(10, 'permit'), (20, 'deny')],
        )
        first = copy.route_policy_entries.get(sequence=10)
        self.assertEqual(list(first.match_prefix_list.all()), [self.prefix_list])
        self.assertEqual(list(first.tags.all()), [self.tag])
        self.assertEqual(first.set_next_hop, self.v4)
        self.assertEqual(first.set_aspath_prepend, [65001, 65001])
        self.assertEqual(
            (first.set_community_list, first.set_community_mode, first.set_metric_mode),
            (self.communities, 'additive', 'add'),
        )
        self.assertEqual(first.description, 'First')
        # the source did not change
        self.assertEqual(self.policy.route_policy_entries.count(), 2)

    def test_the_duplicate_needs_the_permission_to_add_entries(self):
        user = User.objects.create_user('limited', 'l@example.com', 'x')
        from users.models import ObjectPermission
        from django.contrib.contenttypes.models import ContentType

        permission = ObjectPermission.objects.create(
            name='policies', actions=['add', 'view']
        )
        permission.object_types.add(ContentType.objects.get_for_model(RoutePolicy))
        permission.users.add(user)
        self.client.force_login(user)
        self.client.post(
            self.policy.get_absolute_url() + 'duplicate/', {'name': 'Copy'}
        )
        self.assertFalse(RoutePolicy.objects.filter(name='Copy').exists())


class RoutePolicyFiltersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first = RoutePolicy.objects.create(name='First', description='Edge')
        cls.second = RoutePolicy.objects.create(name='Second')
        cls.prefix_list = PrefixList.objects.create(name='Prefixes', family=4)
        cls.aspath = ASPath.objects.create(name='Path')
        cls.communities = CommunityList.objects.create(name='Communities')
        cls.v4 = IPAddress.objects.create(address='192.0.2.1/24')
        cls.permit = make_entry(
            cls.first, 10, match_metric=5, match_origin='igp', set_next_hop=cls.v4
        )
        cls.permit.match_prefix_list.add(cls.prefix_list)
        cls.permit.match_community_list.add(cls.communities)
        cls.deny = make_entry(cls.second, 10, 'deny', match_tag=7)
        cls.deny.match_aspath.add(cls.aspath)

    def policies(self, **params):
        return set(RoutePolicyFilterSet(params, RoutePolicy.objects.all()).qs)

    def entries(self, **params):
        return set(RoutePolicyEntryFilterSet(params, RoutePolicyEntry.objects.all()).qs)

    def test_the_policies(self):
        self.assertEqual(self.policies(q='edge'), {self.first})
        self.assertEqual(self.policies(name=['Second']), {self.second})
        self.assertEqual(self.policies(description=['Edge']), {self.first})
        self.assertEqual(
            self.policies(match_prefix_list_id=[self.prefix_list.pk]), {self.first}
        )
        self.assertEqual(
            self.policies(match_community_list_id=[self.communities.pk]), {self.first}
        )
        self.assertEqual(self.policies(match_aspath_id=[self.aspath.pk]), {self.second})

    def test_the_entries(self):
        self.assertEqual(self.entries(action=['deny']), {self.deny})
        self.assertEqual(self.entries(match_metric=[5]), {self.permit})
        self.assertEqual(self.entries(match_origin=['igp']), {self.permit})
        self.assertEqual(self.entries(match_tag=[7]), {self.deny})
        self.assertEqual(self.entries(set_next_hop_id=[self.v4.pk]), {self.permit})
        self.assertEqual(
            self.entries(match_prefix_list_id=[self.prefix_list.pk]), {self.permit}
        )
        self.assertEqual(self.entries(q='Second'), {self.deny})
        self.assertEqual(self.entries(route_policy_id=[self.first.pk]), {self.permit})
