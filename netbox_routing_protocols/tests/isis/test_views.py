# SPDX-License-Identifier: Apache-2.0

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from dcim.models import Interface
from ipam.models import VRF
from utilities.testing import ViewTestCases, create_test_device

from netbox_routing_protocols.models import (
    ISISRedistribution,
    ISISRouteLeak,
    ISISSummaryAddress,
    ISISFlexAlgo,
    ISISInstance,
    ISISInterface,
    ISISInterfaceLevel,
    ISISLevel,
    ISISPrefixSID,
    ISISSegmentRouting,
    ISISSRv6Locator,
)
from netbox_routing_protocols.tests.base import LeanCoreTestsMixin

__all__ = (
    'ISISInstanceViewTestCase',
    'ISISInterfaceViewTestCase',
    'ISISViewExportsTestCase',
    'ISISBulkEditViewsTestCase',
)


class ISISViewExportsTestCase(SimpleTestCase):
    """Bulk views defined in views/isis.py must also be re-exported from the views
    package __all__, like every other IS-IS view group (regression guard for the
    PrefixSID/SRv6Locator bulk views that were previously omitted)."""

    def test_bulk_views_exported(self):
        from netbox_routing_protocols import views

        for name in (
            'ISISPrefixSIDBulkDeleteView',
            'ISISPrefixSIDBulkImportView',
            'ISISSRv6LocatorBulkDeleteView',
            'ISISSRv6LocatorBulkImportView',
        ):
            with self.subTest(view=name):
                self.assertIn(name, views.__all__)
                self.assertTrue(hasattr(views, name))


class ISISInstanceViewTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = ISISInstance

    @classmethod
    def setUpTestData(cls):
        vrf = VRF.objects.create(name='Test')
        devices = [
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
        ]

        instances = (
            cls.model(
                device=devices[0],
                process_tag='CORE',
                net='49.0001.0000.0000.0001.00',
                is_type='level-1-2',
                vrf=None,
            ),
            cls.model(
                device=devices[0],
                process_tag='EDGE',
                net='49.0001.0000.0000.0002.00',
                is_type='level-2-only',
                vrf=None,
            ),
            cls.model(
                device=devices[0],
                process_tag='FABRIC',
                net='49.0001.0000.0000.0003.00',
                is_type='level-1',
                vrf=vrf,
            ),
        )
        cls.model.objects.bulk_create(instances)

        cls.form_data = {
            'device': devices[1].pk,
            'process_tag': 'ACCESS',
            'net': '49.0001.0000.0000.0004.00',
            'is_type': 'level-1-2',
            'vrf': vrf.pk,
        }

        cls.bulk_edit_data = {
            'description': 'A test instance description',
            'vrf': vrf.pk,
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:isisinstance_{}'


class ISISInterfaceViewTestCase(
    LeanCoreTestsMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = ISISInterface

    @classmethod
    def setUpTestData(cls):
        devices = [
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
        ]
        interfaces = (
            Interface(name='Interface 1', device=devices[0], type='virtual'),
            Interface(name='Interface 2', device=devices[0], type='virtual'),
            Interface(name='Interface 3', device=devices[1], type='virtual'),
            Interface(name='Interface 4', device=devices[1], type='virtual'),
        )
        Interface.objects.bulk_create(interfaces)

        instances = (
            ISISInstance(
                device=devices[0],
                process_tag='CORE',
                net='49.0001.0000.0000.0001.00',
                is_type='level-1-2',
            ),
            ISISInstance(
                device=devices[0],
                process_tag='EDGE',
                net='49.0001.0000.0000.0002.00',
                is_type='level-2-only',
            ),
            ISISInstance(
                device=devices[1],
                process_tag='FABRIC',
                net='49.0001.0000.0000.0003.00',
                is_type='level-1',
            ),
            ISISInstance(
                device=devices[1],
                process_tag='ACCESS',
                net='49.0001.0000.0000.0004.00',
                is_type='level-1-2',
            ),
        )
        ISISInstance.objects.bulk_create(instances)

        isis_interfaces = (
            cls.model(
                interface=interfaces[0],
                instance=ISISInstance.objects.get(process_tag='CORE'),
                address_family='ipv4',
                passive=False,
            ),
            cls.model(
                interface=interfaces[1],
                instance=ISISInstance.objects.get(process_tag='EDGE'),
                address_family='ipv6',
            ),
            cls.model(
                interface=interfaces[2],
                instance=ISISInstance.objects.get(process_tag='FABRIC'),
                address_family='ipv4',
                passive=False,
            ),
        )
        cls.model.objects.bulk_create(isis_interfaces)

        cls.form_data = {
            'interface': interfaces[3].pk,
            'instance': ISISInstance.objects.get(process_tag='ACCESS').pk,
            'address_family': 'ipv6',
            'circuit_type': 'level-1-2',
            'network_type': 'point-to-point',
            'metric': 10,
            'passive': True,
        }

        cls.bulk_edit_data = {
            'description': 'A test interface description',
            'passive': False,
            # hello auth type + key must be settable together in one bulk edit:
            # ISISInterface.clean() requires the pair, and the view runs
            # full_clean() per object, so exposing the type without the key would
            # make any auth bulk-edit fail validation.
            'hello_auth_type': 'md5',
            'hello_auth_key': 's3cret',
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:isisinterface_{}'


class ISISBulkEditViewsTestCase(TestCase):
    """Every IS-IS model can be edited in bulk (#442)."""

    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(
            username='bulk', password='x', is_superuser=True
        )
        cls.user = user
        device = create_test_device(name='Device 1')
        instance = ISISInstance.objects.create(device=device)
        interface = ISISInterface.objects.create(
            instance=instance,
            interface=Interface.objects.create(
                name='lo0', device=device, type='virtual'
            ),
            address_family='ipv4',
        )
        cls.cases = (
            (
                ISISLevel.objects.create(instance=instance, level=1),
                'default_metric',
                '10',
                10,
            ),
            (
                ISISInterfaceLevel.objects.create(interface=interface, level=1),
                'priority',
                '5',
                5,
            ),
            (
                ISISSegmentRouting.objects.create(instance=instance),
                'maximum_sid_depth',
                '5',
                5,
            ),
            (
                ISISFlexAlgo.objects.create(instance=instance, algo_id=128),
                'priority',
                '100',
                100,
            ),
            (
                ISISPrefixSID.objects.create(interface=interface, sid_index=1),
                'no_php',
                '2',
                True,
            ),
            (
                ISISSRv6Locator.objects.create(
                    instance=instance, name='L', prefix='2001:db8::/32'
                ),
                'enabled',
                '2',
                True,
            ),
            (
                ISISRedistribution.objects.create(
                    instance=instance, protocol='connected'
                ),
                'metric',
                '10',
                10,
            ),
            (
                ISISSummaryAddress.objects.create(
                    instance=instance, prefix='10.0.0.0/8'
                ),
                'metric',
                '10',
                10,
            ),
            (
                ISISRouteLeak.objects.create(instance=instance),
                'route_policy',
                'LEAK',
                'LEAK',
            ),
        )

    def test_bulk_edit(self):
        self.client.force_login(self.user)
        for obj, field, posted, expected in self.cases:
            with self.subTest(model=type(obj).__name__):
                url = reverse(
                    f'plugins:netbox_routing_protocols:{obj._meta.model_name}_bulk_edit'
                )
                response = self.client.post(
                    url, {'pk': [obj.pk], '_apply': '', field: posted}
                )
                self.assertEqual(response.status_code, 302, response.content[:300])
                obj.refresh_from_db()
                self.assertEqual(getattr(obj, field), expected)
