from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing.forms import OSPFInterfaceForm
from netbox_routing.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = (
    'OSPFInterfaceAuthenticationTestCase',
    'OSPFInterfaceAuthenticationMigrationTestCase',
)

# md5('password')
PASSWORD_MD5 = '5f4dcc3b5aa765d61d8327deb882cf99'


class OSPFInterfaceAuthenticationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1', process_id=1
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _interface(self, **kwargs):
        return OSPFInterface(
            instance=self.instance, area=self.area, interface=self.interface, **kwargs
        )

    def _assert_invalid(self, field, **kwargs):
        with self.assertRaises(ValidationError) as cm:
            self._interface(**kwargs).full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_no_authentication_is_valid(self):
        self._interface().full_clean()
        self._interface(authentication='null').full_clean()

    def test_message_digest_needs_a_key_and_a_key_id(self):
        self._interface(
            authentication='message-digest',
            passphrase='password',
            authentication_key_id=1,
        ).full_clean()
        self._assert_invalid(
            'passphrase', authentication='message-digest', authentication_key_id=1
        )
        self._assert_invalid(
            'authentication_key_id',
            authentication='message-digest',
            passphrase='password',
        )
        self._assert_invalid(
            'key_chain',
            authentication='message-digest',
            passphrase='password',
            authentication_key_id=1,
            key_chain='chain',
        )

    def test_key_id_limits(self):
        for key_id in (0, 255):
            self._interface(
                authentication='message-digest',
                passphrase='password',
                authentication_key_id=key_id,
            ).full_clean()
        self._assert_invalid(
            'authentication_key_id',
            authentication='message-digest',
            passphrase='password',
            authentication_key_id=256,
        )

    def test_algorithm_defaults_to_md5(self):
        self.assertEqual(self._interface().message_digest_algorithm, 'md5')
        for algorithm in ('hmac-sha-1', 'hmac-sha-256', 'hmac-sha-384', 'hmac-sha-512'):
            self._interface(
                authentication='message-digest',
                passphrase='password',
                authentication_key_id=1,
                message_digest_algorithm=algorithm,
            ).full_clean()
        self._assert_invalid(
            'message_digest_algorithm',
            authentication='message-digest',
            passphrase='password',
            authentication_key_id=1,
            message_digest_algorithm='sha-1',
        )

    def test_key_chain_needs_its_name_and_no_key(self):
        self._interface(authentication='key-chain', key_chain='chain').full_clean()
        self._assert_invalid('key_chain', authentication='key-chain')
        self._assert_invalid(
            'passphrase',
            authentication='key-chain',
            key_chain='chain',
            passphrase='password',
        )
        self._assert_invalid(
            'authentication_key_id',
            authentication='key-chain',
            key_chain='chain',
            authentication_key_id=1,
        )

    def test_key_without_authentication_is_rejected(self):
        self._assert_invalid('passphrase', passphrase='password')
        self._assert_invalid('key_chain', key_chain='chain')
        self._assert_invalid('authentication_key_id', authentication_key_id=1)

    def test_the_key_is_stored_in_plain_text(self):
        ospf_interface = self._interface(
            authentication='message-digest',
            passphrase='password',
            authentication_key_id=1,
        )
        ospf_interface.save()
        self.assertEqual(
            OSPFInterface.objects.get(pk=ospf_interface.pk).passphrase, 'password'
        )

    def test_md5_function_returns_the_digest_of_the_key(self):
        self.assertEqual(
            self._interface(passphrase='password').get_passphrase_md5(), PASSWORD_MD5
        )
        self.assertIsNone(self._interface().get_passphrase_md5())
        self.assertIsNone(self._interface(passphrase='').get_passphrase_md5())

    def test_md5_digest_is_shown_only_when_checked(self):
        ospf_interface = self._interface(passphrase='password')
        self.assertIsNone(ospf_interface.md5_digest)
        ospf_interface.show_md5 = True
        self.assertEqual(ospf_interface.md5_digest, PASSWORD_MD5)

    def test_md5_digest_needs_a_key(self):
        self._assert_invalid('show_md5', show_md5=True)

    def test_form_saves_the_key_and_the_checkbox(self):
        form = OSPFInterfaceForm(
            data={
                'device': self.device.pk,
                'interface': self.interface.pk,
                'instance': self.instance.pk,
                'area': self.area.pk,
                'network_type': 'broadcast',
                'authentication': 'message-digest',
                'authentication_key_id': 7,
                'passphrase': 'password',
                'show_md5': 'on',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        ospf_interface = form.save()
        self.assertEqual(ospf_interface.message_digest_algorithm, 'md5')
        self.assertEqual(ospf_interface.md5_digest, PASSWORD_MD5)


class OSPFInterfaceAuthenticationMigrationTestCase(TransactionTestCase):
    """Key chain names move out of the passphrase; message digest keys get an ID."""

    BEFORE = [('netbox_routing', '0053_ospf_rfc_defaults_and_validations')]
    AFTER = [('netbox_routing', '0055_ospfinterface_authentication_data')]

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_existing_authentication_is_split(self):
        apps = self._migrate(self.BEFORE)
        Site = apps.get_model('dcim', 'Site')
        Manufacturer = apps.get_model('dcim', 'Manufacturer')
        DeviceType = apps.get_model('dcim', 'DeviceType')
        DeviceRole = apps.get_model('dcim', 'DeviceRole')
        Device = apps.get_model('dcim', 'Device')
        Interface = apps.get_model('dcim', 'Interface')
        Instance = apps.get_model('netbox_routing', 'OSPFInstance')
        Area = apps.get_model('netbox_routing', 'OSPFArea')
        Model = apps.get_model('netbox_routing', 'OSPFInterface')

        site = Site.objects.create(name='Site', slug='site')
        manufacturer = Manufacturer.objects.create(name='M', slug='m')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='T', slug='t'
        )
        role = DeviceRole.objects.create(name='R', slug='r')
        device = Device.objects.create(
            name='D', site=site, device_type=device_type, role=role
        )
        instance = Instance.objects.create(
            name='I', device=device, router_id='1.1.1.1', process_id=1
        )
        area = Area.objects.create(instance=instance, area_id='1')
        for name, authentication, passphrase in (
            ('eth0', 'key-chain', 'my-chain'),
            ('eth1', 'message-digest', 'secret'),
            ('eth2', None, None),
        ):
            Model.objects.create(
                instance=instance,
                area=area,
                interface=Interface.objects.create(
                    device=device, name=name, type='virtual'
                ),
                authentication=authentication,
                passphrase=passphrase,
            )

        apps = self._migrate(self.AFTER)
        Model = apps.get_model('netbox_routing', 'OSPFInterface')
        by_name = {
            m.interface.name: m for m in Model.objects.select_related('interface')
        }
        self.assertEqual(by_name['eth0'].key_chain, 'my-chain')
        self.assertIsNone(by_name['eth0'].passphrase)
        self.assertEqual(by_name['eth1'].passphrase, 'secret')
        self.assertEqual(by_name['eth1'].authentication_key_id, 1)
        self.assertIsNone(by_name['eth2'].authentication_key_id)
        self.assertEqual(by_name['eth2'].key_chain, '')

    def tearDown(self):
        # Leave the database at the latest migration for the other tests
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()
