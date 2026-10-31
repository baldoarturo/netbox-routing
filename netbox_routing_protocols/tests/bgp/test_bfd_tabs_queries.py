from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from netaddr import IPNetwork

from ipam.models import IPAddress

from netbox_routing_protocols.models import BFDProfile, BGPPeer, BGPPeerGroup
from netbox_routing_protocols.tables import BGPPeerGroupTable, BGPPeerTable
from netbox_routing_protocols.tests.bgp.base import BGPInstanceMixin
from netbox_routing_protocols.views.bgp import (
    BFDProfilePeerGroupsView,
    BFDProfilePeersView,
)

__all__ = ('BFDProfileTabsQueriesTestCase',)


class BFDProfileTabsQueriesTestCase(BGPInstanceMixin, TestCase):
    """The peer and peer group tabs of a BFD profile load the related objects of their
    rows once, not once per row"""

    def _add_peer(self, profile, group, index):
        address = IPAddress.objects.create(address=IPNetwork(f'10.2.0.{index}/24'))
        BGPPeer.objects.create(
            instance=self.bgp_instance,
            peer=address,
            peer_group=group,
            remote_as=self.asns[1],
            bfd=profile,
        )

    def _queries(self, table):
        with CaptureQueriesContext(connection) as context:
            for row in table.rows:
                for column in table.columns:
                    row.get_cell(column.name)
        return len(context.captured_queries)

    def test_peer_tab_queries_do_not_grow_with_the_rows(self):
        profile = BFDProfile.objects.create(
            name='BFD', min_tx_int=300, min_rx_int=300, multiplier=3
        )
        group = BGPPeerGroup.objects.create(
            name='G', instance=self.bgp_instance, remote_as=self.asns[1]
        )
        self._add_peer(profile, group, 1)
        view = BFDProfilePeersView()
        few = self._queries(BGPPeerTable(view.get_children(None, profile)))
        for index in range(2, 6):
            self._add_peer(profile, group, index)
        many = self._queries(BGPPeerTable(view.get_children(None, profile)))
        self.assertEqual(few, many)

    def test_peer_group_tab_queries_do_not_grow_with_the_rows(self):
        profile = BFDProfile.objects.create(
            name='BFD', min_tx_int=300, min_rx_int=300, multiplier=3
        )
        view = BFDProfilePeerGroupsView()

        def add_group(index):
            BGPPeerGroup.objects.create(
                name=f'G{index}',
                instance=self.bgp_instance,
                remote_as=self.asns[1],
                bfd=profile,
            )

        add_group(1)
        few = self._queries(BGPPeerGroupTable(view.get_children(None, profile)))
        for index in range(2, 6):
            add_group(index)
        many = self._queries(BGPPeerGroupTable(view.get_children(None, profile)))
        self.assertEqual(few, many)
