from django.test import TestCase
from django.urls import reverse
from netaddr import IPNetwork

from ipam.models import IPAddress
from utilities.testing import APITestCase, create_test_device

from netbox_routing_protocols.models import *
from netbox_routing_protocols.tests.bgp.base import BGPInstanceMixin

__all__ = ('BGPQueriesTestCase', 'BGPSessionsWithoutPolicyQueriesTestCase')


def _setup(cls, count):
    """An eBGP instance with `count` families, a policy at every level, a group, and
    `count` peers"""
    cls.policy = RoutePolicy.objects.create(name='P')
    cls.bgp_instance.import_policy = cls.policy
    cls.bgp_instance.save()
    afs = [
        BGPAddressFamily.objects.create(
            instance=cls.bgp_instance, address_family=family
        )
        for family in ('ipv4-unicast', 'ipv6-unicast', 'vpnv4-unicast', 'l2vpn-evpn')[
            :count
        ]
    ]
    group = BGPPeerGroup.objects.create(
        name='G',
        instance=cls.bgp_instance,
        remote_as=cls.asns[1],
        import_policy=cls.policy,
    )
    peers = []
    for i in range(count):
        address = IPAddress.objects.create(address=IPNetwork(f'10.1.0.{i + 1}/24'))
        peers.append(
            BGPPeer.objects.create(
                instance=cls.bgp_instance,
                peer=address,
                peer_group=group,
                import_policy=cls.policy,
                export_policy=cls.policy,
            )
        )
    for peer in peers:
        for af in afs:
            BGPPeerAddressFamily.objects.create(
                peer=peer, address_family=af, import_policy=cls.policy
            )
    return group, peers


class BGPSessionsWithoutPolicyQueriesTestCase(BGPInstanceMixin, TestCase):
    """The RFC 8212 check does not add queries for every address family"""

    def _queries(self, peer):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as context:
            peer.sessions_without_policy()
        return len(context)

    def test_the_queries_do_not_grow_with_the_families(self):
        group, peers = _setup(type(self), 4)
        peer = peers[0]
        peer.peer_group.address_families.all().delete()
        for af in BGPAddressFamily.objects.all():
            BGPPeerAddressFamily.objects.get_or_create(
                peer_group=group, address_family=af
            )
        four = self._queries(BGPPeer.objects.get(pk=peer.pk))
        BGPPeerAddressFamily.objects.filter(peer=peer).exclude(
            address_family__address_family='ipv4-unicast'
        ).delete()
        one = self._queries(BGPPeer.objects.get(pk=peer.pk))
        self.assertLessEqual(four, one + 2)


class BGPQueriesTestCase(BGPInstanceMixin, APITestCase):
    """The REST lists load the policies, the interface and the confederation once"""

    user_permissions = (
        'netbox_routing_protocols.view_bgpinstance',
        'netbox_routing_protocols.view_bgppeer',
        'netbox_routing_protocols.view_bgppeergroup',
    )

    def _count(self, name):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        url = reverse(f'plugins-api:netbox_routing_protocols-api:{name}-list')
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, 200)
        return len(context)

    def test_the_queries_do_not_grow_with_the_rows(self):
        self.add_permissions(*self.user_permissions)
        _setup(type(self), 1)
        small = {n: self._count(n) for n in ('bgppeer', 'bgppeergroup', 'bgpinstance')}
        for i in range(3):
            instance = BGPInstance.objects.create(
                name=f'I{i}',
                device=create_test_device(name=f'Dev {i}'),
                asn=self.asn,
                import_policy=self.policy,
                export_policy=self.policy,
                confederation_identifier=self.asns[2],
            )
            instance.confederation_peers.add(self.asns[3])
            group = BGPPeerGroup.objects.create(
                name='G',
                instance=instance,
                remote_as=self.asns[1],
                import_policy=self.policy,
            )
            BGPPeer.objects.create(
                instance=instance,
                peer=IPAddress.objects.create(address=IPNetwork(f'10.2.{i}.1/24')),
                peer_group=group,
                import_policy=self.policy,
                export_policy=self.policy,
            )
        for name, count in small.items():
            with self.subTest(name):
                self.assertLessEqual(self._count(name), count + 1)
