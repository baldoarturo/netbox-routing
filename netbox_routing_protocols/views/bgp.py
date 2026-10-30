from django.utils.translation import gettext_lazy as _

from extras.ui.panels import TagsPanel
from netbox.object_actions import CloneObject, EditObject, DeleteObject
from netbox.views.generic import (
    ObjectView,
    ObjectEditView,
    ObjectListView,
    ObjectDeleteView,
    ObjectChildrenView,
    BulkEditView,
    BulkDeleteView,
)
from netbox.ui import panels, layout
from netbox_routing_protocols.ui import *

from utilities.views import register_model_view, ViewTab

from netbox_routing_protocols.filtersets.bgp import *
from netbox_routing_protocols.forms.bgp import *
from netbox_routing_protocols.models.bgp import *
from netbox_routing_protocols.tables.bgp import *

__all__ = (
    'BGPInstanceListView',
    'BGPInstanceView',
    'BGPInstanceEditView',
    'BGPInstanceDeleteView',
    'BGPInstanceBulkEditView',
    'BGPInstanceBulkDeleteView',
    'BGPAddressFamilyListView',
    'BGPAddressFamilyView',
    'BGPAddressFamilyEditView',
    'BGPAddressFamilyDeleteView',
    'BGPAddressFamilyBulkEditView',
    'BGPAddressFamilyBulkDeleteView',
    'BGPPeerGroupListView',
    'BGPPeerGroupView',
    'BGPPeerGroupEditView',
    'BGPPeerGroupDeleteView',
    'BGPPeerGroupBulkEditView',
    'BGPPeerGroupBulkDeleteView',
    'BGPPeerListView',
    'BGPPeerView',
    'BGPPeerEditView',
    'BGPPeerDeleteView',
    'BGPPeerBulkEditView',
    'BGPPeerBulkDeleteView',
    'BGPPeerAddressFamilyListView',
    'BGPPeerAddressFamilyView',
    'BGPPeerAddressFamilyEditView',
    'BGPPeerAddressFamilyDeleteView',
    'BGPPeerAddressFamilyBulkEditView',
    'BGPPeerAddressFamilyBulkDeleteView',
    'BFDProfileListView',
    'BFDProfileView',
    'BFDProfileEditView',
    'BFDProfileDeleteView',
    'BFDProfileBulkEditView',
    'BFDProfileBulkDeleteView',
    'BFDProfilePeersView',
    'BFDProfilePeerGroupsView',
)


#
# BGPInstance
#
@register_model_view(BGPInstance, name='list', path='', detail=False)
class BGPInstanceListView(ObjectListView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    filterset = BGPInstanceFilterSet
    filterset_form = BGPInstanceFilterForm
    table = BGPInstanceTable


@register_model_view(BGPInstance)
class BGPInstanceView(ObjectView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPInstancePanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPInstance, name='add', detail=False)
@register_model_view(BGPInstance, name='edit')
class BGPInstanceEditView(ObjectEditView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    form = BGPInstanceForm


@register_model_view(BGPInstance, name='delete')
class BGPInstanceDeleteView(ObjectDeleteView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')


@register_model_view(BGPInstance, name='bulk_edit', detail=False)
class BGPInstanceBulkEditView(BulkEditView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    filterset = BGPInstanceFilterSet
    form = BGPInstanceBulkEditForm
    table = BGPInstanceTable


@register_model_view(BGPInstance, name='bulk_delete', detail=False)
class BGPInstanceBulkDeleteView(BulkDeleteView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    filterset = BGPInstanceFilterSet
    table = BGPInstanceTable


@register_model_view(BGPInstance, name='address_families')
class BGPInstanceAddressFamilysView(ObjectChildrenView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    child_model = BGPAddressFamily
    table = BGPAddressFamilyTable
    filterset = BGPAddressFamilyFilterSet
    filterset_form = BGPAddressFamilyFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Address Families',
        badge=lambda obj: BGPAddressFamily.objects.filter(instance=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent)


@register_model_view(BGPInstance, name='peer_groups')
class BGPInstancePeerGroupsView(ObjectChildrenView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    child_model = BGPPeerGroup
    table = BGPPeerGroupTable
    filterset = BGPPeerGroupFilterSet
    filterset_form = BGPPeerGroupFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Peer Groups',
        badge=lambda obj: BGPPeerGroup.objects.filter(instance=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent)


@register_model_view(BGPInstance, name='peers')
class BGPInstancePeersView(ObjectChildrenView):
    queryset = BGPInstance.objects.select_related('device', 'vrf', 'asn', 'tenant')
    child_model = BGPPeer
    table = BGPPeerTable
    filterset = BGPPeerFilterSet
    filterset_form = BGPPeerFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Peers',
        badge=lambda obj: BGPPeer.objects.filter(instance=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(instance=parent)


#
# BGPAddressFamily
#
@register_model_view(BGPAddressFamily, name='list', path='', detail=False)
class BGPAddressFamilyListView(ObjectListView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    filterset = BGPAddressFamilyFilterSet
    filterset_form = BGPAddressFamilyFilterForm
    table = BGPAddressFamilyTable


@register_model_view(BGPAddressFamily)
class BGPAddressFamilyView(ObjectView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPAddressFamilyPanel(),
            BGPAddressFamilyOptionsPanel(title=_('Options')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPAddressFamily, name='add', detail=False)
@register_model_view(BGPAddressFamily, name='edit')
class BGPAddressFamilyEditView(ObjectEditView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    form = BGPAddressFamilyForm


@register_model_view(BGPAddressFamily, name='delete')
class BGPAddressFamilyDeleteView(ObjectDeleteView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )


@register_model_view(BGPAddressFamily, name='bulk_edit', detail=False)
class BGPAddressFamilyBulkEditView(BulkEditView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    filterset = BGPAddressFamilyFilterSet
    form = BGPAddressFamilyBulkEditForm
    table = BGPAddressFamilyTable


@register_model_view(BGPAddressFamily, name='bulk_delete', detail=False)
class BGPAddressFamilyBulkDeleteView(BulkDeleteView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    filterset = BGPAddressFamilyFilterSet
    table = BGPAddressFamilyTable


@register_model_view(BGPAddressFamily, name='peer_address_families')
class BGPAddressFamilyPeerAddressFamilysView(ObjectChildrenView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn', 'tenant'
    )
    child_model = BGPPeerAddressFamily
    table = BGPPeerAddressFamilyTable
    filterset = BGPPeerAddressFamilyFilterSet
    filterset_form = BGPPeerAddressFamilyFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Peer Address Families',
        badge=lambda obj: BGPPeerAddressFamily.objects.filter(
            address_family=obj
        ).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(address_family=parent)


#
# BGPPeerGroup
#
@register_model_view(BGPPeerGroup, name='list', path='', detail=False)
class BGPPeerGroupListView(ObjectListView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerGroupFilterSet
    filterset_form = BGPPeerGroupFilterForm
    table = BGPPeerGroupTable


@register_model_view(BGPPeerGroup)
class BGPPeerGroupView(ObjectView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPPeerGroupPanel(),
            BGPPeerSessionPanel(title=_('Session')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPPeerGroup, name='add', detail=False)
@register_model_view(BGPPeerGroup, name='edit')
class BGPPeerGroupEditView(ObjectEditView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    form = BGPPeerGroupForm


@register_model_view(BGPPeerGroup, name='delete')
class BGPPeerGroupDeleteView(ObjectDeleteView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )


@register_model_view(BGPPeerGroup, name='bulk_edit', detail=False)
class BGPPeerGroupBulkEditView(BulkEditView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerGroupFilterSet
    form = BGPPeerGroupBulkEditForm
    table = BGPPeerGroupTable


@register_model_view(BGPPeerGroup, name='bulk_delete', detail=False)
class BGPPeerGroupBulkDeleteView(BulkDeleteView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerGroupFilterSet
    table = BGPPeerGroupTable


@register_model_view(BGPPeerGroup, name='peers')
class BGPPeerGroupPeersView(ObjectChildrenView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    child_model = BGPPeer
    table = BGPPeerTable
    filterset = BGPPeerFilterSet
    filterset_form = BGPPeerFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Peers',
        badge=lambda obj: BGPPeer.objects.filter(peer_group=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(peer_group=parent)


@register_model_view(BGPPeerGroup, name='address_families')
class BGPPeerGroupPeerAddressFamilysView(ObjectChildrenView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    child_model = BGPPeerAddressFamily
    table = BGPPeerAddressFamilyTable
    filterset = BGPPeerAddressFamilyFilterSet
    filterset_form = BGPPeerAddressFamilyFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Address Families',
        badge=lambda obj: BGPPeerAddressFamily.objects.filter(peer_group=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(peer_group=parent)


#
# BGPPeer
#
@register_model_view(BGPPeer, name='list', path='', detail=False)
class BGPPeerListView(ObjectListView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerFilterSet
    filterset_form = BGPPeerFilterForm
    table = BGPPeerTable


@register_model_view(BGPPeer)
class BGPPeerView(ObjectView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPPeerPanel(),
            BGPPeerSessionPanel(title=_('Session')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPPeer, name='add', detail=False)
@register_model_view(BGPPeer, name='edit')
class BGPPeerEditView(ObjectEditView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    form = BGPPeerForm


@register_model_view(BGPPeer, name='delete')
class BGPPeerDeleteView(ObjectDeleteView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )


@register_model_view(BGPPeer, name='bulk_edit', detail=False)
class BGPPeerBulkEditView(BulkEditView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerFilterSet
    form = BGPPeerBulkEditForm
    table = BGPPeerTable


@register_model_view(BGPPeer, name='bulk_delete', detail=False)
class BGPPeerBulkDeleteView(BulkDeleteView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    filterset = BGPPeerFilterSet
    table = BGPPeerTable


@register_model_view(BGPPeer, name='address_families')
class BGPPeerPeerAddressFamilysView(ObjectChildrenView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    child_model = BGPPeerAddressFamily
    table = BGPPeerAddressFamilyTable
    filterset = BGPPeerAddressFamilyFilterSet
    filterset_form = BGPPeerAddressFamilyFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Address Families',
        badge=lambda obj: BGPPeerAddressFamily.objects.filter(peer=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(peer=parent)


#
# BGPPeerAddressFamily
#
@register_model_view(BGPPeerAddressFamily, name='list', path='', detail=False)
class BGPPeerAddressFamilyListView(ObjectListView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )
    filterset = BGPPeerAddressFamilyFilterSet
    filterset_form = BGPPeerAddressFamilyFilterForm
    table = BGPPeerAddressFamilyTable


@register_model_view(BGPPeerAddressFamily)
class BGPPeerAddressFamilyView(ObjectView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPPeerAddressFamilyPanel(),
            BGPPolicyFilteringPanel(title=_('Filtering')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPPeerAddressFamily, name='add', detail=False)
@register_model_view(BGPPeerAddressFamily, name='edit')
class BGPPeerAddressFamilyEditView(ObjectEditView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )
    form = BGPPeerAddressFamilyForm


@register_model_view(BGPPeerAddressFamily, name='delete')
class BGPPeerAddressFamilyDeleteView(ObjectDeleteView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )


@register_model_view(BGPPeerAddressFamily, name='bulk_edit', detail=False)
class BGPPeerAddressFamilyBulkEditView(BulkEditView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )
    filterset = BGPPeerAddressFamilyFilterSet
    form = BGPPeerAddressFamilyBulkEditForm
    table = BGPPeerAddressFamilyTable


@register_model_view(BGPPeerAddressFamily, name='bulk_delete', detail=False)
class BGPPeerAddressFamilyBulkDeleteView(BulkDeleteView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance',
        'peer__peer',
        'peer_group__instance',
        'address_family__instance',
        'prefixlist_in',
        'prefixlist_out',
        'routepolicy_in',
        'routepolicy_out',
        'tenant',
    )
    filterset = BGPPeerAddressFamilyFilterSet
    table = BGPPeerAddressFamilyTable


#
# BFD Profile
#
@register_model_view(BFDProfile, name='list', path='', detail=False)
class BFDProfileListView(ObjectListView):
    queryset = BFDProfile.objects.select_related('tenant')
    filterset = BFDProfileFilterSet
    filterset_form = BFDProfileFilterForm
    table = BFDProfileTable


@register_model_view(BFDProfile)
class BFDProfileView(ObjectView):
    queryset = BFDProfile.objects.select_related('tenant')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BFDProfilePanel(),
            BFDProfileSessionPanel(title=_('Session Parameters')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BFDProfile, name='add', detail=False)
@register_model_view(BFDProfile, name='edit')
class BFDProfileEditView(ObjectEditView):
    queryset = BFDProfile.objects.select_related('tenant')
    form = BFDProfileForm


@register_model_view(BFDProfile, name='delete')
class BFDProfileDeleteView(ObjectDeleteView):
    queryset = BFDProfile.objects.select_related('tenant')


@register_model_view(BFDProfile, name='bulk_edit', detail=False)
class BFDProfileBulkEditView(BulkEditView):
    queryset = BFDProfile.objects.select_related('tenant')
    filterset = BFDProfileFilterSet
    form = BFDProfileBulkEditForm
    table = BFDProfileTable


@register_model_view(BFDProfile, name='bulk_delete', detail=False)
class BFDProfileBulkDeleteView(BulkDeleteView):
    queryset = BFDProfile.objects.select_related('tenant')
    filterset = BFDProfileFilterSet
    table = BFDProfileTable


@register_model_view(BFDProfile, name='peers')
class BFDProfilePeersView(ObjectChildrenView):
    queryset = BFDProfile.objects.select_related('tenant')
    child_model = BGPPeer
    table = BGPPeerTable
    filterset = BGPPeerFilterSet
    filterset_form = BGPPeerFilterForm
    actions = ObjectChildrenView.actions
    tab = ViewTab(
        label='BGP Peers',
        badge=lambda obj: BGPPeer.objects.filter(bfd=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(bfd=parent)


@register_model_view(BFDProfile, name='peer_groups')
class BFDProfilePeerGroupsView(ObjectChildrenView):
    queryset = BFDProfile.objects.select_related('tenant')
    child_model = BGPPeerGroup
    table = BGPPeerGroupTable
    filterset = BGPPeerGroupFilterSet
    filterset_form = BGPPeerGroupFilterForm
    actions = ObjectChildrenView.actions
    tab = ViewTab(
        label='BGP Peer Groups',
        badge=lambda obj: BGPPeerGroup.objects.filter(bfd=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(bfd=parent)
