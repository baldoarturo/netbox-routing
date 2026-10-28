from dcim.models import Interface
from ipam.models import VRF
from utilities.testing import ViewTestCases, create_test_device

from netbox_routing_protocols.choices import OSPFNetworkTypeChoices
from netbox_routing_protocols.models import OSPFInstance, OSPFArea, OSPFInterface
from netbox_routing_protocols.tests.base import IPAddressFieldMixin

__all__ = (
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
)


class OSPFInstanceTestCase(
    IPAddressFieldMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = OSPFInstance

    @classmethod
    def setUpTestData(cls):
        vrf = VRF.objects.create(name='Test')
        devices = [
            create_test_device(name='Device 1'),
            create_test_device(name='Device 2'),
        ]

        instances = (
            cls.model(
                name="Instance 0",
                device=devices[0],
                router_id='10.0.0.1',
                process_id='0',
                vrf=None,
            ),
            cls.model(
                name="Instance 1",
                device=devices[0],
                router_id='1.1.1.1',
                process_id='1',
                vrf=None,
            ),
            cls.model(
                name="Instance 2",
                device=devices[0],
                router_id='2.2.2.2',
                process_id='2',
                vrf=vrf,
            ),
        )
        cls.model.objects.bulk_create(instances)

        cls.form_data = {
            'name': 'Instance X',
            'device': devices[1].pk,
            'router_id': '4.4.4.4',
            'process_id': 4,
            'vrf': vrf.pk,
            'default_originate': True,
            'default_originate_always': True,
            'default_originate_metric': 100,
            'default_originate_metric_type': '1',
            'graceful_restart': 'planned',
            'graceful_restart_period': 300,
            'spf_initial_delay': 100,
            'rfc1583_compatibility': False,
            'max_lsa': 5000,
            'reference_bandwidth': 10000,
            'maximum_paths': 8,
            'distance_external': 150,
        }

        cls.bulk_edit_data = {
            'description': 'A test Instance description',
            'vrf': vrf.pk,
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfinstance_{}'


class OSPFAreaTestCase(
    IPAddressFieldMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = OSPFArea

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        instance = OSPFInstance.objects.create(
            name='Instance 1', device=device, router_id='1.1.1.1', process_id=1
        )
        areas = (
            cls.model(instance=instance, area_id='1.1.1.1', area_type='stub'),
            cls.model(instance=instance, area_id='2.2.2.2', area_type='tsa'),
            cls.model(instance=instance, area_id='3.3.3.3', area_type='nssa'),
        )
        cls.model.objects.bulk_create(areas)

        cls.form_data = {
            'instance': instance.pk,
            'area_id': '4.4.4.4',
            'area_type': 'nssa',
            'default_cost': 20,
            'nssa_translate_always': True,
            'nssa_no_redistribution': True,
            'nssa_default_originate': True,
        }

        cls.bulk_edit_data = {
            'description': 'A test Area description',
            'area_type': 'stub',
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfarea_{}'


class OSPFInterfaceTestCase(
    IPAddressFieldMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = OSPFInterface

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
            OSPFInstance(
                name="Instance 0",
                device=devices[0],
                router_id='10.0.0.1',
                process_id='0',
            ),
            OSPFInstance(
                name="Instance 1",
                device=devices[0],
                router_id='1.1.1.1',
                process_id='1',
            ),
            OSPFInstance(
                name="Instance 2",
                device=devices[1],
                router_id='2.2.2.2',
                process_id='2',
            ),
            OSPFInstance(
                name="Instance 3",
                device=devices[1],
                router_id='3.3.3.3',
                process_id='3',
            ),
        )
        OSPFInstance.objects.bulk_create(instances)

        areas = (
            OSPFArea(instance=instances[0], area_id='0.0.0.0'),
            OSPFArea(instance=instances[1], area_id='1.1.1.1'),
            OSPFArea(instance=instances[2], area_id='2.2.2.2'),
            OSPFArea(instance=instances[3], area_id='3.3.3.3'),
        )
        OSPFArea.objects.bulk_create(areas)

        ospfinterfaces = (
            cls.model(
                interface=interfaces[0],
                instance=instances[0],
                area=areas[0],
                passive=False,
            ),
            cls.model(interface=interfaces[1], instance=instances[1], area=areas[1]),
            cls.model(
                interface=interfaces[2],
                instance=instances[2],
                area=areas[2],
                passive=False,
            ),
        )
        cls.model.objects.bulk_create(ospfinterfaces)

        cls.form_data = {
            'interface': interfaces[3].pk,
            'area': areas[3].pk,
            'instance': instances[3].pk,
            'network_type': OSPFNetworkTypeChoices.POINT_TO_POINT,
            'passive': True,
            'cost': 10,
            'mtu_ignore': True,
            'prefix_suppression': True,
            'flood_reduction': False,
            'hello_interval': 30,
            'dead_interval': 120,
        }

        cls.bulk_edit_data = {
            'description': 'A test Interface description',
            'passive': False,
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:ospfinterface_{}'
