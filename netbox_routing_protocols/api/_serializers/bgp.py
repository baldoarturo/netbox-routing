from rest_framework import serializers

from dcim.api.serializers_.devices import DeviceSerializer
from ipam.api.serializers_.asns import ASNSerializer
from ipam.api.serializers_.ip import IPAddressSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from netbox.api.serializers import NetBoxModelSerializer
from tenancy.api.serializers_.tenants import TenantSerializer

from netbox_routing_protocols.api._serializers.objects import (
    PrefixListSerializer,
    RoutePolicySerializer,
)
from netbox_routing_protocols.models.bgp import *

__all__ = (
    'BGPInstanceSerializer',
    'BGPAddressFamilySerializer',
    'BGPPeerGroupSerializer',
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
    'ttl',
    'password',
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
            'graceful_restart',
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'name', 'device', 'vrf', 'asn')


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
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BGPPeerGroup
        fields = (
            'url',
            'id',
            'display',
            'name',
            'instance',
            *_SESSION,
            'tenant',
            *_COMMON,
        )
        brief_fields = ('url', 'id', 'display', 'name', 'instance')


class BGPPeerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:bgppeer-detail'
    )
    instance = BGPInstanceSerializer(nested=True)
    peer = IPAddressSerializer(nested=True)
    source = IPAddressSerializer(nested=True, required=False, allow_null=True)
    peer_group = BGPPeerGroupSerializer(nested=True, required=False, allow_null=True)
    remote_as = ASNSerializer(nested=True, required=False, allow_null=True)
    local_as = ASNSerializer(nested=True, required=False, allow_null=True)
    bfd = serializers.PrimaryKeyRelatedField(
        queryset=BFDProfile.objects.all(), required=False, allow_null=True
    )
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
    routepolicy_in = RoutePolicySerializer(nested=True, required=False, allow_null=True)
    routepolicy_out = RoutePolicySerializer(
        nested=True, required=False, allow_null=True
    )
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
            'routepolicy_in',
            'routepolicy_out',
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
