from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from netbox.graphql.schema import schema
from utilities.testing import APITestCase, create_test_device

from netbox_routing_plugin.models import OSPFArea, OSPFInstance

__all__ = ('OSPFGraphQLReverseRelationsTestCase', 'OSPFGraphQLQueryTestCase')


class OSPFGraphQLReverseRelationsTestCase(TestCase):
    """The parents expose their children, so one query walks the whole tree."""

    RELATIONS = {
        'OSPFInstanceType': {
            'areas',
            'interfaces',
            'redistributions',
            'virtual_links',
            'summary_addresses',
            'prefix_sids',
        },
        'OSPFAreaType': {'interfaces', 'virtual_links', 'ranges'},
        'OSPFInterfaceType': {'networks', 'neighbors'},
    }

    def test_children_are_exposed(self):
        for typename, expected in self.RELATIONS.items():
            with self.subTest(typename=typename):
                gql_type = schema.schema_converter.type_map[typename]
                fields = {f.name for f in gql_type.definition.fields}
                self.assertLessEqual(expected, fields)


class OSPFGraphQLQueryTestCase(APITestCase):
    def test_instance_tree_query(self):
        device = create_test_device(name='Device 1')
        instance = OSPFInstance.objects.create(
            name='Instance 1', device=device, router_id='1.1.1.1'
        )
        OSPFArea.objects.create(instance=instance, area_id='1')
        self.add_permissions(
            'netbox_routing_plugin.view_ospfinstance',
            'netbox_routing_plugin.view_ospfarea',
            'dcim.view_device',
        )
        query = f'{{ ospf_instance(id: {instance.pk}) {{ areas {{ area_id }} interfaces {{ id }} }} }}'
        response = self.client.post(
            reverse('graphql'), {'query': query}, format='json', **self.header
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        data = response.json()
        self.assertNotIn('errors', data)
        self.assertEqual(data['data']['ospf_instance']['areas'], [{'area_id': '1'}])
