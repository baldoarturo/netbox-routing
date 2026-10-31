import importlib

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse

from extras.choices import CustomFieldTypeChoices
from extras.models import CustomField, Tag
from netbox.search.backends import search_backend
from tenancy.models import Tenant
from users.models import Owner
from utilities.testing import APITestCase

from netbox_routing_plugin.filtersets.community import CommunityFilterSet
from netbox_routing_plugin.forms.bulk_import.community import *
from netbox_routing_plugin.forms.community import (
    CommunityListEntryBulkEditForm,
    CommunityListEntryForm,
)
from netbox_routing_plugin.models.community import *

__all__ = (
    'CommunityTypeChangeTestCase',
    'CommunityWellKnownNameTestCase',
    'CommunityTenantUniqueTestCase',
    'CommunityEntryImportTestCase',
    'CommunitySelectorTestCase',
    'CommunityGraphQLFiltersTestCase',
    'CommunityAPIExtraFieldsTestCase',
)

API = 'plugins-api:netbox_routing_plugin-api:'


def make_entry(community_list, sequence, community, action='permit'):
    return CommunityListEntry.objects.create(
        community_list=community_list,
        sequence=sequence,
        community=community,
        action=action,
    )


class CommunityTypeChangeTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.community = Community.objects.create(community='65000:1')
        self.lst = CommunityList.objects.create(name='Std')
        make_entry(self.lst, 10, self.community)

    def test_model_refuses_to_change_the_type_of_a_community_in_use(self):
        self.community.community = 'rt:65000:1'
        with self.assertRaises(ValidationError) as caught:
            self.community.full_clean()
        self.assertIn('Std', str(caught.exception))

    def test_a_community_not_in_use_can_change_type(self):
        free = Community.objects.create(community='65000:2')
        free.community = 'rt:65000:2'
        free.full_clean()
        free.save()
        self.assertEqual(free.type, 'extended')

    def test_the_same_type_is_fine(self):
        self.community.community = '65000:0100'
        self.community.full_clean()

    def test_api_returns_400(self):
        self.add_permissions('netbox_routing_plugin.change_community')
        response = self.client.patch(
            reverse(API + 'community-detail', kwargs={'pk': self.community.pk}),
            {'community': 'rt:65000:1'},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 400)
        self.community.refresh_from_db()
        self.assertEqual(self.community.type, 'standard')


class CommunityWellKnownNameTestCase(TestCase):
    def test_an_empty_name_takes_the_name_of_the_rfc(self):
        community = Community(community='no-export')
        community.full_clean()
        community.save()
        self.assertEqual(community.name, 'NO_EXPORT')

    def test_a_given_name_is_kept(self):
        community = Community(community='65535:666', name='drop')
        community.full_clean()
        community.save()
        self.assertEqual(community.name, 'drop')

    def test_other_communities_stay_without_name(self):
        community = Community(community='65000:1')
        community.full_clean()
        self.assertEqual(community.name, '')

    def test_standby_pe(self):
        community = Community(community='standby-pe')
        community.full_clean()
        self.assertEqual(
            (community.community, community.name, community.well_known),
            ('65535:9', 'STANDBY_PE', 'STANDBY_PE (RFC 9026)'),
        )

    def test_the_search_finds_it(self):
        community = Community(community='65535:65281')
        community.full_clean()
        community.save()
        search_backend.cache([community])
        self.assertEqual(len(list(search_backend.search('no_export'))), 1)

    def test_the_migration_names_the_existing_ones(self):
        migration = importlib.import_module(
            'netbox_routing_plugin.migrations.0084_community_unique_per_tenant'
        )
        Community.objects.bulk_create(
            [Community(community='65535:65282'), Community(community='65000:1')]
        )
        migration.name_well_known(apps, None)
        self.assertEqual(
            dict(Community.objects.values_list('community', 'name')),
            {'65535:65282': 'NO_ADVERTISE', '65000:1': ''},
        )


class CommunityTenantUniqueTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.a = Tenant.objects.create(name='A', slug='a')
        self.b = Tenant.objects.create(name='B', slug='b')

    def test_two_tenants_can_have_the_same_value(self):
        for tenant in (self.a, self.b, None):
            community = Community(community='65000:100', tenant=tenant)
            community.full_clean()
            community.save()
        self.assertEqual(Community.objects.filter(community='65000:100').count(), 3)

    def test_a_tenant_cannot_repeat_a_value(self):
        Community.objects.create(community='65000:100', tenant=self.a)
        with self.assertRaises(ValidationError):
            Community(community='65000:0100', tenant=self.a).full_clean()

    def test_no_tenant_cannot_repeat_a_value(self):
        Community.objects.create(community='65000:100')
        with self.assertRaises(ValidationError) as caught:
            Community(community='65000:100').full_clean()
        self.assertIn('no tenant', str(caught.exception))

    def test_api(self):
        self.add_permissions('netbox_routing_plugin.add_community')
        url = reverse(API + 'community-list')
        for tenant, status in ((self.a, 201), (self.b, 201), (self.a, 400)):
            response = self.client.post(
                url,
                {'community': '65000:100', 'tenant': tenant.pk},
                format='json',
                **self.header,
            )
            self.assertHttpStatus(response, status)


class CommunityEntryImportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Tenant.objects.create(name='A', slug='a')
        cls.lst = CommunityList.objects.create(name='L')
        cls.lst_a = CommunityList.objects.create(name='LA', tenant=cls.a)
        cls.global_one = Community.objects.create(community='65000:100')
        cls.of_a = Community.objects.create(community='65000:100', tenant=cls.a)
        cls.plain = Community.objects.create(community='65000:7')
        cls.well_known = Community.objects.create(community='65535:65281')

    def form(self, **data):
        base = {'community_list': 'L', 'community': '65000:7', 'action': 'permit'}
        return CommunityListEntryImportForm(data={**base, **data})

    def test_the_normal_form_works(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().community, self.plain)

    def test_other_spellings_are_rejected_with_the_form_to_use(self):
        for value, normal in (
            ('no-export', '65535:65281'),
            ('65000:0007', '65000:7'),
            ('RT:65000:1', 'rt:65000:1'),
            ('4259840007', '65000:7'),
        ):
            with self.subTest(value=value):
                form = self.form(community=value)
                self.assertFalse(form.is_valid())
                self.assertIn(normal, form.errors['community'][0])
                self.assertIn('normal form', form.errors['community'][0])

    def test_what_is_not_a_community_says_why(self):
        form = self.form(community='70000:1')
        self.assertFalse(form.is_valid())
        self.assertIn('16-bit', form.errors['community'][0])

    def test_an_unknown_community(self):
        form = self.form(community='65000:999')
        self.assertFalse(form.is_valid())
        self.assertIn('No community 65000:999', form.errors['community'][0])

    def test_several_tenants_use_the_tenant_of_the_list_then_no_tenant(self):
        form = self.form(community='65000:100')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().community, self.global_one)
        form = self.form(community_list='LA', community='65000:100')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().community, self.of_a)

    def test_community_tenant_chooses(self):
        form = self.form(community='65000:100', community_tenant='A')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().community, self.of_a)

    def test_ambiguous_without_a_preferred_one(self):
        Community.objects.filter(pk=self.global_one.pk).delete()
        other = Tenant.objects.create(name='B', slug='b')
        Community.objects.create(community='65000:100', tenant=other)
        form = self.form(community='65000:100')
        self.assertFalse(form.is_valid())
        self.assertIn('community_tenant', form.errors['community'][0])


class CommunitySelectorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.std = Community.objects.create(community='65000:1')
        cls.ext = Community.objects.create(community='rt:65000:1')
        cls.large = Community.objects.create(community='65000:1:2')
        cls.std_list = CommunityList.objects.create(name='Std')
        cls.ext_list = CommunityList.objects.create(name='Ext', type='extended')

    def usable(self, community_list):
        data = QueryDict(f'usable_in_list_id={community_list.pk}')
        return set(CommunityFilterSet(data, Community.objects.all()).qs)

    def test_the_filter_returns_the_communities_of_the_type_of_the_list(self):
        self.assertEqual(self.usable(self.std_list), {self.std})
        self.assertEqual(self.usable(self.ext_list), {self.ext})

    def test_without_a_list_nothing_is_filtered(self):
        qs = CommunityFilterSet({}, Community.objects.all()).qs
        self.assertEqual(qs.count(), 3)

    def test_the_forms_ask_for_the_communities_of_the_list(self):
        for form in (CommunityListEntryForm(), CommunityListEntryBulkEditForm()):
            widget = form.fields['community'].widget
            self.assertEqual(
                widget.attrs.get('data-url') is not None
                or form.fields['community'].query_params,
                form.fields['community'].query_params,
            )
            self.assertEqual(
                form.fields['community'].query_params,
                {'usable_in_list_id': '$community_list'},
            )


class CommunityGraphQLFiltersTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.std = Community.objects.create(community='65000:1', name='first')
        cls.ext = Community.objects.create(community='rt:65000:1', status='reserved')
        cls.std_list = CommunityList.objects.create(name='Std')
        cls.ext_list = CommunityList.objects.create(name='Ext', type='extended')
        cls.e1 = make_entry(cls.std_list, 10, cls.std)
        cls.e2 = make_entry(cls.std_list, 20, cls.std, 'deny')

    def query(self, text):
        response = self.client.post(
            reverse('graphql'), {'query': text}, format='json', **self.header
        )
        self.assertHttpStatus(response, 200)
        self.assertNotIn('errors', response.json(), response.json())
        return response.json()['data']

    def ids(self, field, filters):
        data = self.query(f'{{ {field}(filters: {{{filters}}}) {{ id }} }}')
        return {int(row['id']) for row in data[field]}

    def test_filters(self):
        self.add_permissions(
            'netbox_routing_plugin.view_community',
            'netbox_routing_plugin.view_communitylist',
            'netbox_routing_plugin.view_communitylistentry',
        )
        for field, filters, expected in (
            ('community_list', 'community: {exact: "65000:1"}', {self.std.pk}),
            ('community_list', 'type: {exact: "extended"}', {self.ext.pk}),
            ('community_list', 'name: {exact: "first"}', {self.std.pk}),
            ('community_list', 'status: {exact: "reserved"}', {self.ext.pk}),
            ('communitylist_list', 'name: {exact: "Ext"}', {self.ext_list.pk}),
            ('communitylist_list', 'type: {exact: "standard"}', {self.std_list.pk}),
            (
                'communitylistentry_list',
                'sequence: {filter_lookup: {exact: 20}}',
                {self.e2.pk},
            ),
            ('communitylistentry_list', 'action: {exact: "deny"}', {self.e2.pk}),
        ):
            with self.subTest(field=field, filters=filters):
                self.assertEqual(self.ids(field, filters), expected)


class CommunityAPIExtraFieldsTestCase(APITestCase):
    """owner, tags and custom fields can be written and read in the three objects"""

    @classmethod
    def setUpTestData(cls):
        cls.owner = Owner.objects.create(name='Team')
        cls.tag = Tag.objects.create(name='edge', slug='edge')
        cls.community = Community.objects.create(community='65000:1')
        cls.community_list = CommunityList.objects.create(name='L')
        cls.field = CustomField.objects.create(
            name='note', type=CustomFieldTypeChoices.TYPE_TEXT, required=False
        )
        cls.field.object_types.set(
            [
                ContentType.objects.get_for_model(model)
                for model in (Community, CommunityList, CommunityListEntry)
            ]
        )

    def setUp(self):
        super().setUp()
        for model in ('community', 'communitylist', 'communitylistentry'):
            self.add_permissions(
                *(
                    f'netbox_routing_plugin.{action}_{model}'
                    for action in ('add', 'change', 'view')
                )
            )
        self.add_permissions('extras.view_tag', 'users.view_owner')

    def check(self, data):
        self.assertEqual(data['owner']['name'], 'Team')
        self.assertEqual([t['name'] for t in data['tags']], ['edge'])
        self.assertEqual(data['custom_fields']['note'], 'hello')
        self.assertIn('created', data)
        self.assertIn('last_updated', data)

    def extras(self, note='hello'):
        return {
            'owner': {'name': 'Team'},
            'tags': [{'name': 'edge'}],
            'custom_fields': {'note': note},
        }

    def test_create_update_and_read(self):
        cases = (
            ('community', {'community': '65000:55'}),
            ('communitylist', {'name': 'Created'}),
            (
                'communitylistentry',
                {
                    'community_list': self.community_list.pk,
                    'community': self.community.pk,
                    'action': 'permit',
                },
            ),
        )
        for name, data in cases:
            with self.subTest(name):
                response = self.client.post(
                    reverse(API + f'{name}-list'),
                    {**data, **self.extras()},
                    format='json',
                    **self.header,
                )
                self.assertHttpStatus(response, 201)
                self.check(response.data)
                url = reverse(
                    API + f'{name}-detail', kwargs={'pk': response.data['id']}
                )

                response = self.client.patch(
                    url,
                    {'custom_fields': {'note': 'changed'}, 'tags': []},
                    format='json',
                    **self.header,
                )
                self.assertHttpStatus(response, 200)
                self.assertEqual(response.data['custom_fields']['note'], 'changed')
                self.assertEqual(response.data['tags'], [])
                self.assertEqual(response.data['owner']['name'], 'Team')

                response = self.client.get(url, **self.header)
                self.assertHttpStatus(response, 200)
                self.assertEqual(response.data['custom_fields']['note'], 'changed')

    def test_community_reports_type_and_well_known(self):
        response = self.client.post(
            reverse(API + 'community-list'),
            {'community': 'no-export'},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['community'], '65535:65281')
        self.assertEqual(response.data['type']['value'], 'standard')
        self.assertEqual(response.data['well_known'], 'NO_EXPORT (RFC 1997)')
        self.assertEqual(response.data['name'], 'NO_EXPORT')
