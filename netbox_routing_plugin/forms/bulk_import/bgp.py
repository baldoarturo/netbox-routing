from django import forms
from django.utils.translation import gettext_lazy as _
from netaddr import AddrFormatError, IPNetwork

from dcim.models import Device, Interface
from ipam.models import ASN, VRF, IPAddress, Prefix
from netbox.forms import NetBoxModelImportForm
from tenancy.models import Tenant
from utilities.forms.fields import CSVChoiceField, CSVModelChoiceField

from netbox_routing_plugin.choices.bgp import (
    BGPAddressFamilyChoices,
    BGPCommunityTypeChoices,
    BGPMaximumPrefixActionChoices,
    BGPStatusChoices,
)
from netbox_routing_plugin.models import (
    BFDProfile,
    BGPAddressFamily,
    BGPInstance,
    BGPListenRange,
    BGPPeer,
    BGPPeerAddressFamily,
    BGPPeerGroup,
    PrefixList,
    RoutePolicy,
)

__all__ = (
    'BFDProfileImportForm',
    'BGPInstanceImportForm',
    'BGPAddressFamilyImportForm',
    'BGPPeerGroupImportForm',
    'BGPListenRangeImportForm',
    'BGPPeerImportForm',
    'BGPPeerAddressFamilyImportForm',
)


def _device_field():
    return CSVModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        to_field_name='name',
        help_text=_('Name of the device of the BGP instance'),
    )


def _vrf_field():
    return CSVModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the VRF of the BGP instance (empty: the global table)'),
    )


def _policy_field(direction):
    return CSVModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the %s route policy') % direction,
    )


def _prefix_list_field(direction):
    return CSVModelChoiceField(
        queryset=PrefixList.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the %s prefix list') % direction,
    )


def _asn_field(label):
    return CSVModelChoiceField(
        queryset=ASN.objects.all(),
        required=False,
        to_field_name='asn',
        help_text=_('Number of the %s ASN') % label,
    )


def _bfd_field():
    return CSVModelChoiceField(
        queryset=BFDProfile.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Name of the BFD profile'),
    )


def _net(value, field):
    """An address or prefix typed in a row, as a form error when it is not one"""
    try:
        return IPNetwork(value)
    except (AddrFormatError, ValueError):
        raise forms.ValidationError({field: _('Not an IP address or prefix.')})


def _instance_of(device, vrf):
    """The BGP instance on a device in a VRF (no VRF: the global table)"""
    if device is None:
        return None
    return BGPInstance.objects.filter(device=device, vrf=vrf).first()


class _InstanceRowMixin:
    """A row names its instance by device and VRF, like the other BGP objects. The
    instance is found in clean(), and kept on the object (it is not a CSV column)."""

    def _find_instance(self, cleaned):
        instance = _instance_of(cleaned.get('device'), cleaned.get('vrf'))
        if instance is None:
            raise forms.ValidationError(
                _('There is no BGP instance on this device in this VRF.')
            )
        return instance

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('device') is None:
            return cleaned
        self.bgp_instance = self._find_instance(cleaned)
        if 'instance' in {field.name for field in self.Meta.model._meta.fields}:
            self.instance.instance = self.bgp_instance
        return cleaned


class BGPInstanceImportForm(NetBoxModelImportForm):
    device = _device_field()
    vrf = _vrf_field()
    asn = _asn_field('instance')
    confederation_identifier = _asn_field('confederation identifier')
    import_policy = _policy_field('import')
    export_policy = _policy_field('export')

    class Meta:
        model = BGPInstance
        fields = (
            'name',
            'device',
            'vrf',
            'asn',
            'router_id',
            'asdot',
            'cluster_id',
            'confederation_identifier',
            'graceful_restart',
            'graceful_restart_time',
            'graceful_restart_stale_time',
            'graceful_restart_helper_only',
            'import_policy',
            'export_policy',
            'description',
            'comments',
            'tags',
        )


class BGPAddressFamilyImportForm(_InstanceRowMixin, NetBoxModelImportForm):
    device = _device_field()
    vrf = _vrf_field()
    address_family = CSVChoiceField(
        choices=BGPAddressFamilyChoices,
        required=True,
        help_text=_('Address family of the instance'),
    )

    class Meta:
        model = BGPAddressFamily
        fields = (
            'device',
            'vrf',
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
            'description',
            'comments',
            'tags',
        )

    def clean(self):
        cleaned = super().clean()
        instance = getattr(self, 'bgp_instance', None)
        if (
            instance
            and BGPAddressFamily.objects.filter(
                instance=instance, address_family=cleaned.get('address_family')
            ).exists()
        ):
            raise forms.ValidationError(
                _('The instance already has this address family.')
            )
        return cleaned


class BGPPeerGroupImportForm(_InstanceRowMixin, NetBoxModelImportForm):
    device = _device_field()
    vrf = _vrf_field()
    remote_as = _asn_field('remote')
    local_as = _asn_field('local')
    bfd = _bfd_field()
    import_policy = _policy_field('import')
    export_policy = _policy_field('export')

    class Meta:
        model = BGPPeerGroup
        fields = (
            'name',
            'device',
            'vrf',
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
            'route_reflector_client',
            'extended_nexthop',
            'keepalive',
            'hold_time',
            'listen_limit',
            'import_policy',
            'export_policy',
            'description',
            'comments',
            'tags',
        )


class BGPListenRangeImportForm(_InstanceRowMixin, NetBoxModelImportForm):
    device = _device_field()
    vrf = _vrf_field()
    peer_group = forms.CharField(
        required=True,
        help_text=_('Name of the peer group of the instance that listens'),
    )
    prefix = forms.CharField(
        required=True,
        help_text=_('Prefix of IPAM, in the VRF of the instance'),
    )

    class Meta:
        model = BGPListenRange
        fields = ('description', 'comments', 'tags')

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('device') is None:
            return cleaned
        instance = self.bgp_instance
        group = BGPPeerGroup.objects.filter(
            instance=instance, name=cleaned.get('peer_group')
        ).first()
        if group is None:
            raise forms.ValidationError(
                {'peer_group': _('No peer group of this name.')}
            )
        prefix = Prefix.objects.filter(
            prefix=_net(cleaned['prefix'], 'prefix'), vrf=instance.vrf
        ).first()
        if prefix is None:
            raise forms.ValidationError(
                {'prefix': _('No prefix of IPAM in the VRF of the instance.')}
            )
        self.instance.peer_group = group
        self.instance.prefix = prefix
        return cleaned


class BGPPeerImportForm(_InstanceRowMixin, NetBoxModelImportForm):
    """A neighbor by its address, or an unnumbered one by an interface of the device"""

    device = _device_field()
    vrf = _vrf_field()
    peer = forms.CharField(
        required=False,
        help_text=_('Address of the neighbor, in the VRF of the instance'),
    )
    interface = forms.CharField(
        required=False,
        help_text=_('Name of the interface of the device, for an unnumbered neighbor'),
    )
    source = forms.CharField(
        required=False,
        help_text=_('Address of this router to open the session from'),
    )
    peer_group = forms.CharField(
        required=False, help_text=_('Name of the peer group of the instance')
    )
    remote_as = _asn_field('remote')
    local_as = _asn_field('local')
    bfd = _bfd_field()
    import_policy = _policy_field('import')
    export_policy = _policy_field('export')
    status = CSVChoiceField(
        choices=BGPStatusChoices, required=False, help_text=_('Status of the session')
    )

    class Meta:
        model = BGPPeer
        fields = (
            'name',
            'device',
            'vrf',
            'status',
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
            'route_reflector_client',
            'extended_nexthop',
            'keepalive',
            'hold_time',
            'import_policy',
            'export_policy',
            'description',
            'comments',
            'tags',
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('device') is None:
            return cleaned
        instance = self.bgp_instance
        address, interface = cleaned.get('peer'), cleaned.get('interface')
        if bool(address) == bool(interface):
            raise forms.ValidationError(
                _(
                    'Give the address of the neighbor or an interface, not both nor neither.'
                )
            )
        if address:
            ip = IPAddress.objects.filter(
                address=_net(address, 'peer'), vrf=instance.vrf
            ).first()
            if ip is None:
                raise forms.ValidationError({'peer': _('No IP address in the VRF.')})
            self.instance.peer = ip
        if interface:
            found = Interface.objects.filter(
                device=instance.device, name=interface
            ).first()
            if found is None:
                raise forms.ValidationError(
                    {'interface': _('No interface of this name on the device.')}
                )
            self.instance.interface = found
        if cleaned.get('source'):
            source = IPAddress.objects.filter(
                address=_net(cleaned['source'], 'source'), vrf=instance.vrf
            ).first()
            if source is None:
                raise forms.ValidationError({'source': _('No IP address in the VRF.')})
            self.instance.source = source
        if cleaned.get('peer_group'):
            group = BGPPeerGroup.objects.filter(
                instance=instance, name=cleaned['peer_group']
            ).first()
            if group is None:
                raise forms.ValidationError(
                    {'peer_group': _('No peer group of this name in the instance.')}
                )
            self.instance.peer_group = group
        return cleaned


class BGPPeerAddressFamilyImportForm(_InstanceRowMixin, NetBoxModelImportForm):
    """A neighbor (by its address) or a peer group (by its name) and an address family
    of its instance"""

    device = _device_field()
    vrf = _vrf_field()
    peer = forms.CharField(
        required=False, help_text=_('Address of the neighbor, or empty for a group')
    )
    peer_group = forms.CharField(
        required=False, help_text=_('Name of the peer group, or empty for a neighbor')
    )
    address_family = CSVChoiceField(
        choices=BGPAddressFamilyChoices,
        required=True,
        help_text=_('Address family of the instance'),
    )
    import_policy = _policy_field('import')
    export_policy = _policy_field('export')
    prefixlist_in = _prefix_list_field('inbound')
    prefixlist_out = _prefix_list_field('outbound')
    send_community = forms.MultipleChoiceField(
        choices=BGPCommunityTypeChoices,
        required=False,
        help_text=_('Standard, extended and/or large, separated by commas'),
    )
    maximum_prefix_action = CSVChoiceField(
        choices=BGPMaximumPrefixActionChoices,
        required=False,
        help_text=_('Action when the maximum is exceeded'),
    )

    class Meta:
        model = BGPPeerAddressFamily
        fields = (
            'device',
            'vrf',
            'enabled',
            'import_policy',
            'export_policy',
            'prefixlist_in',
            'prefixlist_out',
            'send_community',
            'next_hop_self',
            'remove_private_as',
            'allowas_in',
            'maximum_prefix',
            'maximum_prefix_warning',
            'maximum_prefix_action',
            'maximum_prefix_restart',
            'description',
            'comments',
            'tags',
        )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('device') is None:
            return cleaned
        address, group_name = cleaned.get('peer'), cleaned.get('peer_group')
        if bool(address) == bool(group_name):
            raise forms.ValidationError(
                _(
                    'Give the address of a neighbor or the name of a peer group, not both.'
                )
            )
        instance = _instance_of(cleaned['device'], cleaned.get('vrf'))
        if instance is None:
            raise forms.ValidationError(
                _('There is no BGP instance on this device in this VRF.')
            )
        af = BGPAddressFamily.objects.filter(
            instance=instance, address_family=cleaned.get('address_family')
        ).first()
        if af is None:
            raise forms.ValidationError(
                {'address_family': _('The instance has no such address family.')}
            )
        if address:
            peer = BGPPeer.objects.filter(
                instance=instance, peer__address=_net(address, 'peer')
            ).first()
            if peer is None:
                raise forms.ValidationError(
                    {'peer': _('No neighbor with this address in the instance.')}
                )
            self.instance.peer = peer
        else:
            group = BGPPeerGroup.objects.filter(
                instance=instance, name=group_name
            ).first()
            if group is None:
                raise forms.ValidationError(
                    {'peer_group': _('No peer group of this name in the instance.')}
                )
            self.instance.peer_group = group
        self.instance.address_family = af
        return cleaned


class BFDProfileImportForm(NetBoxModelImportForm):
    tenant = CSVModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='name',
        help_text=_('Tenant name'),
    )

    class Meta:
        model = BFDProfile
        fields = (
            'name',
            'min_tx_int',
            'min_rx_int',
            'multiplier',
            'hold',
            'tenant',
            'description',
            'comments',
            'tags',
        )
