from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_protocols.forms import OSPFAreaForm
from netbox_routing_protocols.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFAuthenticationInheritanceTestCase',)

MD = {
    'authentication': 'message-digest',
    'authentication_key_id': 1,
    'passphrase': 'password',
}


class OSPFAuthenticationInheritanceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interfaces = [
            Interface.objects.create(
                name=f'Interface {i}', device=cls.device, type='virtual'
            )
            for i in (1, 2, 3)
        ]
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1', process_id=1
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _ospf_interface(self, n=0, **kwargs):
        return OSPFInterface(
            instance=self.instance,
            area=self.area,
            interface=self.interfaces[n],
            **kwargs,
        )

    def _save_interface(self, n=0, **kwargs):
        ospf_interface = self._ospf_interface(n, **kwargs)
        ospf_interface.save()
        return ospf_interface

    def _set(self, obj, **values):
        for name, value in values.items():
            setattr(obj, name, value)
        obj.save()

    def test_without_authentication_nothing_is_in_use(self):
        ospf_interface = self._ospf_interface()
        self.assertIsNone(ospf_interface.effective_authentication)
        self.assertIsNone(ospf_interface.authentication_source)

    def test_interface_uses_the_area_then_the_instance_authentication(self):
        ospf_interface = self._ospf_interface()
        self._set(self.instance, **MD)
        self.assertEqual(ospf_interface.effective_authentication, 'message-digest')
        self.assertEqual(ospf_interface.authentication_source, 'instance')

        self.area.refresh_from_db()
        self._set(self.area, authentication='key-chain', key_chain='chain')
        self.assertEqual(ospf_interface.effective_authentication, 'key-chain')
        self.assertEqual(ospf_interface.authentication_source, 'area')

    def test_interface_own_authentication_wins(self):
        self._set(self.area, **MD)
        ospf_interface = self._ospf_interface(
            authentication='key-chain', key_chain='chain'
        )
        self.assertEqual(ospf_interface.effective_authentication, 'key-chain')
        self.assertEqual(ospf_interface.authentication_source, 'interface')

    def test_an_interface_inherits_the_authentication_of_the_area(self):
        self._set(self.area, **MD)
        self._ospf_interface().full_clean()

    def test_new_interface_cannot_go_without_authentication_in_the_area(self):
        self._set(self.area, **MD)
        with self.assertRaises(ValidationError) as cm:
            self._ospf_interface(authentication='null').full_clean()
        self.assertIn('authentication', cm.exception.error_dict)

    def test_new_interface_can_use_a_key_chain_in_a_message_digest_area(self):
        self._set(self.area, **MD)
        self._ospf_interface(authentication='key-chain', key_chain='chain').full_clean()
        self._ospf_interface(**MD).full_clean()

    def test_new_interface_cannot_authenticate_in_an_area_without_it(self):
        self._set(self.area, authentication='null')
        with self.assertRaises(ValidationError) as cm:
            self._ospf_interface(**MD).full_clean()
        self.assertIn('authentication', cm.exception.error_dict)
        self._ospf_interface(authentication='null').full_clean()

    def test_the_three_authentication_types_cannot_be_mixed_in_an_area(self):
        simple = {'authentication': 'simple', 'passphrase': 'secret'}
        # (type of the area, type of the interface, conflict)
        for area, interface, conflict in (
            ('simple', 'simple', False),
            ('simple', 'message-digest', True),
            ('simple', 'key-chain', True),
            ('simple', 'null', True),
            ('message-digest', 'simple', True),
            ('message-digest', 'key-chain', False),
            ('null', 'simple', True),
        ):
            with self.subTest(area=area, interface=interface):
                blocks = {
                    'simple': simple,
                    'message-digest': MD,
                    'null': {'authentication': 'null'},
                }
                self._set(
                    self.area,
                    authentication=None,
                    passphrase=None,
                    authentication_key_id=None,
                    key_chain='',
                )
                self._set(self.area, **blocks[area])
                own = {
                    'simple': simple,
                    'message-digest': MD,
                    'key-chain': {'authentication': 'key-chain', 'key_chain': 'c'},
                    'null': {'authentication': 'null'},
                }[interface]
                ospf_interface = self._ospf_interface(**own)
                if conflict:
                    with self.assertRaises(ValidationError) as cm:
                        ospf_interface.full_clean()
                    self.assertIn('authentication', cm.exception.error_dict)
                else:
                    ospf_interface.full_clean()

    def test_the_instance_default_applies_to_areas_without_their_own(self):
        self._set(self.instance, **MD)
        with self.assertRaises(ValidationError):
            self._ospf_interface(authentication='null').full_clean()
        # an area with its own type is not bound by the instance default
        self._set(self.area, authentication='null')
        self._ospf_interface(authentication='null').full_clean()

    def test_area_authentication_is_checked_against_its_interfaces(self):
        self._save_interface(0, authentication='null')
        self._save_interface(1)
        self.area.authentication = 'message-digest'
        self.area.authentication_key_id = 1
        self.area.passphrase = 'password'
        with self.assertRaises(ValidationError) as cm:
            self.area.full_clean()
        self.assertIn('authentication', cm.exception.error_dict)
        self.assertIn('Interface 1', str(cm.exception))
        self.assertNotIn('Interface 2', str(cm.exception))

    def test_area_authentication_is_valid_when_the_interfaces_agree(self):
        self._save_interface(0, **MD)
        self._save_interface(1)
        self.area.authentication = 'message-digest'
        self.area.authentication_key_id = 1
        self.area.passphrase = 'password'
        self.area.full_clean()

    def test_instance_authentication_is_checked_against_its_interfaces(self):
        self._save_interface(0, authentication='null')
        self.instance.authentication = 'message-digest'
        self.instance.authentication_key_id = 1
        self.instance.passphrase = 'password'
        with self.assertRaises(ValidationError) as cm:
            self.instance.full_clean()
        self.assertIn('authentication', cm.exception.error_dict)

    def test_instance_default_ignores_areas_with_their_own_authentication(self):
        self._set(self.area, authentication='null')
        self._save_interface(0, authentication='null')
        self.instance.authentication = 'message-digest'
        self.instance.authentication_key_id = 1
        self.instance.passphrase = 'password'
        self.instance.full_clean()

    def test_area_and_instance_authentication_blocks_are_validated(self):
        for obj in (self.area, self.instance):
            with self.subTest(obj=type(obj).__name__):
                obj.authentication = 'message-digest'
                obj.passphrase = 'password'
                with self.assertRaises(ValidationError) as cm:
                    obj.full_clean()
                self.assertIn('authentication_key_id', cm.exception.error_dict)
                obj.authentication_key_id = 1
                obj.full_clean()
                obj.authentication = None
                obj.authentication_key_id = None
                obj.passphrase = None

    def test_area_md5_digest(self):
        self._set(self.area, show_md5=False, **MD)
        self.assertIsNone(self.area.md5_digest)
        self.area.show_md5 = True
        self.assertEqual(self.area.md5_digest, '5f4dcc3b5aa765d61d8327deb882cf99')

    def test_area_form_saves_the_authentication(self):
        form = OSPFAreaForm(
            data={
                'instance': self.instance.pk,
                'area_id': '2',
                'area_type': 'standard',
                'authentication': 'message-digest',
                'authentication_key_id': 3,
                'passphrase': 'password',
                'show_md5': 'on',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        area = form.save()
        self.assertEqual(area.message_digest_algorithm, 'md5')
        self.assertEqual(area.authentication_key_id, 3)
        self.assertEqual(area.md5_digest, '5f4dcc3b5aa765d61d8327deb882cf99')
