from rest_framework import serializers

from dcim.api.serializers_.devices import DeviceSerializer
from ipam.api.serializers_.asns import ASNSerializer
from dcim.api.serializers_.device_components import InterfaceSerializer
from ipam.api.serializers_.ip import IPAddressSerializer, PrefixSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from ipam.models import ASN
from netbox.api.fields import SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer

from netbox_routing_protocols.api._serializers.objects import (
    PrefixListSerializer,
    RoutePolicySerializer,
)
from netbox_routing_protocols.models import EIGRPRouter, ISISInstance, OSPFInstance
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceSerializer',
    'BGPAddressFamilySerializer',
    'BGPPeerGroupSerializer',
    'BGPListenRangeSerializer',
    'BGPRedistributionSerializer',
    'BGPPeerSerializer',
    'BGPPeerAddressFamilySerializer',
    'BFDProfileSerializer',
)

_COMMON = (
    'description',
    'comments',
    'tags',
    'custom_fields',
    'created',
    'last_updated',
)
_SESSION = (
    'remote_as',
    'local_as',
    'enabled',
    'bfd',
    'ebgp_multihop',
    'ttl_security_hops',
    'passive',
    'as_override',
    'soft_reconfiguration_inbound',
    'graceful_shutdown',
    'import_policy',
    'export_policy',
    'passphrase',
    'passphrase_md5',
    'show_md5',
    'route_reflector_client',
    'extended_nexthop',
    'keepalive',
    'hold_time',
)


class BGPInstanceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgpinstance-detail'
    )
    device = DeviceSerializer(nested=True)
    vrf = VRFSerializer(nested=True, required=False, allow_null=True)
    asn = ASNSerializer(nested=True)
    confederation_identifier = ASNSerializer(
        nested=True, required=False, allow_null=True
    )
    confederation_peers = SerializedPKRelatedField(
        queryset=ASN.objects.all(),
        serializer=ASNSerializer,
        nested=True,
        required=False,
        many=True,
    )
    import_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    export_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPInstance
        fields = (
            'url',
            'id',
            'display',
            'name',
            'device',
            'vrf',
            'asn',
            'router_id',
            'asdot',
            'cluster_id',
            'confederation_identifier',
            'confederation_peers',
            'graceful_restart',
            'graceful_restart_time',
            'graceful_restart_stale_time',
            'graceful_restart_helper_only',
            'import_policy',
            'export_policy',
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'name', 'device', 'vrf', 'asn')

    def validate(self, data):
        data = super().validate(data)
        instance = self.instance
        peers = data.get(
            'confederation_peers',
            instance.confederation_peers.all() if instance else [],
        )
        errors = BGPInstance.confederation_errors(
            data.get('asn', instance.asn if instance else None),
            data.get(
                'confederation_identifier',
                instance.confederation_identifier if instance else None,
            ),
            peers,
        )
        if errors:
            raise serializers.ValidationError(errors)
        return data


class BGPAddressFamilySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgpaddressfamily-detail'
    )
    instance = BGPInstanceSerializer(nested=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPAddressFamily
        fields = (
            'url',
            'id',
            'display',
            'instance',
            'address_family',
            'maximum_paths',
            'default_metric',
            'default_originate',
            'auto_summary',
            'distance_ebgp',
            'distance_ibgp',
            'additional_paths_send',
            'additional_paths_receive',
            'additional_paths_install',
            'long_lived_stale_time',
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'instance', 'address_family')


class BGPPeerGroupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgppeergroup-detail'
    )
    instance = BGPInstanceSerializer(nested=True)
    remote_as = ASNSerializer(nested=True, required=False, allow_null=True)
    local_as = ASNSerializer(nested=True, required=False, allow_null=True)
    bfd = serializers.PrimaryKeyRelatedField(
        queryset=BFDProfile.objects.all(), required=False, allow_null=True
    )
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )
    import_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    export_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPPeerGroup
        fields = (
            'url',
            'id',
            'display',
            'name',
            'instance',
            'listen_limit',
            *_SESSION,
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'name', 'instance')


class BGPListenRangeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgplistenrange-detail'
    )
    peer_group = BGPPeerGroupSerializer(nested=True)
    prefix = PrefixSerializer(nested=True)

    class Meta:
        model = BGPListenRange
        fields = ('url', 'id', 'display', 'peer_group', 'prefix', *_COMMON)
        brief_fields = ('url', 'id', 'display', 'peer_group', 'prefix')


class BGPRedistributionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgpredistribution-detail'
    )
    address_family = BGPAddressFamilySerializer(nested=True)
    # the sources are the OSPF, IS-IS and EIGRP serializers' modules, which import this one
    ospf_source = serializers.PrimaryKeyRelatedField(
        queryset=OSPFInstance.objects.all(), required=False, allow_null=True
    )
    isis_source = serializers.PrimaryKeyRelatedField(
        queryset=ISISInstance.objects.all(), required=False, allow_null=True
    )
    eigrp_source = serializers.PrimaryKeyRelatedField(
        queryset=EIGRPRouter.objects.all(), required=False, allow_null=True
    )
    route_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPRedistribution
        fields = (
            'url',
            'id',
            'display',
            'address_family',
            'protocol',
            'ospf_source',
            'isis_source',
            'eigrp_source',
            'metric',
            'route_policy',
            'ospf_match',
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'address_family', 'protocol')


class BGPPeerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgppeer-detail'
    )
    instance = BGPInstanceSerializer(nested=True)
    peer = IPAddressSerializer(nested=True, required=False, allow_null=True)
    interface = InterfaceSerializer(nested=True, required=False, allow_null=True)
    source = IPAddressSerializer(nested=True, required=False, allow_null=True)
    peer_group = BGPPeerGroupSerializer(nested=True, required=False, allow_null=True)
    remote_as = ASNSerializer(nested=True, required=False, allow_null=True)
    local_as = ASNSerializer(nested=True, required=False, allow_null=True)
    bfd = serializers.PrimaryKeyRelatedField(
        queryset=BFDProfile.objects.all(), required=False, allow_null=True
    )
    passphrase_md5 = serializers.CharField(
        source='md5_digest', read_only=True, allow_null=True
    )
    import_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    export_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPPeer
        fields = (
            'url',
            'id',
            'display',
            'name',
            'instance',
            'peer',
            'interface',
            'source',
            'peer_group',
            'status',
            *_SESSION,
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'name', 'instance', 'peer')


class BGPPeerAddressFamilySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgppeeraddressfamily-detail'
    )
    peer = BGPPeerSerializer(nested=True, required=False, allow_null=True)
    peer_group = BGPPeerGroupSerializer(nested=True, required=False, allow_null=True)
    address_family = BGPAddressFamilySerializer(nested=True)
    prefixlist_in = PrefixListSerializer(nested=True, required=False, allow_null=True)
    prefixlist_out = PrefixListSerializer(nested=True, required=False, allow_null=True)
    import_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    export_policy = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPPeerAddressFamily
        fields = (
            'url',
            'id',
            'display',
            'peer',
            'peer_group',
            'address_family',
            'enabled',
            'prefixlist_in',
            'prefixlist_out',
            'import_policy',
            'export_policy',
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            'maximum_prefix',
            'maximum_prefix_warning',
            'maximum_prefix_action',
            'maximum_prefix_restart',
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'peer', 'peer_group', 'address_family')


class BFDProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bfdprofile-detail'
    )
    tenant = TenantSerializer(nested=True, required=False)

    class Meta:
        model = BFDProfile
        fields = (
            'url',
            'id',
            'display',
            'description',
            'comments',
            'name',
            'min_rx_int',
            'min_tx_int',
            'multiplier',
            'hold',
            'tenant',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
        )
