from django.urls import reverse
from ipam.models import Role
from tenancy.models import Tenant
from utilities.testing import APIViewTestCases, APITestCase

from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'CommunityTestCase',
    'CommunityListTestCase',
    'CommunityListEntryTestCase',
)


class CommunityTestCase(APIViewTestCases.APIViewTestCase):
    model = Community
    view_namespace = "plugins-api:netbox_routing_protocols"
    brief_fields = [
        'community',
        'description',
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'status': 'reserved'}

    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(name='Test Role')
        communities = (
            Community(community='64512', status='active', role=role),
            Community(community='64513', status='active', role=role),
            Community(community='64514', status='active', role=role),
        )
        Community.objects.bulk_create(communities)

        cls.create_data = [
            {
                'community': '64512:1',
                'status': 'active',
                'role': role.pk,
            },
            {
                'community': '64512:2:3',
                'status': 'active',
                'role': role.pk,
            },
        ]


class CommunityListTestCase(LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase):
    model = CommunityList
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'communitylist'
    brief_fields = [
        'description',
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {}

    @classmethod
    def setUpTestData(cls):
        community_lists = (
            CommunityList(
                name='Community List 1',
            ),
            CommunityList(
                name='Community List 2',
            ),
            CommunityList(
                name='Community List 3',
            ),
        )
        CommunityList.objects.bulk_create(community_lists)

        cls.create_data = [
            {
                'name': 'Community List 4',
            },
            {
                'name': 'Community List 5',
            },
        ]

        tenant = Tenant.objects.create(name='Test Tenant')
        cls.bulk_update_data = {'tenant': tenant.pk}


class CommunityListEntryTestCase(APIViewTestCases):
    model = CommunityListEntry
    view_namespace = "plugins-api:netbox_routing_protocols"
    graphql_base_name = 'communitylistentry'
    brief_fields = [
        'community',
        'community_list',
        'description',
        'display',
        'id',
        'url',
    ]

    bulk_update_data = {}

    @classmethod
    def setUpTestData(cls):
        tenant = Tenant.objects.create(name='Test Tenant', slug='test-tenant')
        role = Role.objects.create(name='Test Role', slug='test-role')
        communities = (
            Community(
                community='64512',
                status='active',
                role=role,
                tenant=tenant,
            ),
            Community(
                community='64513',
                status='active',
                role=role,
                tenant=tenant,
            ),
            Community(
                community='64514',
                status='active',
                role=role,
                tenant=tenant,
            ),
        )
        Community.objects.bulk_create(communities)
        community_lists = (
            CommunityList(
                name='Community List 1',
                tenant=tenant,
            ),
        )
        CommunityList.objects.bulk_create(community_lists)

        cls.create_data = [
            {
                'community_list': community_lists[0].pk,
                'community': communities[0].pk,
            },
            {
                'community_list': community_lists[0].pk,
                'community': communities[1].pk,
            },
            {
                'community_list': community_lists[0].pk,
                'community': communities[2].pk,
            },
        ]

        cls.bulk_update_data = {'description': 'Test updated description'}


class CommunityApiShapeTestCase(APITestCase):
    """Foreign keys are nested objects and the choices are {value, label}."""

    user_permissions = (
        'netbox_routing_protocols.view_communitylistentry',
        'netbox_routing_protocols.view_community',
    )

    def test_entry_and_community_shape(self):
        lst = CommunityList.objects.create(name='L')
        comm = Community.objects.create(community='65000:1')
        entry = CommunityListEntry.objects.create(
            community_list=lst, sequence=10, community=comm, action='permit'
        )
        self.add_permissions(*self.user_permissions)
        base = 'plugins-api:netbox_routing_protocols-api'

        data = self.client.get(
            reverse(f'{base}:communitylistentry-detail', kwargs={'pk': entry.pk}),
            **self.header,
        ).json()
        self.assertEqual(data['community_list']['id'], lst.pk)
        self.assertEqual(data['community']['community'], '65000:1')
        self.assertEqual(data['action']['value'], 'permit')

        data = self.client.get(
            reverse(f'{base}:community-detail', kwargs={'pk': comm.pk}),
            **self.header,
        ).json()
        self.assertEqual(data['status']['value'], 'active')
