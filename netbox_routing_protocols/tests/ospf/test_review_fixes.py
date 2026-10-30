from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF, IPAddress
from utilities.exceptions import AbortRequest
from utilities.testing import create_test_device

from netbox_routing_protocols.choices import (
    OSPFAddressFamilyChoices,
    OSPFAuthenticationChoices,
)
from netbox_routing_protocols.forms import (
    OSPFInterfaceFilterForm,
    OSPFPrefixSIDFilterForm,
    OSPFRedistributionFilterForm,
    OSPFVirtualLinkForm,
)
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFAuthenticationKey,
    OSPFInstance,
    OSPFInterface,
    OSPFNeighbor,
    OSPFRedistribution,
)

__all__ = ('OSPFReviewFixesTestCase',)

MD = OSPFAuthenticationChoices.MESSAGE_DIGEST


class OSPFReviewFixesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.instance = OSPFInstance.objects.create(
            name='Main',
            device=cls.device,
            router_id='1.1.1.1',
            authentication=MD,
            passphrase='primary',
            authentication_key_id=1,
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')
        cls.interface = Interface.objects.create(
            name='Eth1', device=cls.device, type='virtual'
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_virtual_link_form_has_the_ttl_security_fields(self):
        form = OSPFVirtualLinkForm()
        self.assertIn('ttl_security', form.fields)
        self.assertIn('ttl_security_hops', form.fields)

    def test_filter_forms_offer_the_missing_fields(self):
        for form, names in (
            (OSPFInterfaceFilterForm, ('te_metric', 'adjacency_sid')),
            (OSPFRedistributionFilterForm, ('route_policy_id', 'metric')),
            (OSPFPrefixSIDFilterForm, ('explicit_null', 'no_php')),
        ):
            for name in names:
                self.assertIn(name, form().fields)
        grouped = {
            field
            for fieldset in OSPFInterfaceFilterForm.fieldsets
            for field in fieldset.items
        }
        self.assertIn('te_metric', grouped)

    def test_moving_an_address_keeps_the_neighbors_valid(self):
        ospf_interface = OSPFInterface.objects.create(
            instance=self.instance,
            area=self.area,
            interface=self.interface,
            network_type='non_broadcast',
        )
        address = IPAddress.objects.create(
            address='10.0.0.1/30', assigned_object=self.interface
        )
        IPAddress.objects.create(
            address='192.168.0.1/24', assigned_object=self.interface
        )
        OSPFNeighbor.objects.create(
            ospf_interface=ospf_interface, ip_address='10.0.0.2', priority=1
        )
        other = Interface.objects.create(
            name='Eth2', device=self.device, type='virtual'
        )
        address.assigned_object = other
        with self.assertRaises(AbortRequest):
            address.save()
        address.refresh_from_db()
        address.address = '172.16.0.1/30'
        with self.assertRaises(AbortRequest):
            address.save()
        # A change that keeps the neighbor on an attached network is fine
        address.address = '10.0.0.5/29'
        address.save()

    def test_inherited_keys_stop_the_authentication_from_changing(self):
        ospf_interface = OSPFInterface.objects.create(
            instance=self.instance,
            area=self.area,
            interface=self.interface,
            network_type='point_to_point',
        )
        OSPFAuthenticationKey.objects.create(
            ospf_interface=ospf_interface, key_id=2, passphrase='next'
        )
        for owner in (self.instance, self.area):
            owner.authentication = OSPFAuthenticationChoices.NULL
            owner.passphrase = None
            owner.authentication_key_id = None
            self._assert_invalid(owner, 'authentication')
            owner.refresh_from_db()

    def test_redistribution_of_another_family_is_refused(self):
        other = OSPFInstance.objects.create(
            name='v3',
            device=self.device,
            router_id='2.2.2.2',
            address_family=OSPFAddressFamilyChoices.IPV6,
            vrf=VRF.objects.create(name='VRF 1'),
        )
        self._assert_invalid(
            OSPFRedistribution(
                instance=self.instance, protocol='ospf', ospf_source=other
            ),
            'ospf_source',
        )
