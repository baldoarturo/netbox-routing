# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.prefetch import GenericPrefetch

from netbox.api.viewsets import NetBoxModelViewSet

from netbox_routing_protocols import filtersets
from netbox_routing_protocols.api.serializers import (
    ISISInstanceSerializer,
    ISISInterfaceSerializer,
    ISISSettingSerializer,
    ISISLevelSerializer,
    ISISInterfaceLevelSerializer,
    ISISSegmentRoutingSerializer,
    ISISFlexAlgoSerializer,
    ISISPrefixSIDSerializer,
    ISISSRv6LocatorSerializer,
    ISISSRMappingEntrySerializer,
    ISISAdjacencySIDSerializer,
    ISISAreaAddressSerializer,
    ISISRedistributionSerializer,
    ISISSummaryAddressSerializer,
    ISISRouteLeakSerializer,
)
from netbox_routing_protocols.models import (
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISSRMappingEntry,
    ISISAdjacencySID,
    ISISAreaAddress,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
)

__all__ = (
    'ISISInstanceViewSet',
    'ISISInterfaceViewSet',
    'ISISSettingViewSet',
    'ISISLevelViewSet',
    'ISISInterfaceLevelViewSet',
    'ISISSegmentRoutingViewSet',
    'ISISFlexAlgoViewSet',
    'ISISPrefixSIDViewSet',
    'ISISSRv6LocatorViewSet',
    'ISISSRMappingEntryViewSet',
    'ISISAdjacencySIDViewSet',
    'ISISAreaAddressViewSet',
    'ISISRedistributionViewSet',
    'ISISSummaryAddressViewSet',
    'ISISRouteLeakViewSet',
)


class ISISFlexAlgoViewSet(NetBoxModelViewSet):
    # display renders str(self) -> str(instance) -> instance.device, so pull the
    # whole chain in one join to keep the list view query count flat.
    queryset = ISISFlexAlgo.objects.select_related('instance__device')
    serializer_class = ISISFlexAlgoSerializer
    filterset_class = filtersets.ISISFlexAlgoFilterSet


class ISISPrefixSIDViewSet(NetBoxModelViewSet):
    # str(self) -> str(ISISInterface) -> ISISInterface.interface (dcim Interface)
    queryset = ISISPrefixSID.objects.select_related('interface__interface')
    serializer_class = ISISPrefixSIDSerializer
    filterset_class = filtersets.ISISPrefixSIDFilterSet


class ISISSRv6LocatorViewSet(NetBoxModelViewSet):
    # str(self) -> str(instance) -> instance.device
    queryset = ISISSRv6Locator.objects.select_related('instance__device')
    serializer_class = ISISSRv6LocatorSerializer
    filterset_class = filtersets.ISISSRv6LocatorFilterSet


class ISISSettingViewSet(NetBoxModelViewSet):
    # The serializer renders assigned_object (a GenericForeignKey); without a
    # GenericPrefetch each row would fetch its target separately (N+1).
    queryset = ISISSetting.objects.prefetch_related(
        GenericPrefetch(
            'assigned_object',
            [
                ISISInstance.objects.select_related(
                    'device', 'vrf', 'import_policy', 'export_policy'
                ),
                ISISInterface.objects.select_related(
                    'instance__device', 'instance__vrf', 'interface'
                ),
            ],
        )
    )
    serializer_class = ISISSettingSerializer
    filterset_class = filtersets.ISISSettingFilterSet


class ISISLevelViewSet(NetBoxModelViewSet):
    # str(self) -> str(instance) -> instance.device
    queryset = ISISLevel.objects.select_related('instance__device')
    serializer_class = ISISLevelSerializer
    filterset_class = filtersets.ISISLevelFilterSet


class ISISInterfaceLevelViewSet(NetBoxModelViewSet):
    # str(self) -> str(ISISInterface) -> ISISInterface.interface (dcim Interface)
    queryset = ISISInterfaceLevel.objects.select_related('interface__interface')
    serializer_class = ISISInterfaceLevelSerializer
    filterset_class = filtersets.ISISInterfaceLevelFilterSet


class ISISSegmentRoutingViewSet(NetBoxModelViewSet):
    # str(self) -> str(instance) -> instance.device
    queryset = ISISSegmentRouting.objects.select_related('instance__device')
    serializer_class = ISISSegmentRoutingSerializer
    filterset_class = filtersets.ISISSegmentRoutingFilterSet


class ISISInstanceViewSet(NetBoxModelViewSet):
    queryset = ISISInstance.objects.select_related(
        'device', 'vrf', 'import_policy', 'export_policy'
    )
    serializer_class = ISISInstanceSerializer
    filterset_class = filtersets.ISISInstanceFilterSet


class ISISInterfaceViewSet(NetBoxModelViewSet):
    queryset = ISISInterface.objects.select_related(
        'instance__device', 'instance__vrf', 'interface'
    )
    serializer_class = ISISInterfaceSerializer
    filterset_class = filtersets.ISISInterfaceFilterSet


class ISISRedistributionViewSet(NetBoxModelViewSet):
    queryset = ISISRedistribution.objects.select_related(
        'instance__device',
        'instance__vrf',
        'ospf_source__device',
        'eigrp_source__device',
        'bgp_source__asn',
        'isis_source__device',
    ).prefetch_related('bgp_source__assigned_object')
    serializer_class = ISISRedistributionSerializer
    filterset_class = filtersets.ISISRedistributionFilterSet


class ISISSummaryAddressViewSet(NetBoxModelViewSet):
    queryset = ISISSummaryAddress.objects.select_related(
        'instance__device', 'instance__vrf'
    )
    serializer_class = ISISSummaryAddressSerializer
    filterset_class = filtersets.ISISSummaryAddressFilterSet


class ISISRouteLeakViewSet(NetBoxModelViewSet):
    queryset = ISISRouteLeak.objects.select_related('instance__device', 'instance__vrf')
    serializer_class = ISISRouteLeakSerializer
    filterset_class = filtersets.ISISRouteLeakFilterSet


class ISISAreaAddressViewSet(NetBoxModelViewSet):
    queryset = ISISAreaAddress.objects.select_related('instance__device')
    serializer_class = ISISAreaAddressSerializer
    filterset_class = filtersets.ISISAreaAddressFilterSet


class ISISSRMappingEntryViewSet(NetBoxModelViewSet):
    queryset = ISISSRMappingEntry.objects.select_related('instance__device')
    serializer_class = ISISSRMappingEntrySerializer
    filterset_class = filtersets.ISISSRMappingEntryFilterSet


class ISISAdjacencySIDViewSet(NetBoxModelViewSet):
    queryset = ISISAdjacencySID.objects.select_related('interface__interface')
    serializer_class = ISISAdjacencySIDSerializer
    filterset_class = filtersets.ISISAdjacencySIDFilterSet
