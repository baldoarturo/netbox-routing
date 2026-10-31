from django.core.exceptions import ValidationError
from django.test import TestCase
from netaddr import IPNetwork

from ipam.models import IPAddress
from netbox_routing_plugin.models import BGPPeer, BGPPeerGroup
from netbox_routing_plugin.tests.bgp.base import BGPInstanceMixin

__all__ = ('BGPNeighborOptionsTestCase',)


class BGPNeighborOptionsTestCase(BGPInstanceMixin, TestCase):
    """AS override (eBGP only), soft reconfiguration inbound and graceful shutdown
    (RFC 8326) on a peer and a peer group; a peer inherits them from its group"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = BGPPeerGroup.objects.create(
            name='Group',
            instance=cls.bgp_instance,
            remote_as=cls.asns[1],
            soft_reconfiguration_inbound=True,
        )

    def _peer(self, **kwargs):
        kwargs.setdefault('instance', self.bgp_instance)
        kwargs.setdefault(
            'peer', IPAddress.objects.create(address=IPNetwork('10.7.7.7/24'))
        )
        kwargs.setdefault('remote_as', self.asns[1])
        return BGPPeer(**kwargs)

    def test_as_override_only_for_ebgp(self):
        self._peer(as_override=True).full_clean()
        with self.assertRaises(ValidationError) as cm:
            self._peer(as_override=True, remote_as=self.asn).full_clean()
        self.assertIn('as_override', cm.exception.error_dict)
        group = BGPPeerGroup(
            name='iBGP',
            instance=self.bgp_instance,
            remote_as=self.asn,
            as_override=True,
        )
        with self.assertRaises(ValidationError) as cm:
            group.full_clean()
        self.assertIn('as_override', cm.exception.error_dict)

    def test_a_peer_inherits_the_options_of_its_group(self):
        peer = self._peer(peer_group=self.group)
        self.assertTrue(peer.effective('soft_reconfiguration_inbound'))
        self.assertIsNone(peer.effective('graceful_shutdown'))
        peer.soft_reconfiguration_inbound = False
        self.assertFalse(peer.effective('soft_reconfiguration_inbound'))

    def test_graceful_shutdown_is_a_flag(self):
        peer = self._peer(graceful_shutdown=True)
        peer.full_clean()
        self.assertTrue(peer.graceful_shutdown)
