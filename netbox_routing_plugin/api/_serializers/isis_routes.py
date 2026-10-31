from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer
from netbox_routing_plugin.api._serializers.bgp import BGPInstanceSerializer
from netbox_routing_plugin.api._serializers.eigrp import EIGRPRouterSerializer
from netbox_routing_plugin.api._serializers.isis import ISISInstanceSerializer
from netbox_routing_plugin.api._serializers.ospf import OSPFInstanceSerializer
from netbox_routing_plugin.models import (
    ISISRedistribution,
    ISISRouteLeak,
    ISISSummaryAddress,
)

__all__ = (
    'ISISRedistributionSerializer',
    'ISISSummaryAddressSerializer',
    'ISISRouteLeakSerializer',
)


class ISISRedistributionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisredistribution-detail'
    )
    instance = ISISInstanceSerializer(nested=True)
    ospf_source = OSPFInstanceSerializer(nested=True, required=False, allow_null=True)
    eigrp_source = EIGRPRouterSerializer(nested=True, required=False, allow_null=True)
    bgp_source = BGPInstanceSerializer(nested=True, required=False, allow_null=True)
    isis_source = ISISInstanceSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = ISISRedistribution
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'address_family',
            'protocol',
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            'level',
            'metric',
            'metric_type',
            'route_tag',
            'route_policy',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'protocol')


class ISISSummaryAddressSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isissummaryaddress-detail'
    )
    instance = ISISInstanceSerializer(nested=True)

    class Meta:
        model = ISISSummaryAddress
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'prefix',
            'level',
            'not_advertise',
            'metric',
            'route_tag',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'prefix')


class ISISRouteLeakSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_plugin-api:isisrouteleak-detail'
    )
    instance = ISISInstanceSerializer(nested=True)

    class Meta:
        model = ISISRouteLeak
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'address_family',
            'route_policy',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'address_family')
