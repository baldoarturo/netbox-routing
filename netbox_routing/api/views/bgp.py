from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing import filtersets
from netbox_routing.api._serializers.bgp import *
from netbox_routing.models.bgp import *

__all__ = (
    'BGPRouterViewSet',
    'BGPScopeViewSet',
    'BGPAddressFamilyViewSet',
    'BGPSettingViewSet',
    'BGPPeerViewSet',
    'BGPPeerAddressFamilyViewSet',
    'BGPPeerTemplateViewSet',
    'BGPPolicyTemplateViewSet',
    'BGPSessionTemplateViewSet',
    'BFDProfileViewSet',
)


class BGPSettingViewSet(NetBoxModelViewSet):
    queryset = BGPSetting.objects.all()
    serializer_class = BGPSettingSerializer
    filterset_class = filtersets.BGPSettingFilterSet


class BGPRouterViewSet(NetBoxModelViewSet):
    queryset = BGPRouter.objects.select_related('asn', 'tenant')
    serializer_class = BGPRouterSerializer
    filterset_class = filtersets.BGPRouterFilterSet


class BGPScopeViewSet(NetBoxModelViewSet):
    queryset = BGPScope.objects.select_related('router__asn', 'vrf', 'tenant')
    serializer_class = BGPScopeSerializer
    filterset_class = filtersets.BGPScopeFilterSet


class BGPAddressFamilyViewSet(NetBoxModelViewSet):
    queryset = BGPAddressFamily.objects.select_related(
        'scope__router__asn', 'scope__vrf', 'tenant'
    )
    serializer_class = BGPAddressFamilySerializer
    filterset_class = filtersets.BGPAddressFamilyFilterSet


class BGPPeerViewSet(NetBoxModelViewSet):
    queryset = BGPPeer.objects.select_related(
        'scope__router__asn',
        'peer',
        'source',
        'peer_group',
        'peer_session',
        'remote_as',
        'local_as',
        'bfd',
        'tenant',
    )
    serializer_class = BGPPeerSerializer
    filterset_class = filtersets.BGPPeerFilterSet


class BGPPeerTemplateViewSet(NetBoxModelViewSet):
    queryset = BGPPeerTemplate.objects.select_related('remote_as', 'tenant')
    serializer_class = BGPPeerTemplateSerializer
    filterset_class = filtersets.BGPPeerTemplateFilterSet


class BGPPolicyTemplateViewSet(NetBoxModelViewSet):
    queryset = BGPPolicyTemplate.objects.select_related(
        'prefixlist_out', 'prefixlist_in', 'routemap_out', 'routemap_in', 'tenant'
    )
    serializer_class = BGPPolicyTemplateSerializer
    filterset_class = filtersets.BGPPolicyTemplateFilterSet


class BGPSessionTemplateViewSet(NetBoxModelViewSet):
    queryset = BGPSessionTemplate.objects.select_related(
        'parent', 'local_as', 'remote_as', 'bfd', 'tenant'
    )
    serializer_class = BGPSessionTemplateSerializer
    filterset_class = filtersets.BGPSessionTemplateFilterSet


class BGPPeerAddressFamilyViewSet(NetBoxModelViewSet):
    queryset = BGPPeerAddressFamily.objects.select_related(
        'address_family__scope__router__asn',
        'peer_policy',
        'prefixlist_out',
        'prefixlist_in',
        'routemap_out',
        'routemap_in',
        'tenant',
    )
    serializer_class = BGPPeerAddressFamilySerializer
    filterset_class = filtersets.BGPPeerAddressFamilyFilterSet


class BFDProfileViewSet(NetBoxModelViewSet):
    queryset = BFDProfile.objects.select_related('tenant')
    serializer_class = BFDProfileSerializer
    filterset_class = filtersets.BFDProfileFilterSet
