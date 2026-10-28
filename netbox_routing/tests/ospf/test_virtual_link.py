from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing.filtersets import OSPFVirtualLinkFilterSet
from netbox_routing.forms import OSPFVirtualLinkForm
from netbox_routing.models import OSPFArea, OSPFInstance, OSPFVirtualLink
from netbox_routing.tests.base import IPAddressFieldMixin

__all__ = (
    'OSPFVirtualLinkModelTestCase',
    'OSPFVirtualLinkFormTestCase',
    'OSPFVirtualLinkFilterSetTestCase',
    'OSPFVirtualLinkViewTestCase',
    'OSPFVirtualLinkAPITestCase',
)

MD = {
    'authentication': 'message-digest',
    'authentication_key_id': 1,
    'passphrase': 'password',
}


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instance = OSPFInstance.objects.create(
        name='Instance 1', device=cls.device, router_id='1.1.1.1', process_id=1
    )
    cls.other_instance = OSPFInstance.objects.create(
        name='Instance 2', device=cls.device, router_id='2.2.2.2', process_id=2
    )
    cls.backbone = OSPFArea.objects.create(
        instance=cls.instance, area_id='0', area_type='backbone'
    )
    cls.transit = OSPFArea.objects.create(instance=cls.instance, area_id='1')
    cls.transit2 = OSPFArea.objects.create(instance=cls.instance, area_id='4')
    cls.stub = OSPFArea.objects.create(
        instance=cls.instance, area_id='2', area_type='stub'
    )
    cls.nssa = OSPFArea.objects.create(
        instance=cls.instance, area_id='3', area_type='nssa'
    )
    cls.foreign = OSPFArea.objects.create(instance=cls.other_instance, area_id='1')


class OSPFVirtualLinkModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def _link(self, **kwargs):
        kwargs.setdefault('instance', self.instance)
        kwargs.setdefault('transit_area', self.transit)
        kwargs.setdefault('remote_router_id', '9.9.9.9')
        return OSPFVirtualLink(**kwargs)

    def _assert_invalid(self, field, **kwargs):
        with self.assertRaises(ValidationError) as cm:
            self._link(**kwargs).full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_defaults(self):
        link = self._link()
        link.full_clean()
        self.assertEqual(
            (
                link.hello_interval,
                link.dead_interval,
                link.retransmit_interval,
                link.transmit_delay,
            ),
            (10, 40, 5, 1),
        )
        self.assertEqual(link.message_digest_algorithm, 'md5')
        self.assertEqual(str(link), '9.9.9.9 via area 1')

    def test_the_transit_area_must_be_a_standard_area(self):
        self._assert_invalid('transit_area', transit_area=self.backbone)
        self._assert_invalid('transit_area', transit_area=self.stub)
        self._assert_invalid('transit_area', transit_area=self.nssa)

    def test_the_transit_area_must_belong_to_the_instance(self):
        self._assert_invalid('transit_area', transit_area=self.foreign)

    def test_remote_router_id(self):
        for value in ('2001:db8::1', '0.0.0.0', '1.1.1.1'):
            with self.subTest(value=value):
                self._assert_invalid('remote_router_id', remote_router_id=value)

    def test_timers_follow_the_interface_rules(self):
        self._assert_invalid('dead_interval', hello_interval=40, dead_interval=40)
        self._assert_invalid('hello_interval', hello_interval=0)
        self._assert_invalid('transmit_delay', transmit_delay=0)

    def test_authentication_block_is_validated(self):
        self._link(**MD).full_clean()
        self._assert_invalid(
            'authentication_key_id', authentication='message-digest', passphrase='x'
        )
        self._assert_invalid('passphrase', passphrase='password')

    def test_a_virtual_link_exists_once_per_transit_area_and_remote(self):
        OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit,
            remote_router_id='9.9.9.9',
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            OSPFVirtualLink.objects.create(
                instance=self.instance,
                transit_area=self.transit,
                remote_router_id='9.9.9.9',
            )
        OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit2,
            remote_router_id='9.9.9.9',
        )

    def test_it_uses_the_authentication_of_the_backbone_then_the_instance(self):
        link = self._link()
        self.assertIsNone(link.effective_authentication)
        OSPFInstance.objects.filter(pk=self.instance.pk).update(**MD)
        link.instance = OSPFInstance.objects.get(pk=self.instance.pk)
        self.assertEqual(
            (link.effective_authentication, link.authentication_source),
            ('message-digest', 'instance'),
        )
        OSPFArea.objects.filter(pk=self.backbone.pk).update(
            authentication='key-chain', key_chain='chain'
        )
        self.assertEqual(
            (link.effective_authentication, link.authentication_source),
            ('key-chain', 'area'),
        )
        link.authentication = 'message-digest'
        self.assertEqual(link.authentication_source, 'virtual link')

    def test_the_authentication_type_must_agree_with_the_backbone(self):
        OSPFArea.objects.filter(pk=self.backbone.pk).update(**MD)
        self._assert_invalid('authentication', authentication='null')
        self._link(authentication='key-chain', key_chain='chain').full_clean()

    def test_the_backbone_authentication_is_checked_against_its_virtual_links(self):
        OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit,
            remote_router_id='9.9.9.9',
            authentication='null',
        )
        self.backbone.authentication = 'message-digest'
        self.backbone.authentication_key_id = 1
        self.backbone.passphrase = 'password'
        with self.assertRaises(ValidationError) as cm:
            self.backbone.full_clean()
        self.assertIn('authentication', cm.exception.error_dict)
        self.assertIn('9.9.9.9', str(cm.exception))

    def test_the_transit_area_cannot_be_deleted_while_it_is_crossed(self):
        from django.db.models import RestrictedError

        OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit,
            remote_router_id='9.9.9.9',
        )
        with self.assertRaises(RestrictedError):
            self.transit.delete()

    def test_deleting_the_instance_deletes_its_virtual_links(self):
        OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit,
            remote_router_id='9.9.9.9',
        )
        self.instance.delete()
        self.assertFalse(OSPFVirtualLink.objects.exists())


class OSPFVirtualLinkFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)

    def test_timers_and_algorithm_left_out_take_their_default(self):
        form = OSPFVirtualLinkForm(
            data={
                'instance': self.instance.pk,
                'transit_area': self.transit.pk,
                'remote_router_id': '9.9.9.9',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        link = form.save()
        self.assertEqual((link.hello_interval, link.dead_interval), (10, 40))
        self.assertEqual(link.message_digest_algorithm, 'md5')

    def test_form_rejects_a_stub_transit_area(self):
        form = OSPFVirtualLinkForm(
            data={
                'instance': self.instance.pk,
                'transit_area': self.stub.pk,
                'remote_router_id': '9.9.9.9',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('transit_area', form.errors)


class OSPFVirtualLinkFilterSetTestCase(TestCase):
    queryset = OSPFVirtualLink.objects.all()
    filterset = OSPFVirtualLinkFilterSet

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFVirtualLink.objects.bulk_create(
            (
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit,
                    remote_router_id='9.9.9.9',
                    hello_interval=30,
                ),
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit2,
                    remote_router_id='8.8.8.8',
                    authentication='message-digest',
                ),
                OSPFVirtualLink(
                    instance=cls.other_instance,
                    transit_area=cls.foreign,
                    remote_router_id='9.9.9.9',
                ),
            )
        )

    def count(self, params):
        return self.filterset(params, self.queryset).qs.count()

    def test_filters(self):
        for params, expected in (
            ({'instance_id': [self.instance.pk]}, 2),
            ({'instance': ['Instance 2']}, 1),
            ({'device_id': [self.device.pk]}, 3),
            ({'transit_area_id': [self.transit.pk]}, 1),
            ({'remote_router_id': ['9.9.9.9']}, 2),
            ({'hello_interval': [30]}, 1),
            ({'authentication': ['message-digest']}, 1),
            ({'q': '8.8.8.8'}, 1),
        ):
            with self.subTest(params=params):
                self.assertEqual(self.count(params), expected)


class OSPFVirtualLinkViewTestCase(
    IPAddressFieldMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFVirtualLink

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFVirtualLink.objects.bulk_create(
            (
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit,
                    remote_router_id='9.9.9.9',
                ),
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit,
                    remote_router_id='8.8.8.8',
                ),
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit2,
                    remote_router_id='9.9.9.9',
                ),
            )
        )
        cls.form_data = {
            'instance': cls.instance.pk,
            'transit_area': cls.transit2.pk,
            'remote_router_id': '7.7.7.7',
            'hello_interval': 20,
            'dead_interval': 80,
            'authentication': 'message-digest',
            'authentication_key_id': 2,
            'passphrase': 'password',
            'show_md5': True,
        }
        cls.bulk_edit_data = {'description': 'A test description', 'hello_interval': 15}

    def _get_base_url(self):
        return 'plugins:netbox_routing:ospfvirtuallink_{}'


class OSPFVirtualLinkAPITestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = OSPFVirtualLink
    view_namespace = 'plugins-api:netbox_routing'
    brief_fields = [
        'display',
        'id',
        'instance',
        'remote_router_id',
        'transit_area',
        'url',
    ]

    user_permissions = (
        'netbox_routing.view_ospfinstance',
        'netbox_routing.view_ospfarea',
        'dcim.view_device',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFVirtualLink.objects.bulk_create(
            (
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit,
                    remote_router_id='9.9.9.9',
                ),
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit,
                    remote_router_id='8.8.8.8',
                ),
                OSPFVirtualLink(
                    instance=cls.instance,
                    transit_area=cls.transit2,
                    remote_router_id='9.9.9.9',
                ),
            )
        )
        cls.create_data = [
            {
                'instance': cls.instance.pk,
                'transit_area': cls.transit2.pk,
                'remote_router_id': '7.7.7.7',
                'hello_interval': 20,
                'dead_interval': 80,
                'authentication': 'message-digest',
                'authentication_key_id': 2,
                'passphrase': 'password',
                'show_md5': True,
            },
        ]

    def test_the_md5_digest_is_exposed_when_checked(self):
        self.add_permissions('netbox_routing.view_ospfvirtuallink')
        link = OSPFVirtualLink.objects.create(
            instance=self.instance,
            transit_area=self.transit2,
            remote_router_id='6.6.6.6',
            show_md5=True,
            **MD,
        )
        response = self.client.get(self._get_detail_url(link), **self.header)
        self.assertEqual(
            response.data['passphrase_md5'], '5f4dcc3b5aa765d61d8327deb882cf99'
        )
