from django.urls import path, include

from utilities.urls import get_model_urls

from . import views  # noqa F401
from .views.community import CommunityMatchView
from .views.objects import ASPathMatchView, PrefixMatchView, RoutePolicyMatchView

app_name = 'netbox_routing_protocols'

urlpatterns = [
    # Tools
    path('tools/prefix-match/', PrefixMatchView.as_view(), name='prefix_match'),
    path('tools/as-path-match/', ASPathMatchView.as_view(), name='aspath_match'),
    path(
        'tools/route-policy-match/',
        RoutePolicyMatchView.as_view(),
        name='routepolicy_match',
    ),
    path(
        'tools/community-match/',
        CommunityMatchView.as_view(),
        name='community_match',
    ),
    path(
        'routes/static/', include(get_model_urls(app_name, 'staticroute', detail=False))
    ),
    path('routes/static/<int:pk>/', include(get_model_urls(app_name, 'staticroute'))),
    # OSPF
    path(
        'ospf/instance/',
        include(get_model_urls(app_name, 'ospfinstance', detail=False)),
    ),
    path('ospf/instance/<int:pk>/', include(get_model_urls(app_name, 'ospfinstance'))),
    path('ospf/area/', include(get_model_urls(app_name, 'ospfarea', detail=False))),
    path('ospf/area/<int:pk>/', include(get_model_urls(app_name, 'ospfarea'))),
    path(
        'ospf/interface/',
        include(get_model_urls(app_name, 'ospfinterface', detail=False)),
    ),
    path(
        'ospf/interface/<int:pk>/', include(get_model_urls(app_name, 'ospfinterface'))
    ),
    path(
        'ospf/network/',
        include(get_model_urls(app_name, 'ospfnetwork', detail=False)),
    ),
    path('ospf/network/<int:pk>/', include(get_model_urls(app_name, 'ospfnetwork'))),
    path(
        'ospf/redistribution/',
        include(get_model_urls(app_name, 'ospfredistribution', detail=False)),
    ),
    path(
        'ospf/redistribution/<int:pk>/',
        include(get_model_urls(app_name, 'ospfredistribution')),
    ),
    path(
        'ospf/virtual-link/',
        include(get_model_urls(app_name, 'ospfvirtuallink', detail=False)),
    ),
    path(
        'ospf/virtual-link/<int:pk>/',
        include(get_model_urls(app_name, 'ospfvirtuallink')),
    ),
    path(
        'ospf/summary-address/',
        include(get_model_urls(app_name, 'ospfsummaryaddress', detail=False)),
    ),
    path(
        'ospf/summary-address/<int:pk>/',
        include(get_model_urls(app_name, 'ospfsummaryaddress')),
    ),
    path(
        'ospf/neighbor/',
        include(get_model_urls(app_name, 'ospfneighbor', detail=False)),
    ),
    path('ospf/neighbor/<int:pk>/', include(get_model_urls(app_name, 'ospfneighbor'))),
    path(
        'ospf/authentication-key/',
        include(get_model_urls(app_name, 'ospfauthenticationkey', detail=False)),
    ),
    path(
        'ospf/authentication-key/<int:pk>/',
        include(get_model_urls(app_name, 'ospfauthenticationkey')),
    ),
    path(
        'ospf/area-range/',
        include(get_model_urls(app_name, 'ospfarearange', detail=False)),
    ),
    path(
        'ospf/area-range/<int:pk>/', include(get_model_urls(app_name, 'ospfarearange'))
    ),
    path(
        'ospf/prefix-sid/',
        include(get_model_urls(app_name, 'ospfprefixsid', detail=False)),
    ),
    path(
        'ospf/prefix-sid/<int:pk>/', include(get_model_urls(app_name, 'ospfprefixsid'))
    ),
    # IS-IS
    path(
        'isis/setting/',
        include(get_model_urls(app_name, 'isissetting', detail=False)),
    ),
    path('isis/setting/<int:pk>/', include(get_model_urls(app_name, 'isissetting'))),
    path('isis/level/', include(get_model_urls(app_name, 'isislevel', detail=False))),
    path('isis/level/<int:pk>/', include(get_model_urls(app_name, 'isislevel'))),
    path(
        'isis/interface-level/',
        include(get_model_urls(app_name, 'isisinterfacelevel', detail=False)),
    ),
    path(
        'isis/interface-level/<int:pk>/',
        include(get_model_urls(app_name, 'isisinterfacelevel')),
    ),
    path(
        'isis/segment-routing/',
        include(get_model_urls(app_name, 'isissegmentrouting', detail=False)),
    ),
    path(
        'isis/segment-routing/<int:pk>/',
        include(get_model_urls(app_name, 'isissegmentrouting')),
    ),
    path(
        'isis/flex-algo/',
        include(get_model_urls(app_name, 'isisflexalgo', detail=False)),
    ),
    path('isis/flex-algo/<int:pk>/', include(get_model_urls(app_name, 'isisflexalgo'))),
    path(
        'isis/address-family/',
        include(get_model_urls(app_name, 'isisaddressfamily', detail=False)),
    ),
    path(
        'isis/address-family/<int:pk>/',
        include(get_model_urls(app_name, 'isisaddressfamily')),
    ),
    path(
        'isis/sr-mapping-entry/',
        include(get_model_urls(app_name, 'isissrmappingentry', detail=False)),
    ),
    path(
        'isis/sr-mapping-entry/<int:pk>/',
        include(get_model_urls(app_name, 'isissrmappingentry')),
    ),
    path(
        'isis/adjacency-sid/',
        include(get_model_urls(app_name, 'isisadjacencysid', detail=False)),
    ),
    path(
        'isis/adjacency-sid/<int:pk>/',
        include(get_model_urls(app_name, 'isisadjacencysid')),
    ),
    path(
        'isis/area-address/',
        include(get_model_urls(app_name, 'isisareaaddress', detail=False)),
    ),
    path(
        'isis/area-address/<int:pk>/',
        include(get_model_urls(app_name, 'isisareaaddress')),
    ),
    path(
        'isis/redistribution/',
        include(get_model_urls(app_name, 'isisredistribution', detail=False)),
    ),
    path(
        'isis/redistribution/<int:pk>/',
        include(get_model_urls(app_name, 'isisredistribution')),
    ),
    path(
        'isis/summary-address/',
        include(get_model_urls(app_name, 'isissummaryaddress', detail=False)),
    ),
    path(
        'isis/summary-address/<int:pk>/',
        include(get_model_urls(app_name, 'isissummaryaddress')),
    ),
    path(
        'isis/route-leak/',
        include(get_model_urls(app_name, 'isisrouteleak', detail=False)),
    ),
    path(
        'isis/route-leak/<int:pk>/', include(get_model_urls(app_name, 'isisrouteleak'))
    ),
    path(
        'isis/prefix-sid/',
        include(get_model_urls(app_name, 'isisprefixsid', detail=False)),
    ),
    path(
        'isis/prefix-sid/<int:pk>/', include(get_model_urls(app_name, 'isisprefixsid'))
    ),
    path(
        'isis/srv6-locator/',
        include(get_model_urls(app_name, 'isissrv6locator', detail=False)),
    ),
    path(
        'isis/srv6-locator/<int:pk>/',
        include(get_model_urls(app_name, 'isissrv6locator')),
    ),
    path(
        'isis/instance/',
        include(get_model_urls(app_name, 'isisinstance', detail=False)),
    ),
    path('isis/instance/<int:pk>/', include(get_model_urls(app_name, 'isisinstance'))),
    path(
        'isis/interface/',
        include(get_model_urls(app_name, 'isisinterface', detail=False)),
    ),
    path(
        'isis/interface/<int:pk>/', include(get_model_urls(app_name, 'isisinterface'))
    ),
    # EIGRP
    path(
        'eigrp/router/', include(get_model_urls(app_name, 'eigrprouter', detail=False))
    ),
    path('eigrp/router/<int:pk>/', include(get_model_urls(app_name, 'eigrprouter'))),
    path(
        'eigrp/address-family/',
        include(get_model_urls(app_name, 'eigrpaddressfamily', detail=False)),
    ),
    path(
        'eigrp/address-family/<int:pk>/',
        include(get_model_urls(app_name, 'eigrpaddressfamily')),
    ),
    path(
        'eigrp/network/',
        include(get_model_urls(app_name, 'eigrpnetwork', detail=False)),
    ),
    path('eigrp/network/<int:pk>/', include(get_model_urls(app_name, 'eigrpnetwork'))),
    path(
        'eigrp/interface/',
        include(get_model_urls(app_name, 'eigrpinterface', detail=False)),
    ),
    path(
        'eigrp/interface/<int:pk>/', include(get_model_urls(app_name, 'eigrpinterface'))
    ),
    # BFD
    path('bfd/profile/', include(get_model_urls(app_name, 'bfdprofile', detail=False))),
    path('bfd/profile/<int:pk>/', include(get_model_urls(app_name, 'bfdprofile'))),
    # BGP
    path(
        'bgp/instance/', include(get_model_urls(app_name, 'bgpinstance', detail=False))
    ),
    path('bgp/instance/<int:pk>/', include(get_model_urls(app_name, 'bgpinstance'))),
    path(
        'bgp/peer-group/',
        include(get_model_urls(app_name, 'bgppeergroup', detail=False)),
    ),
    path('bgp/peer-group/<int:pk>/', include(get_model_urls(app_name, 'bgppeergroup'))),
    path(
        'bgp/redistribution/',
        include(get_model_urls(app_name, 'bgpredistribution', detail=False)),
    ),
    path(
        'bgp/redistribution/<int:pk>/',
        include(get_model_urls(app_name, 'bgpredistribution')),
    ),
    path(
        'bgp/listen-range/',
        include(get_model_urls(app_name, 'bgplistenrange', detail=False)),
    ),
    path(
        'bgp/listen-range/<int:pk>/',
        include(get_model_urls(app_name, 'bgplistenrange')),
    ),
    path(
        'bgp/address-family/',
        include(get_model_urls(app_name, 'bgpaddressfamily', detail=False)),
    ),
    path(
        'bgp/address-family/<int:pk>/',
        include(get_model_urls(app_name, 'bgpaddressfamily')),
    ),
    path('bgp/peer/', include(get_model_urls(app_name, 'bgppeer', detail=False))),
    path('bgp/peer/<int:pk>/', include(get_model_urls(app_name, 'bgppeer'))),
    path(
        'bgp/peer-address-family/',
        include(get_model_urls(app_name, 'bgppeeraddressfamily', detail=False)),
    ),
    path(
        'bgp/peer-address-family/<int:pk>/',
        include(get_model_urls(app_name, 'bgppeeraddressfamily')),
    ),
    # Objects: Community
    path(
        'objects/community-list/',
        include(get_model_urls(app_name, 'communitylist', detail=False)),
    ),
    path(
        'objects/community-list/<int:pk>/',
        include(get_model_urls(app_name, 'communitylist')),
    ),
    path(
        'objects/community/',
        include(get_model_urls(app_name, 'community', detail=False)),
    ),
    path('objects/community/<int:pk>/', include(get_model_urls(app_name, 'community'))),
    path(
        'objects/community-list-entry/',
        include(get_model_urls(app_name, 'communitylistentry', detail=False)),
    ),
    path(
        'objects/community-list-entry/<int:pk>/',
        include(get_model_urls(app_name, 'communitylistentry')),
    ),
    # Objects: Prefix List
    path(
        'objects/prefix-list/',
        include(get_model_urls(app_name, 'prefixlist', detail=False)),
    ),
    path(
        'objects/prefix-list/<int:pk>/', include(get_model_urls(app_name, 'prefixlist'))
    ),
    path(
        'objects/prefix-list-entry/',
        include(get_model_urls(app_name, 'prefixlistentry', detail=False)),
    ),
    path(
        'objects/prefix-list-entry/<int:pk>/',
        include(get_model_urls(app_name, 'prefixlistentry')),
    ),
    # Objects: Route Policy
    path(
        'objects/route-policy/',
        include(get_model_urls(app_name, 'routepolicy', detail=False)),
    ),
    path(
        'objects/route-policy/<int:pk>/',
        include(get_model_urls(app_name, 'routepolicy')),
    ),
    path(
        'objects/route-policy-entry/',
        include(get_model_urls(app_name, 'routepolicyentry', detail=False)),
    ),
    path(
        'objects/route-policy-entry/<int:pk>/',
        include(get_model_urls(app_name, 'routepolicyentry')),
    ),
    # Objects: AS Path
    path(
        'objects/as-path/',
        include(get_model_urls(app_name, 'aspath', detail=False)),
    ),
    path('objects/as-path/<int:pk>/', include(get_model_urls(app_name, 'aspath'))),
    path(
        'objects/as-path-entry/',
        include(get_model_urls(app_name, 'aspathentry', detail=False)),
    ),
    path(
        'objects/as-path-entry/<int:pk>/',
        include(get_model_urls(app_name, 'aspathentry')),
    ),
]
