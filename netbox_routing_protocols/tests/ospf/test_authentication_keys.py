from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF
from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.choices import (
    OSPFAddressFamilyChoices,
    OSPFAuthenticationChoices,
    OSPFMessageDigestAlgorithmChoices,
)
from netbox_routing_protocols.filtersets import OSPFAuthenticationKeyFilterSet
from netbox_routing_protocols.forms import OSPFAuthenticationKeyImportForm
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFAuthenticationKey,
    OSPFInstance,
    OSPFInterface,
)
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'OSPFAuthenticationKeyModelTestCase',
    'OSPFAuthenticationKeyViewTestCase',
    'OSPFAuthenticationKeyAPITestCase',
)

MD = OSPFAuthenticationChoices.MESSAGE_DIGEST
TRAILER = OSPFAuthenticationChoices.TRAILER
SHA256 = OSPFMessageDigestAlgorithmChoices.HMAC_SHA_256


def _create_fixtures(cls):
    cls.device = create_test_device(name='Device 1')
    cls.instances = [
        OSPFInstance.objects.create(
            name=f'Instance {i}',
            device=cls.device,
            router_id=f'{i}.{i}.{i}.{i}',
            vrf=VRF.objects.create(name=f'VRF {i}'),
            authentication=MD,
            passphrase='primary',
            authentication_key_id=1,
        )
        for i in (1, 2)
    ]


class OSPFAuthenticationKeyModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        cls.area = OSPFArea.objects.create(
            instance=cls.instances[0],
            area_id='1',
            authentication=MD,
            passphrase='area',
            authentication_key_id=1,
        )
        cls.interface = Interface.objects.create(
            name='Eth1', device=cls.device, type='virtual', vrf=cls.instances[0].vrf
        )
        cls.ospf_interface = OSPFInterface.objects.create(
            instance=cls.instances[0], area=cls.area, interface=cls.interface
        )

    def _key(self, **kwargs):
        values = {'instance': self.instances[0], 'key_id': 2, 'passphrase': 'next'}
        values.update(kwargs)
        return OSPFAuthenticationKey(**values)

    def _assert_invalid(self, key, field=None):
        with self.assertRaises(ValidationError) as cm:
            key.full_clean()
        if field:
            self.assertIn(field, cm.exception.error_dict)

    def test_key_of_each_parent(self):
        self._key().full_clean()
        self._key(instance=None, area=self.area).full_clean()
        self._key(instance=None, ospf_interface=self.ospf_interface).full_clean()

    def test_exactly_one_parent(self):
        self._assert_invalid(self._key(instance=None))
        self._assert_invalid(self._key(area=self.area))

    def test_parent_needs_cryptographic_authentication(self):
        self.instances[0].authentication = OSPFAuthenticationChoices.NULL
        self.instances[0].passphrase = None
        self.instances[0].authentication_key_id = None
        self.instances[0].save()
        self._assert_invalid(self._key())

    def test_key_id_is_not_the_one_of_the_authentication(self):
        self._assert_invalid(self._key(key_id=1), 'key_id')

    def test_key_id_unique_per_parent_only(self):
        self._key().save()
        other = self._key()
        self._assert_invalid(other)
        with self.assertRaises(IntegrityError), transaction.atomic():
            other.save()
        self._key(instance=self.instances[1]).full_clean()

    def test_message_digest_key_id_and_md5_length(self):
        self._assert_invalid(self._key(key_id=256), 'key_id')
        self._assert_invalid(self._key(passphrase='x' * 17), 'passphrase')

    def test_trailer_keys(self):
        v6 = OSPFInstance.objects.create(
            name='v3',
            device=self.device,
            router_id='3.3.3.3',
            address_family=OSPFAddressFamilyChoices.IPV6,
            authentication=TRAILER,
            passphrase='primary',
            authentication_key_id=1,
            message_digest_algorithm=SHA256,
        )
        self._key(
            instance=v6, key_id=60000, message_digest_algorithm=SHA256
        ).full_clean()
        self._assert_invalid(
            self._key(instance=v6, key_id=2), 'message_digest_algorithm'
        )

    def test_lifetimes_go_in_order(self):
        def at(day):
            return datetime(2027, 1, day, tzinfo=timezone.utc)

        self._key(
            accept_from=at(1), send_from=at(2), send_until=at(20), accept_until=at(21)
        ).full_clean()
        self._assert_invalid(self._key(send_from=at(5), send_until=at(2)), 'send_until')
        self._assert_invalid(self._key(accept_from=at(5), send_from=at(2)), 'send_from')

    def test_parent_cannot_drop_the_authentication_with_keys(self):
        self._key().save()
        self.instances[0].authentication = OSPFAuthenticationChoices.NULL
        self.instances[0].passphrase = None
        self.instances[0].authentication_key_id = None
        self._assert_invalid(self.instances[0], 'authentication')

    def test_filter_by_parent(self):
        key = self._key()
        key.save()
        self._key(instance=self.instances[1]).save()
        qs = OSPFAuthenticationKeyFilterSet(
            {'instance_id': [self.instances[0].pk]}, OSPFAuthenticationKey.objects.all()
        ).qs
        self.assertEqual(list(qs), [key])

    def test_import_on_an_area(self):
        form = OSPFAuthenticationKeyImportForm(
            data={
                'device': 'Device 1',
                'instance': 'Instance 1',
                'area': '1',
                'key_id': '2',
                'passphrase': 'next',
            }
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        key = form.save()
        self.assertEqual(key.area, self.area)
        self.assertIsNone(key.instance)


class OSPFAuthenticationKeyViewTestCase(
    LeanCoreTestsMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = OSPFAuthenticationKey

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFAuthenticationKey.objects.bulk_create(
            (
                OSPFAuthenticationKey(
                    instance=cls.instances[0], key_id=2, passphrase='a'
                ),
                OSPFAuthenticationKey(
                    instance=cls.instances[0], key_id=3, passphrase='b'
                ),
                OSPFAuthenticationKey(
                    instance=cls.instances[1], key_id=2, passphrase='c'
                ),
            )
        )
        cls.form_data = {
            'instance': cls.instances[1].pk,
            'key_id': 5,
            'passphrase': 'new',
            'message_digest_algorithm': SHA256,
        }
        cls.bulk_edit_data = {'description': 'A test description'}

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfauthenticationkey_{}'


class OSPFAuthenticationKeyAPITestCase(
    LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase
):
    model = OSPFAuthenticationKey
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['display', 'id', 'key_id', 'url']

    user_permissions = (
        'netbox_routing_protocols.view_ospfinstance',
        'dcim.view_device',
    )

    bulk_update_data = {'description': 'A test description'}

    @classmethod
    def setUpTestData(cls):
        _create_fixtures(cls)
        OSPFAuthenticationKey.objects.bulk_create(
            (
                OSPFAuthenticationKey(
                    instance=cls.instances[0], key_id=2, passphrase='a'
                ),
                OSPFAuthenticationKey(
                    instance=cls.instances[0], key_id=3, passphrase='b'
                ),
                OSPFAuthenticationKey(
                    instance=cls.instances[1], key_id=2, passphrase='c'
                ),
            )
        )
        cls.create_data = [
            {
                'instance': cls.instances[1].pk,
                'key_id': 5,
                'passphrase': 'new',
                'message_digest_algorithm': SHA256,
            },
        ]
