from ipam.models import ASN, IPAddress, Prefix, RIR, VRF
from django.test import TestCase
from netaddr import IPNetwork
from utilities.testing import ViewTestCases, create_test_device

from netbox_routing_protocols.models.bgp import *
from netbox_routing_protocols.tests.base import (
    BulkEditMixin,
    LeanCoreTestsMixin,
    PluginBaseURLMixin,
)

__all__ = (
    'BGPInstanceTestCase',
    'BGPAddressFamilyTestCase',
    'BGPPeerGroupTestCase',
    'BGPListenRangeTestCase',
    'BGPPeerTestCase',
    'BGPPeerAddressFamilyTestCase',
    'BFDProfileTestCase',
)


VIEW_CASES = (
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
)


class _ViewHelpers:
    @classmethod
    def _parents(cls):
        rir = RIR.objects.create(name='ARIN')
        asns = [ASN.objects.create(rir=rir, asn=64512 + i) for i in range(4)]
        instance = BGPInstance.objects.create(
            name='Instance', device=create_test_device(name='Device'), asn=asns[0]
        )
        cls.asns = asns
        return asns, instance


class BGPInstanceTestCase(_ViewHelpers, *VIEW_CASES):
    model = BGPInstance

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='ARIN')
        asn = ASN.objects.create(rir=rir, asn=64512)
        devices = [create_test_device(name=f'Device {i}') for i in range(1, 5)]
        vrf = VRF.objects.create(name='Test VRF')
        cls.model.objects.bulk_create(
            [
                cls.model(name=f'Instance {i}', device=devices[i], asn=asn)
                for i in range(3)
            ]
        )
        cls.form_data = {
            'name': 'Instance X',
            'device': devices[3].pk,
            'vrf': vrf.pk,
            'asn': asn.pk,
            'router_id': '192.0.2.1',
            'asdot': True,
            'graceful_restart': True,
            'graceful_restart_time': 120,
            'graceful_restart_stale_time': 360,
        }


class BGPAddressFamilyTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BGPAddressFamily

    @classmethod
    def setUpTestData(cls):
        _asns, instance = cls._parents()
        cls.model.objects.bulk_create(
            [
                cls.model(instance=instance, address_family=af)
                for af in ('ipv4-unicast', 'ipv6-unicast', 'vpnv4-unicast')
            ]
        )
        cls.form_data = {
            'instance': instance.pk,
            'address_family': 'l2vpn-evpn',
            'maximum_paths': 4,
            'distance_ebgp': 20,
            'additional_paths_send': True,
        }


class BGPPeerGroupTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BGPPeerGroup

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        cls.model.objects.bulk_create(
            [cls.model(name=f'Group {i}', instance=instance) for i in range(3)]
        )
        cls.form_data = {
            'name': 'Group X',
            'instance': instance.pk,
            'remote_as': asns[1].pk,
            'hold_time': 90,
            'keepalive': 30,
            'ebgp_multihop': 2,
            'passive': True,
        }


class BGPListenRangeTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BGPListenRange

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asns[1]
        )
        prefixes = [Prefix.objects.create(prefix=f'10.{i}.0.0/24') for i in range(1, 5)]
        cls.model.objects.bulk_create(
            [cls.model(peer_group=group, prefix=prefixes[i]) for i in range(3)]
        )
        cls.form_data = {'peer_group': group.pk, 'prefix': prefixes[3].pk}


class BGPPeerTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BGPPeer

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        addresses = [
            IPAddress.objects.create(address=IPNetwork(f'10.0.0.{i}/24'))
            for i in range(1, 6)
        ]
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asns[1]
        )
        cls.model.objects.bulk_create(
            [
                cls.model(instance=instance, peer=addresses[i], remote_as=asns[1])
                for i in range(3)
            ]
        )
        cls.form_data = {
            'instance': instance.pk,
            'peer': addresses[3].pk,
            'peer_group': group.pk,
            'status': 'planned',
            'enabled': True,
        }


class BGPPeerAddressFamilyTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BGPPeerAddressFamily

    @classmethod
    def setUpTestData(cls):
        asns, instance = cls._parents()
        afs = [
            BGPAddressFamily.objects.create(instance=instance, address_family=af)
            for af in ('ipv4-unicast', 'ipv6-unicast', 'vpnv4-unicast', 'l2vpn-evpn')
        ]
        peer = BGPPeer.objects.create(
            instance=instance,
            peer=IPAddress.objects.create(address=IPNetwork('10.0.0.1/24')),
            remote_as=asns[1],
        )
        cls.model.objects.bulk_create(
            [cls.model(peer=peer, address_family=afs[i]) for i in range(3)]
        )
        cls.form_data = {
            'peer': peer.pk,
            'address_family': afs[3].pk,
            'enabled': True,
            'send_community': ['standard', 'large'],
            'next_hop_self': True,
            'maximum_prefix': 100,
            'maximum_prefix_action': 'stop',
        }


class BFDProfileTestCase(LeanCoreTestsMixin, _ViewHelpers, *VIEW_CASES):
    model = BFDProfile

    @classmethod
    def setUpTestData(cls):
        cls.model.objects.bulk_create(
            [
                cls.model(
                    name=f'Test BFD Profile {i}',
                    min_rx_int=60,
                    min_tx_int=60,
                    multiplier=3,
                )
                for i in range(1, 4)
            ]
        )
        cls.form_data = {
            'name': f'{cls.model._meta.verbose_name} 5',
            'min_rx_int': 60,
            'min_tx_int': 60,
            'multiplier': 3,
        }


class BGPInstanceDeleteConfirmationTestCase(TestCase):
    """The delete page of an instance shows what goes with it (#523)"""

    @classmethod
    def setUpTestData(cls):
        rir = RIR.objects.create(name='ARIN')
        asn = ASN.objects.create(rir=rir, asn=64512)
        instance = BGPInstance.objects.create(
            name='Instance', device=create_test_device(name='Device'), asn=asn
        )
        af = BGPAddressFamily.objects.create(
            instance=instance, address_family='ipv4-unicast'
        )
        group = BGPPeerGroup.objects.create(
            name='Group', instance=instance, remote_as=asn
        )
        peer = BGPPeer.objects.create(
            instance=instance,
            peer=IPAddress.objects.create(address=IPNetwork('10.0.0.1/24')),
            peer_group=group,
        )
        BGPPeerAddressFamily.objects.create(peer=peer, address_family=af)
        cls.instance = instance

    def test_the_page_lists_the_children_that_will_be_deleted(self):
        from users.models import User

        user = User.objects.create(username='admin', is_superuser=True)
        self.client.force_login(user)
        response = self.client.get(self.instance.get_absolute_url() + 'delete/')
        self.assertEqual(response.status_code, 200)
        dependent = response.context['dependent_objects']
        names = {model._meta.model_name for model in dependent}
        self.assertTrue(
            {'bgpaddressfamily', 'bgppeergroup', 'bgppeer', 'bgppeeraddressfamily'}
            <= names,
            names,
        )
        self.assertContains(response, 'Group')
