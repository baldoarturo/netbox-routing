from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_plugin.choices import (
    OSPFAddressFamilyChoices,
    OSPFAuthenticationChoices,
    OSPFMessageDigestAlgorithmChoices,
)
from netbox_routing_plugin.forms.model_objects.ospf import OSPFAreaForm
from netbox_routing_plugin.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFAuthenticationTrailerTestCase',)

TRAILER = OSPFAuthenticationChoices.TRAILER
SHA256 = OSPFMessageDigestAlgorithmChoices.HMAC_SHA_256


class OSPFAuthenticationTrailerTestCase(TestCase):
    """The authentication trailer (RFC 7166) belongs to OSPFv3, the rest to OSPFv2."""

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.v4 = OSPFInstance.objects.create(
            name='v2', device=cls.device, router_id='1.1.1.1'
        )
        cls.v6 = OSPFInstance.objects.create(
            name='v3',
            device=cls.device,
            router_id='1.1.1.1',
            address_family=OSPFAddressFamilyChoices.IPV6,
        )
        cls.area6 = OSPFArea.objects.create(instance=cls.v6, area_id='1')
        cls.area4 = OSPFArea.objects.create(instance=cls.v4, area_id='1')

    def _trailer(self, **kwargs):
        values = {
            'authentication': TRAILER,
            'passphrase': 'secret',
            'authentication_key_id': 1,
            'message_digest_algorithm': SHA256,
        }
        values.update(kwargs)
        return values

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_trailer_on_ipv6_at_every_level(self):
        self.v6.__dict__.update(self._trailer())
        self.v6.full_clean()
        self.area6.__dict__.update(self._trailer(authentication_key_id=65535))
        self.area6.full_clean()
        OSPFInterface(
            instance=self.v6,
            area=self.area6,
            interface=self.interface,
            **self._trailer(),
        ).full_clean()

    def test_trailer_is_refused_on_ipv4(self):
        self.v4.__dict__.update(self._trailer())
        self._assert_invalid(self.v4, 'authentication')
        self.area4.__dict__.update(self._trailer())
        self._assert_invalid(self.area4, 'authentication')

    def test_v2_types_are_refused_on_ipv6(self):
        self.v6.authentication = OSPFAuthenticationChoices.SIMPLE
        self.v6.passphrase = 'secret'
        self._assert_invalid(self.v6, 'authentication')
        self.v6.authentication = OSPFAuthenticationChoices.MESSAGE_DIGEST
        self.v6.authentication_key_id = 1
        self._assert_invalid(self.v6, 'authentication')

    def test_key_chain_and_null_on_ipv6(self):
        self.v6.authentication = OSPFAuthenticationChoices.KEYCHAIN
        self.v6.key_chain = 'chain'
        self.v6.full_clean()
        self.v6.authentication = OSPFAuthenticationChoices.NULL
        self.v6.key_chain = ''
        self.v6.full_clean()

    def test_trailer_needs_key_sa_id_and_hmac_sha(self):
        self.v6.__dict__.update(self._trailer(passphrase=None))
        self._assert_invalid(self.v6, 'passphrase')
        self.v6.__dict__.update(self._trailer(authentication_key_id=None))
        self._assert_invalid(self.v6, 'authentication_key_id')
        self.v6.__dict__.update(
            self._trailer(
                message_digest_algorithm=OSPFMessageDigestAlgorithmChoices.MD5
            )
        )
        self._assert_invalid(self.v6, 'message_digest_algorithm')
        self.v6.__dict__.update(self._trailer(key_chain='chain'))
        self._assert_invalid(self.v6, 'key_chain')

    def test_sa_id_goes_up_to_16_bits(self):
        self.v6.__dict__.update(self._trailer(authentication_key_id=65536))
        self._assert_invalid(self.v6, 'authentication_key_id')

    def test_message_digest_key_id_stays_8_bits(self):
        self.v4.authentication = OSPFAuthenticationChoices.MESSAGE_DIGEST
        self.v4.passphrase = 'secret'
        self.v4.authentication_key_id = 256
        self._assert_invalid(self.v4, 'authentication_key_id')

    def test_no_type_rule_between_interface_and_area_on_ipv6(self):
        """The RFC 2328 rule (one AuType per area) does not exist in OSPFv3."""
        self.area6.authentication = OSPFAuthenticationChoices.KEYCHAIN
        self.area6.key_chain = 'chain'
        self.area6.save()
        OSPFInterface(
            instance=self.v6,
            area=self.area6,
            interface=self.interface,
            authentication=OSPFAuthenticationChoices.NULL,
        ).full_clean()

    def test_form_offers_only_the_types_of_the_family(self):
        for instance, expected in (
            (self.v4, OSPFAuthenticationChoices.IPV4),
            (self.v6, OSPFAuthenticationChoices.IPV6),
        ):
            form = OSPFAreaForm(initial={'instance': instance.pk})
            offered = {value for value, _ in form.fields['authentication'].choices}
            offered.discard('')
            self.assertEqual(offered, set(expected))
