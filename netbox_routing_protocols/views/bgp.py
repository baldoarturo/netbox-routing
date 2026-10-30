from django.utils.translation import gettext_lazy as _

from extras.ui.panels import TagsPanel
from netbox.object_actions import CloneObject, EditObject, DeleteObject
from netbox.views.generic import (
    BulkImportView,
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
    'BGPInstanceBulkImportView',
    'BGPAddressFamilyBulkImportView',
    'BGPPeerGroupBulkImportView',
    'BGPListenRangeBulkImportView',
    'BGPPeerBulkImportView',
    'BGPPeerAddressFamilyBulkImportView',
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
    'BGPListenRangeListView',
    'BGPListenRangeView',
    'BGPListenRangeEditView',
    'BGPListenRangeDeleteView',
    'BGPListenRangeBulkEditView',
    'BGPListenRangeBulkDeleteView',
    'BGPRedistributionListView',
    'BGPRedistributionView',
    'BGPRedistributionEditView',
    'BGPRedistributionDeleteView',
    'BGPRedistributionBulkEditView',
    'BGPRedistributionBulkDeleteView',
    'BGPAddressFamilyRedistributionsView',
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
    queryset = BGPInstance.objects.select_related(
        'device',
        'vrf',
        'asn',
        'confederation_identifier',
        'import_policy',
        'export_policy',
        'tenant',
    ).prefetch_related('confederation_peers')
    filterset = BGPInstanceFilterSet
    filterset_form = BGPInstanceFilterForm
    table = BGPInstanceTable


@register_model_view(BGPInstance)
class BGPInstanceView(ObjectView):
    queryset = BGPInstance.objects.select_related(
        'device',
        'vrf',
        'asn',
        'confederation_identifier',
        'import_policy',
        'export_policy',
        'tenant',
    ).prefetch_related('confederation_peers')
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPInstancePanel(),
            BGPInstanceRoutingPanel(title=_('Route reflector and confederation')),
            BGPInstanceVRFPanel(title=_('VRF')),
            BGPGracefulRestartPanel(title=_('Graceful restart')),
            BGPRoutePolicyPanel(title=_('Route policy')),
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
    queryset = BGPInstance.objects.select_related(
        'device',
        'vrf',
        'asn',
        'confederation_identifier',
        'import_policy',
        'export_policy',
        'tenant',
    ).prefetch_related('confederation_peers')
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPNoPolicyPanel(title=_('No explicit policy')),
            BGPPeerGroupPanel(),
            BGPPeerSessionPanel(title=_('Session')),
            BGPRoutePolicyPanel(title=_('Route policy')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )

    def get_extra_context(self, request, instance):
        return {'sessions_without_policy': instance.sessions_without_policy()}


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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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


@register_model_view(BGPPeerGroup, name='listen_ranges')
class BGPPeerGroupListenRangesView(ObjectChildrenView):
    queryset = BGPPeerGroup.objects.select_related(
        'instance__device', 'instance__vrf', 'instance__asn'
    )
    child_model = BGPListenRange
    table = BGPListenRangeTable
    filterset = BGPListenRangeFilterSet
    filterset_form = BGPListenRangeFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Listen Ranges',
        badge=lambda obj: BGPListenRange.objects.filter(peer_group=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(peer_group=parent)


#
# BGPListenRange
#
@register_model_view(BGPListenRange, name='list', path='', detail=False)
class BGPListenRangeListView(ObjectListView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )
    filterset = BGPListenRangeFilterSet
    filterset_form = BGPListenRangeFilterForm
    table = BGPListenRangeTable


@register_model_view(BGPListenRange)
class BGPListenRangeView(ObjectView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPListenRangePanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPListenRange, name='add', detail=False)
@register_model_view(BGPListenRange, name='edit')
class BGPListenRangeEditView(ObjectEditView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )
    form = BGPListenRangeForm


@register_model_view(BGPListenRange, name='delete')
class BGPListenRangeDeleteView(ObjectDeleteView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )


@register_model_view(BGPListenRange, name='bulk_edit', detail=False)
class BGPListenRangeBulkEditView(BulkEditView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )
    filterset = BGPListenRangeFilterSet
    form = BGPListenRangeBulkEditForm
    table = BGPListenRangeTable


@register_model_view(BGPListenRange, name='bulk_delete', detail=False)
class BGPListenRangeBulkDeleteView(BulkDeleteView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device',
        'peer_group__instance__vrf',
        'peer_group__instance__asn',
        'prefix',
    )
    filterset = BGPListenRangeFilterSet
    table = BGPListenRangeTable


#
# BGPRedistribution
#
@register_model_view(BGPRedistribution, name='list', path='', detail=False)
class BGPRedistributionListView(ObjectListView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    filterset = BGPRedistributionFilterSet
    filterset_form = BGPRedistributionFilterForm
    table = BGPRedistributionTable


@register_model_view(BGPRedistribution)
class BGPRedistributionView(ObjectView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPRedistributionPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(BGPRedistribution, name='add', detail=False)
@register_model_view(BGPRedistribution, name='edit')
class BGPRedistributionEditView(ObjectEditView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    form = BGPRedistributionForm


@register_model_view(BGPRedistribution, name='delete')
class BGPRedistributionDeleteView(ObjectDeleteView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )


@register_model_view(BGPRedistribution, name='bulk_edit', detail=False)
class BGPRedistributionBulkEditView(BulkEditView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    filterset = BGPRedistributionFilterSet
    form = BGPRedistributionBulkEditForm
    table = BGPRedistributionTable


@register_model_view(BGPRedistribution, name='bulk_delete', detail=False)
class BGPRedistributionBulkDeleteView(BulkDeleteView):
    queryset = BGPRedistribution.objects.select_related(
        'address_family__instance__device',
        'address_family__instance__vrf',
        'address_family__instance__asn',
        'ospf_source__device',
        'isis_source__device',
        'eigrp_source__router__device',
        'eigrp_source__vrf',
        'route_policy',
        'tenant',
    )
    filterset = BGPRedistributionFilterSet
    table = BGPRedistributionTable


@register_model_view(BGPAddressFamily, name='redistributions')
class BGPAddressFamilyRedistributionsView(ObjectChildrenView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__asn'
    )
    child_model = BGPRedistribution
    table = BGPRedistributionTable
    filterset = BGPRedistributionFilterSet
    filterset_form = BGPRedistributionFilterForm
    actions = (CloneObject, EditObject, DeleteObject)
    tab = ViewTab(
        label='Redistribution',
        badge=lambda obj: BGPRedistribution.objects.filter(address_family=obj).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(address_family=parent)


#
# Bulk import (CSV)
#
@register_model_view(BGPInstance, name='bulk_import', detail=False)
class BGPInstanceBulkImportView(BulkImportView):
    queryset = BGPInstance.objects.select_related(
        'device', 'vrf', 'asn', 'import_policy', 'export_policy'
    )
    model_form = BGPInstanceImportForm


@register_model_view(BGPAddressFamily, name='bulk_import', detail=False)
class BGPAddressFamilyBulkImportView(BulkImportView):
    queryset = BGPAddressFamily.objects.select_related(
        'instance__device', 'instance__vrf'
    )
    model_form = BGPAddressFamilyImportForm


@register_model_view(BGPPeerGroup, name='bulk_import', detail=False)
class BGPPeerGroupBulkImportView(BulkImportView):
    queryset = BGPPeerGroup.objects.select_related('instance__device', 'instance__vrf')
    model_form = BGPPeerGroupImportForm


@register_model_view(BGPListenRange, name='bulk_import', detail=False)
class BGPListenRangeBulkImportView(BulkImportView):
    queryset = BGPListenRange.objects.select_related(
        'peer_group__instance__device', 'peer_group__instance__vrf'
    )
    model_form = BGPListenRangeImportForm


@register_model_view(BGPPeer, name='bulk_import', detail=False)
class BGPPeerBulkImportView(BulkImportView):
    queryset = BGPPeer.objects.select_related('instance__device', 'instance__vrf')
    model_form = BGPPeerImportForm


@register_model_view(BGPPeerAddressFamily, name='bulk_import', detail=False)
class BGPPeerAddressFamilyBulkImportView(BulkImportView):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'peer__instance__device', 'peer_group__instance__device'
    )
    model_form = BGPPeerAddressFamilyImportForm


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
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
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
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPNoPolicyPanel(title=_('No explicit policy')),
            BGPPeerPanel(),
            BGPPeerSessionPanel(title=_('Session')),
            BGPRoutePolicyPanel(title=_('Route policy')),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )

    def get_extra_context(self, request, instance):
        return {'sessions_without_policy': instance.sessions_without_policy()}


@register_model_view(BGPPeer, name='add', detail=False)
@register_model_view(BGPPeer, name='edit')
class BGPPeerEditView(ObjectEditView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
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
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
        'tenant',
    )


@register_model_view(BGPPeer, name='bulk_edit', detail=False)
class BGPPeerBulkEditView(BulkEditView):
    queryset = BGPPeer.objects.select_related(
        'instance__device',
        'instance__vrf',
        'instance__asn',
        'peer',
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
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
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
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
        'interface__device',
        'source',
        'peer_group',
        'remote_as',
        'local_as',
        'bfd',
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
        'tenant',
    )
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            BGPPeerAddressFamilyPanel(),
            BGPEffectivePolicyPanel(title=_('Effective route policy')),
            BGPPolicyFilteringPanel(title=_('Filtering')),
            BGPPeerAddressFamilyOptionsPanel(title=_('Options')),
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
        'import_policy',
        'export_policy',
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
