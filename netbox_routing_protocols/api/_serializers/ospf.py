from rest_framework import serializers

from dcim.api.serializers_.device_components import InterfaceSerializer
from dcim.api.serializers_.devices import DeviceSerializer
from ipam.api.serializers_.ip import IPAddressSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from netbox.api.serializers import NetBoxModelSerializer
from netbox_routing_protocols.api._serializers.bgp import BGPRouterSerializer
from netbox_routing_protocols.api._serializers.eigrp import EIGRPRouterSerializer
from netbox_routing_protocols.api._serializers.isis import ISISInstanceSerializer
from netbox_routing_protocols.models import (
    OSPFAuthenticationMixin,
    OSPFInstance,
    OSPFArea,
    OSPFInterface,
    OSPFNetwork,
    OSPFRedistribution,
    OSPFVirtualLink,
    OSPFSummaryAddress,
    OSPFNeighbor,
    OSPFAreaRange,
    OSPFPrefixSID,
)

__all__ = (
    'OSPFInstanceSerializer',
    'OSPFAreaSerializer',
    'OSPFInterfaceSerializer',
    'OSPFNetworkSerializer',
    'OSPFRedistributionSerializer',
    'OSPFVirtualLinkSerializer',
    'OSPFSummaryAddressSerializer',
    'OSPFNeighborSerializer',
    'OSPFAreaRangeSerializer',
    'OSPFPrefixSIDSerializer',
)


class OSPFInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfinstance-detail'
    )
    device = DeviceSerializer(nested=True)
    vrf = VRFSerializer(nested=True, required=False, allow_null=True)
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )

    class Meta:
        model = OSPFInstance
        fields = (
            'url',
            'id',
            'display',
            'name',
            'router_id',
            'device',
            'vrf',
            'default_originate',
            'default_originate_always',
            'default_originate_metric',
            'default_originate_metric_type',
            *OSPFInstance.ADVANCED_FIELDS,
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            'passphrase_md5',
            'description',
            'comments',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
            'router_id',
            'device',
            'vrf',
        )


class OSPFAreaSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfarea-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )

    class Meta:
        model = OSPFArea
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'area_id',
            'area_type',
            'default_cost',
            'nssa_translate_always',
            'nssa_no_redistribution',
            'nssa_default_originate',
            'traffic_engineering',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            'passphrase_md5',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'instance',
            'area_id',
            'area_type',
        )


class OSPFInterfaceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfinterface-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)
    area = OSPFAreaSerializer(nested=True)
    interface = InterfaceSerializer(nested=True)
    mtu = serializers.IntegerField(source='interface.mtu', read_only=True)
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )
    effective_authentication = serializers.CharField(read_only=True, allow_null=True)
    authentication_source = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = OSPFInterface
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'area',
            'interface',
            'network_type',
            'passive',
            'priority',
            'bfd',
            'cost',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'ttl_security',
            'ttl_security_hops',
            'mtu',
            'mtu_ignore',
            'adjacency_sid',
            'te_metric',
            'te_max_reservable_bandwidth',
            'te_admin_group',
            'prefix_suppression',
            'database_filter_all_out',
            'flood_reduction',
            'demand_circuit',
            'authentication',
            'passphrase',
            'authentication_key_id',
            'message_digest_algorithm',
            'key_chain',
            'show_md5',
            'passphrase_md5',
            'effective_authentication',
            'authentication_source',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'instance',
            'area',
            'interface',
            'network_type',
            'passive',
        )


class OSPFNetworkSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfnetwork-detail'
    )
    ospf_interface = OSPFInterfaceSerializer(nested=True)
    ip_address = IPAddressSerializer(nested=True)
    subnet = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OSPFNetwork
        fields = (
            'url',
            'id',
            'display',
            'ospf_interface',
            'ip_address',
            'subnet',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'ospf_interface',
            'ip_address',
        )

    def get_subnet(self, obj):
        return str(obj.subnet)


class OSPFRedistributionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfredistribution-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)
    ospf_source = OSPFInstanceSerializer(nested=True, required=False, allow_null=True)
    eigrp_source = EIGRPRouterSerializer(nested=True, required=False, allow_null=True)
    bgp_source = BGPRouterSerializer(nested=True, required=False, allow_null=True)
    isis_source = ISISInstanceSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = OSPFRedistribution
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'protocol',
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            'ospf_match',
            'metric',
            'metric_type',
            'subnets',
            'route_tag',
            'route_policy',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'instance',
            'protocol',
        )


class OSPFVirtualLinkSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfvirtuallink-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)
    transit_area = OSPFAreaSerializer(nested=True)
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )
    effective_authentication = serializers.CharField(read_only=True, allow_null=True)
    authentication_source = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = OSPFVirtualLink
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'transit_area',
            'remote_router_id',
            'hello_interval',
            'dead_interval',
            'retransmit_interval',
            'transmit_delay',
            'ttl_security',
            'ttl_security_hops',
            *OSPFAuthenticationMixin.AUTHENTICATION_FIELDS,
            'passphrase_md5',
            'effective_authentication',
            'authentication_source',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'instance',
            'transit_area',
            'remote_router_id',
        )


class OSPFSummaryAddressSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfsummaryaddress-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)

    class Meta:
        model = OSPFSummaryAddress
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'prefix',
            'not_advertise',
            'route_tag',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'prefix')


class OSPFNeighborSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfneighbor-detail'
    )
    ospf_interface = OSPFInterfaceSerializer(nested=True)

    class Meta:
        model = OSPFNeighbor
        fields = (
            'url',
            'id',
            'display',
            'ospf_interface',
            'ip_address',
            'priority',
            'poll_interval',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'ospf_interface', 'ip_address')


class OSPFAreaRangeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfarearange-detail'
    )
    area = OSPFAreaSerializer(nested=True)

    class Meta:
        model = OSPFAreaRange
        fields = (
            'url',
            'id',
            'display',
            'area',
            'prefix',
            'range_type',
            'advertise',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'area', 'prefix')


class OSPFPrefixSIDSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:ospfprefixsid-detail'
    )
    instance = OSPFInstanceSerializer(nested=True)

    class Meta:
        model = OSPFPrefixSID
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'prefix',
            'sid_type',
            'sid',
            'algorithm',
            'node_sid',
            'no_php',
            'explicit_null',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'prefix', 'sid')
