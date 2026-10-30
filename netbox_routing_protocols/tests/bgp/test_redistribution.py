from django.core.exceptions import ValidationError
from django.test import TestCase
from ipam.models import ASN, RIR, VRF
from utilities.testing import APIViewTestCases, ViewTestCases, create_test_device

from netbox_routing_protocols.models import (
    BGPAddressFamily,
    BGPInstance,
    BGPRedistribution,
    EIGRPAddressFamily,
    EIGRPRouter,
    ISISAddressFamily,
    ISISInstance,
    OSPFInstance,
)
from netbox_routing_protocols.tests.base import (
    BulkEditMixin,
    LeanCoreTestsMixin,
    PluginBaseURLMixin,
)

__all__ = (
    'BGPRedistributionModelTestCase',
    'BGPRedistributionAPITestCase',
    'BGPRedistributionViewTestCase',
)


def _instance(device, asn, vrf=None, name='BGP'):
    return BGPInstance.objects.create(name=name, device=device, asn=asn, vrf=vrf)


class BGPRedistributionModelTestCase(TestCase):
    """A redistribution is per address family, and its source is on the same device,
    in the same VRF and runs the same IP version (#528)"""

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='RIR')
        cls.asn = ASN.objects.create(rir=rir, asn=64512)
        cls.device = create_test_device(name='Device')
        cls.instance = _instance(cls.device, cls.asn)
        cls.af = BGPAddressFamily.objects.create(
            instance=cls.instance, address_family='ipv4-unicast'
        )
        cls.af_v6 = BGPAddressFamily.objects.create(
            instance=cls.instance, address_family='ipv6-unicast'
        )
        cls.ospf = OSPFInstance.objects.create(
            name='OSPF', device=cls.device, router_id='1.1.1.1', address_family='ipv4'
        )
        cls.ospf_v6 = OSPFInstance.objects.create(
            name='OSPFv3', device=cls.device, router_id='1.1.1.2', address_family='ipv6'
        )
        cls.isis = ISISInstance.objects.create(device=cls.device, process_tag='core')
        ISISAddressFamily.objects.create(instance=cls.isis, address_family='ipv4')
        cls.eigrp_router = EIGRPRouter.objects.create(
            device=cls.device, mode='classic', pid=100
        )
        cls.eigrp = EIGRPAddressFamily.objects.create(router=cls.eigrp_router, family=4)

    def _redistribution(self, **kwargs):
        kwargs.setdefault('address_family', self.af)
        return BGPRedistribution(**kwargs)

    def test_each_protocol_needs_its_own_source(self):
        self._redistribution(protocol='connected').full_clean()
        self._redistribution(protocol='static').full_clean()
        self._redistribution(protocol='ospf', ospf_source=self.ospf).full_clean()
        self._redistribution(protocol='isis', isis_source=self.isis).full_clean()
        self._redistribution(protocol='eigrp', eigrp_source=self.eigrp).full_clean()
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='ospf').full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='static', ospf_source=self.ospf).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)

    def test_the_source_is_on_the_device_of_the_instance(self):
        other = OSPFInstance.objects.create(
            name='Other',
            device=create_test_device(name='Other'),
            router_id='2.2.2.2',
            address_family='ipv4',
        )
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='ospf', ospf_source=other).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)

    def test_the_source_is_in_the_vrf_of_the_instance(self):
        vrf = VRF.objects.create(name='VRF')
        in_vrf = OSPFInstance.objects.create(
            name='In VRF',
            device=self.device,
            vrf=vrf,
            router_id='3.3.3.3',
            address_family='ipv4',
        )
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='ospf', ospf_source=in_vrf).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)
        # an EIGRP address family in the global table cannot feed an instance in a VRF
        vrf_instance = _instance(self.device, self.asn, vrf=vrf, name='BGP VRF')
        vrf_af = BGPAddressFamily.objects.create(
            instance=vrf_instance, address_family='ipv4-unicast'
        )
        with self.assertRaises(ValidationError) as cm:
            BGPRedistribution(
                address_family=vrf_af, protocol='eigrp', eigrp_source=self.eigrp
            ).full_clean()
        self.assertIn('eigrp_source', cm.exception.error_dict)

    def test_the_source_runs_the_ip_version_of_the_address_family(self):
        # an IPv4 address family takes an IPv4 OSPF instance, not an IPv6 one
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='ospf', ospf_source=self.ospf_v6).full_clean()
        self.assertIn('ospf_source', cm.exception.error_dict)
        self._redistribution(
            address_family=self.af_v6, protocol='ospf', ospf_source=self.ospf_v6
        ).full_clean()
        # IS-IS: the instance must have the family
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                address_family=self.af_v6, protocol='isis', isis_source=self.isis
            ).full_clean()
        self.assertIn('isis_source', cm.exception.error_dict)
        # EIGRP: the address family of the source is of the same version
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                address_family=self.af_v6, protocol='eigrp', eigrp_source=self.eigrp
            ).full_clean()
        self.assertIn('eigrp_source', cm.exception.error_dict)

    def test_an_address_family_without_prefixes_takes_no_redistribution(self):
        evpn = BGPAddressFamily.objects.create(
            instance=self.instance, address_family='l2vpn-evpn'
        )
        for kwargs in ({'protocol': 'connected'}, {'protocol': 'static'}):
            with self.subTest(**kwargs):
                with self.assertRaises(ValidationError) as cm:
                    self._redistribution(address_family=evpn, **kwargs).full_clean()
                self.assertIn('address_family', cm.exception.error_dict)

    def test_vpn_families_carry_the_ip_version_of_their_prefixes(self):
        vpnv4 = BGPAddressFamily.objects.create(
            instance=self.instance, address_family='vpnv4-unicast'
        )
        self._redistribution(
            address_family=vpnv4, protocol='ospf', ospf_source=self.ospf
        ).full_clean()

    def test_route_types_only_with_ospf(self):
        self._redistribution(
            protocol='ospf', ospf_source=self.ospf, ospf_match=['internal']
        ).full_clean()
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(
                protocol='static', ospf_match=['internal']
            ).full_clean()
        self.assertIn('ospf_match', cm.exception.error_dict)

    def test_metric_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self._redistribution(protocol='connected', metric=4294967296).full_clean()
        self.assertIn('metric', cm.exception.error_dict)

    def test_one_redistribution_per_source_and_address_family(self):
        BGPRedistribution.objects.create(
            address_family=self.af, protocol='ospf', ospf_source=self.ospf
        )
        with self.assertRaises(ValidationError):
            self._redistribution(protocol='ospf', ospf_source=self.ospf).full_clean()
        # one connected and one static are fine
        BGPRedistribution.objects.create(address_family=self.af, protocol='connected')
        with self.assertRaises(ValidationError):
            self._redistribution(protocol='connected').full_clean()


class BGPRedistributionAPITestCase(
    LeanCoreTestsMixin, APIViewTestCases.APIViewTestCase
):
    model = BGPRedistribution
    view_namespace = 'plugins-api:netbox_routing_protocols'
    brief_fields = ['address_family', 'display', 'id', 'protocol', 'url']

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='RIR')
        asn = ASN.objects.create(rir=rir, asn=64512)
        device = create_test_device(name='Device')
        instance = _instance(device, asn)
        af = BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv4-unicast'
        )
        af_v6 = BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv6-unicast'
        )
        cls.ospf = OSPFInstance.objects.create(
            name='OSPF', device=device, router_id='1.1.1.1'
        )
        cls.model.objects.bulk_create(
            [
                cls.model(address_family=af, protocol='connected'),
                cls.model(address_family=af, protocol='static'),
                cls.model(address_family=af_v6, protocol='connected'),
            ]
        )
        cls.create_data = [
            {
                'address_family': af.pk,
                'protocol': 'ospf',
                'ospf_source': cls.ospf.pk,
                'metric': 10,
            },
            {'address_family': af_v6.pk, 'protocol': 'static', 'metric': 20},
        ]
        cls.bulk_update_data = {'description': 'Description'}


class BGPRedistributionViewTestCase(
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
    model = BGPRedistribution

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='RIR')
        asn = ASN.objects.create(rir=rir, asn=64512)
        device = create_test_device(name='Device')
        instance = _instance(device, asn)
        af = BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv4-unicast'
        )
        af_v6 = BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv6-unicast'
        )
        cls.ospf = OSPFInstance.objects.create(
            name='OSPF', device=device, router_id='1.1.1.1'
        )
        cls.model.objects.bulk_create(
            [
                cls.model(address_family=af, protocol='connected'),
                cls.model(address_family=af, protocol='static'),
                cls.model(address_family=af_v6, protocol='connected'),
            ]
        )
        cls.form_data = {
            'address_family': af.pk,
            'protocol': 'ospf',
            'ospf_source': cls.ospf.pk,
            'ospf_match': ['internal'],
            'metric': 10,
        }
        cls.bulk_edit_data = {'metric': 30}
