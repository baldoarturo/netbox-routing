from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from utilities.testing import APITestCase, create_test_device

from netbox_routing_plugin.filtersets import (
    EIGRPRouterFilterSet,
    ISISInstanceFilterSet,
    OSPFInstanceFilterSet,
)
from netbox_routing_plugin.models import (
    EIGRPRouter,
    ISISInstance,
    OSPFInstance,
    RoutePolicy,
)


def make_ospf(device, **fields):
    return OSPFInstance.objects.create(
        name='OSPF', device=device, router_id='1.1.1.1', **fields
    )


def make_isis(device, **fields):
    return ISISInstance.objects.create(device=device, process_tag='core', **fields)


def make_eigrp(device, **fields):
    return EIGRPRouter.objects.create(
        device=device, mode='classic', pid=1, rid='1.1.1.1', **fields
    )


# (model, factory, basename of the API and the pages, filter set)
PROTOCOLS = (
    (OSPFInstance, make_ospf, 'ospfinstance', OSPFInstanceFilterSet),
    (ISISInstance, make_isis, 'isisinstance', ISISInstanceFilterSet),
    (EIGRPRouter, make_eigrp, 'eigrprouter', EIGRPRouterFilterSet),
)


class ProtocolRoutePolicyTestCase(TestCase):
    """The import and the export policy of the instance of every protocol"""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.imp = RoutePolicy.objects.create(name='Import')
        cls.exp = RoutePolicy.objects.create(name='Export')

    def test_both_are_optional_and_saved(self):
        for model, make, _name, _filterset in PROTOCOLS:
            with self.subTest(model.__name__):
                instance = make(self.device)
                self.assertIsNone(instance.import_policy)
                self.assertIsNone(instance.export_policy)
                instance.import_policy = self.imp
                instance.export_policy = self.exp
                instance.full_clean()
                instance.save()
                instance = model.objects.get(pk=instance.pk)
                self.assertEqual(
                    (instance.import_policy, instance.export_policy),
                    (self.imp, self.exp),
                )
                instance.delete()

    def test_a_policy_in_use_cannot_be_deleted(self):
        for model, make, _name, _filterset in PROTOCOLS:
            for field in ('import_policy', 'export_policy'):
                with self.subTest(f'{model.__name__} {field}'):
                    policy = RoutePolicy.objects.create(name=f'{model.__name__}{field}')
                    instance = make(self.device, **{field: policy})
                    with self.assertRaises(ProtectedError):
                        policy.delete()
                    instance.delete()
                    policy.delete()

    def test_the_instances_can_be_filtered_by_policy(self):
        for model, make, _name, filterset in PROTOCOLS:
            with self.subTest(model.__name__):
                used = make(self.device, import_policy=self.imp, export_policy=self.exp)
                other = make(create_test_device(name=f'{model.__name__} other'))
                queryset = model.objects.all()
                for params in (
                    {'import_policy_id': [self.imp.pk]},
                    {'export_policy_id': [self.exp.pk]},
                    {'import_policy': [self.imp.name]},
                    {'export_policy': [self.exp.name]},
                ):
                    self.assertEqual(list(filterset(params, queryset).qs), [used])
                used.delete()
                other.delete()


class ProtocolRoutePolicyPagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.imp = RoutePolicy.objects.create(name='Import')
        cls.exp = RoutePolicy.objects.create(name='Export')
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')

    def test_the_page_and_the_list_show_the_policies(self):
        self.client.force_login(self.user)
        for _model, make, name, _filterset in PROTOCOLS:
            with self.subTest(name):
                instance = make(
                    self.device, import_policy=self.imp, export_policy=self.exp
                )
                page = self.client.get(instance.get_absolute_url())
                self.assertContains(page, self.imp.get_absolute_url())
                self.assertContains(page, self.exp.get_absolute_url())
                listing = self.client.get(
                    reverse(f'plugins:netbox_routing_plugin:{name}_list')
                    + f'?import_policy_id={self.imp.pk}'
                )
                self.assertEqual(listing.status_code, 200)
                self.assertContains(listing, instance.get_absolute_url())
                instance.delete()

    def test_the_delete_of_a_policy_in_use_is_refused(self):
        self.client.force_login(self.user)
        for model, make, name, _filterset in PROTOCOLS:
            with self.subTest(name):
                instance = make(self.device, import_policy=self.imp)
                self.client.post(
                    self.imp.get_absolute_url() + 'delete/',
                    {'confirm': True},
                    follow=True,
                )
                self.assertTrue(RoutePolicy.objects.filter(pk=self.imp.pk).exists())
                instance.delete()


class ProtocolRoutePolicyAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.device = create_test_device(name='Device 1')
        self.imp = RoutePolicy.objects.create(name='Import')
        self.exp = RoutePolicy.objects.create(name='Export')

    def test_the_policies_go_through_the_api(self):
        for model, make, name, _filterset in PROTOCOLS:
            with self.subTest(name):
                self.add_permissions(
                    f'netbox_routing_plugin.change_{name}',
                    f'netbox_routing_plugin.view_{name}',
                )
                instance = make(self.device)
                url = reverse(
                    f'plugins-api:netbox_routing_plugin-api:{name}-detail',
                    kwargs={'pk': instance.pk},
                )
                response = self.client.patch(
                    url,
                    {'import_policy': self.imp.pk, 'export_policy': self.exp.pk},
                    format='json',
                    **self.header,
                )
                self.assertHttpStatus(response, 200)
                self.assertEqual(response.data['import_policy']['id'], self.imp.pk)
                self.assertEqual(response.data['export_policy']['id'], self.exp.pk)
                response = self.client.patch(
                    url, {'import_policy': None}, format='json', **self.header
                )
                self.assertHttpStatus(response, 200)
                self.assertIsNone(response.data['import_policy'])
                instance.delete()
