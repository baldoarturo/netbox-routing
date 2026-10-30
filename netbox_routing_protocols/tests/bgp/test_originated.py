from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from ipam.models import Prefix, VRF
from utilities.testing import APIViewTestCases, ViewTestCases

from netbox_routing_protocols.models import (
    BGPAddressFamily,
    BGPAggregate,
    BGPOriginatedNetwork,
)
from netbox_routing_protocols.tests.base import (
    BulkEditMixin,
    LeanCoreTestsMixin,
    PluginBaseURLMixin,
)
from netbox_routing_protocols.tests.bgp.base import BGPInstanceMixin

__all__ = (
    'BGPOriginatedNetworkModelTestCase',
    'BGPAggregateModelTestCase',
    'BGPOriginatedNetworkAPITestCase',
    'BGPAggregateAPITestCase',
    'BGPOriginatedNetworkViewTestCase',
    'BGPAggregateViewTestCase',
)


class _PrefixRulesMixin(BGPInstanceMixin):
    """A prefix of IPAM originated or aggregated by an address family: in the VRF of the
    instance and of the IP version of the family (#528)"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.af = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv4-unicast'
        )
        cls.af_v6 = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv6-unicast'
        )
        cls.evpn = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='l2vpn-evpn'
        )
        cls.prefix = Prefix.objects.create(prefix='10.9.0.0/16')
        cls.prefix_v6 = Prefix.objects.create(prefix='2001:db8::/32')
        cls.vrf = VRF.objects.create(name='Blue')
        cls.prefix_in_vrf = Prefix.objects.create(prefix='10.8.0.0/16', vrf=cls.vrf)


class BGPOriginatedNetworkModelTestCase(_PrefixRulesMixin, TestCase):
    def _network(self, **kwargs):
        kwargs.setdefault('address_family', self.af)
        kwargs.setdefault('prefix', self.prefix)
        return BGPOriginatedNetwork(**kwargs)

    def test_a_prefix_of_the_instance_vrf_and_version(self):
        self._network().full_clean()
        self._network(address_family=self.af_v6, prefix=self.prefix_v6).full_clean()

    def test_the_prefix_is_in_the_vrf_of_the_instance(self):
        with self.assertRaises(ValidationError) as cm:
            self._network(prefix=self.prefix_in_vrf).full_clean()
        self.assertIn('prefix', cm.exception.error_dict)
        vrf_instance_af = BGPAddressFamily.objects.create(
            instance=type(self.bgp_instance).objects.create(
                name='VRF',
                device=self.bgp_instance.device,
                asn=self.asns[2],
                vrf=self.vrf,
            ),
            address_family='ipv4-unicast',
        )
        self._network(
            address_family=vrf_instance_af, prefix=self.prefix_in_vrf
        ).full_clean()

    def test_the_version_of_the_prefix_is_the_one_of_the_family(self):
        with self.assertRaises(ValidationError) as cm:
            self._network(address_family=self.af_v6).full_clean()
        self.assertIn('prefix', cm.exception.error_dict)

    def test_a_family_without_prefixes_originates_nothing(self):
        with self.assertRaises(ValidationError) as cm:
            self._network(address_family=self.evpn).full_clean()
        self.assertIn('address_family', cm.exception.error_dict)

    def test_one_prefix_once_per_family(self):
        self._network().save()
        with self.assertRaises(ValidationError):
            self._network().full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._network().save()

    def test_a_prefix_originated_cannot_be_deleted(self):
        self._network().save()
        with self.assertRaises(ProtectedError):
            self.prefix.delete()


class BGPAggregateModelTestCase(_PrefixRulesMixin, TestCase):
    def _aggregate(self, **kwargs):
        kwargs.setdefault('address_family', self.af)
        kwargs.setdefault('prefix', self.prefix)
        return BGPAggregate(**kwargs)

    def test_the_attributes_are_per_aggregate(self):
        aggregate = self._aggregate(summary_only=True, as_set=False)
        aggregate.full_clean()
        aggregate.save()
        other = Prefix.objects.create(prefix='10.10.0.0/16')
        self._aggregate(prefix=other, as_set=True).full_clean()
        self.assertTrue(BGPAggregate.objects.get(prefix=self.prefix).summary_only)
        self.assertFalse(BGPAggregate.objects.get(prefix=self.prefix).as_set)

    def test_the_same_rules_as_the_originated_networks(self):
        with self.assertRaises(ValidationError) as cm:
            self._aggregate(prefix=self.prefix_v6).full_clean()
        self.assertIn('prefix', cm.exception.error_dict)
        with self.assertRaises(ValidationError) as cm:
            self._aggregate(address_family=self.evpn).full_clean()
        self.assertIn('address_family', cm.exception.error_dict)
        with self.assertRaises(ValidationError) as cm:
            self._aggregate(prefix=self.prefix_in_vrf).full_clean()
        self.assertIn('prefix', cm.exception.error_dict)


class BGPOriginatedNetworkAPITestCase(
    LeanCoreTestsMixin, _PrefixRulesMixin, APIViewTestCases.APIViewTestCase
):
    model = BGPOriginatedNetwork
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['address_family', 'display', 'id', 'prefix', 'url']
    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        prefixes = [
            Prefix.objects.create(prefix=f'10.{i}.0.0/16') for i in range(20, 25)
        ]
        cls.model.objects.bulk_create(
            [cls.model(address_family=cls.af, prefix=p) for p in prefixes[:3]]
        )
        cls.create_data = [
            {'address_family': cls.af.pk, 'prefix': prefixes[3].pk},
            {'address_family': cls.af.pk, 'prefix': prefixes[4].pk},
        ]


class BGPAggregateAPITestCase(
    LeanCoreTestsMixin, _PrefixRulesMixin, APIViewTestCases.APIViewTestCase
):
    model = BGPAggregate
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['address_family', 'display', 'id', 'prefix', 'url']
    bulk_update_data = {'summary_only': True}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        prefixes = [
            Prefix.objects.create(prefix=f'10.{i}.0.0/16') for i in range(30, 35)
        ]
        cls.model.objects.bulk_create(
            [cls.model(address_family=cls.af, prefix=p) for p in prefixes[:3]]
        )
        cls.create_data = [
            {
                'address_family': cls.af.pk,
                'prefix': prefixes[3].pk,
                'summary_only': True,
            },
            {'address_family': cls.af.pk, 'prefix': prefixes[4].pk, 'as_set': True},
        ]


class BGPOriginatedNetworkViewTestCase(
    BGPInstanceMixin,
    LeanCoreTestsMixin,
    BulkEditMixin,
    PluginBaseURLMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = BGPOriginatedNetwork

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        af = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv4-unicast'
        )
        prefixes = [
            Prefix.objects.create(prefix=f'10.{i}.0.0/16') for i in range(40, 44)
        ]
        cls.model.objects.bulk_create(
            [cls.model(address_family=af, prefix=prefixes[i]) for i in range(3)]
        )
        cls.form_data = {'address_family': af.pk, 'prefix': prefixes[3].pk}
        cls.bulk_edit_data = {'description': 'Originated'}


class BGPAggregateViewTestCase(
    BGPInstanceMixin,
    LeanCoreTestsMixin,
    BulkEditMixin,
    PluginBaseURLMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = BGPAggregate

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        af = BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family='ipv4-unicast'
        )
        prefixes = [
            Prefix.objects.create(prefix=f'10.{i}.0.0/16') for i in range(50, 54)
        ]
        cls.model.objects.bulk_create(
            [cls.model(address_family=af, prefix=prefixes[i]) for i in range(3)]
        )
        cls.form_data = {
            'address_family': af.pk,
            'prefix': prefixes[3].pk,
            'summary_only': True,
            'as_set': False,
        }
        print('AGG FORM CHECK', cls.form_data)
        cls.bulk_edit_data = {'summary_only': True}
