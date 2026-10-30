from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from dcim.api.serializers_.devices import DeviceSerializer
from dcim.api.serializers_.device_components import InterfaceSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from netbox.api.fields import ChoiceField
from netbox.api.serializers import NetBoxModelSerializer

from netbox_routing_protocols.api.field_serializers import IPAddressField
from netbox_routing_protocols.choices import StaticRouteNextHopTypeChoices
from netbox_routing_protocols.models import StaticRoute

__all__ = ('StaticRouteSerializer',)


class StaticRouteSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing_protocols-api:staticroute-detail'
    )
    devices = DeviceSerializer(many=True, nested=True, required=False, allow_null=True)
    vrf = VRFSerializer(nested=True, required=False, allow_null=True)
    next_hop = IPAddressField(required=False, allow_null=True)
    interface = InterfaceSerializer(nested=True, required=False, allow_null=True)
    next_hop_type = ChoiceField(choices=StaticRouteNextHopTypeChoices, required=False)
    next_hop_vrf = VRFSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = StaticRoute
        fields = (
            'url',
            'id',
            'display',
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'interface',
            'next_hop_type',
            'next_hop_vrf',
            'next_hop_global',
            'name',
            'distance',
            'tag',
            'permanent',
            'description',
            'comments',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
            'prefix',
            'next_hop',
            'description',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        current = instance or StaticRoute()  # defaults for the omitted fields
        route = StaticRoute(
            pk=instance.pk if instance else None,
            **{
                field: attrs.get(field, getattr(current, field))
                for field in (
                    'vrf',
                    'prefix',
                    'next_hop',
                    'interface',
                    'next_hop_type',
                    'next_hop_vrf',
                    'next_hop_global',
                )
            },
        )
        if 'devices' in attrs:
            devices = attrs['devices'] or []
        else:
            devices = instance.devices.all() if instance else []
        try:
            route.validate_devices(devices)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs

    def create(self, validated_data):
        devices = validated_data.pop('devices', None)
        instance = super().create(validated_data)

        return self._update_devices(instance, devices)

    def update(self, instance, validated_data):
        devices = validated_data.pop('devices', None)
        instance = super().update(instance, validated_data)

        return self._update_devices(instance, devices)

    def _update_devices(self, instance: StaticRoute, devices: object) -> StaticRoute:
        if devices:
            instance.devices.set(devices)
        elif devices is not None:
            instance.devices.clear()

        return instance
