from django.test import TestCase

from dcim.models import Interface
from ipam.models import VRF, IPAddress
from utilities.testing import create_test_device

from netbox_routing_protocols.forms import (
    OSPFAreaRangeImportForm,
    OSPFInterfaceImportForm,
    OSPFNeighborImportForm,
    OSPFNetworkImportForm,
    OSPFPrefixSIDImportForm,
    OSPFRedistributionImportForm,
    OSPFSummaryAddressImportForm,
    OSPFVirtualLinkImportForm,
)
from netbox_routing_protocols.models import (
    OSPFArea,
    OSPFAreaRange,
    OSPFInstance,
    OSPFInterface,
    OSPFNeighbor,
    OSPFPrefixSID,
    OSPFRedistribution,
    OSPFSummaryAddress,
    OSPFVirtualLink,
    RoutePolicy,
)

__all__ = ('OSPFBulkImportTestCase',)


class OSPFBulkImportTestCase(TestCase):
    """One CSV row per object: the device narrows the names and the area IDs."""

    @classmethod
    def setUpTestData(cls):
        # The same names and area IDs on two devices
        cls.devices = [create_test_device(name=f'Device {i}') for i in (1, 2)]
        cls.instances, cls.areas, cls.interfaces = [], [], []
        for number, device in enumerate(cls.devices, start=1):
            instance = OSPFInstance.objects.create(
                name='Main',
                device=device,
                router_id=f'{number}.{number}.{number}.{number}',
                opaque_capability=True,
                segment_routing=True,
                srgb_start=16000,
                srgb_size=8000,
            )
            cls.instances.append(instance)
            cls.areas.append(OSPFArea.objects.create(instance=instance, area_id='1'))
            cls.interfaces.append(
                Interface.objects.create(name='Eth1', device=device, type='virtual')
            )
        cls.address = IPAddress.objects.create(
            address='10.0.0.1/30', assigned_object=cls.interfaces[1]
        )
        cls.policy = RoutePolicy.objects.create(name='TO-OSPF')

    def _save(self, form_class, **row):
        form = form_class(data=row)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        return form.save()

    def _ospf_interface(self, device_index=1):
        return OSPFInterface.objects.create(
            instance=self.instances[device_index],
            area=self.areas[device_index],
            interface=self.interfaces[device_index],
            network_type='non_broadcast',
        )

    def test_interface_resolves_everything_on_its_device(self):
        obj = self._save(
            OSPFInterfaceImportForm,
            device='Device 2',
            instance='Main',
            area='1',
            interface='Eth1',
            network_type='point_to_point',
        )
        self.assertEqual(obj.instance, self.instances[1])
        self.assertEqual(obj.area, self.areas[1])
        self.assertEqual(obj.interface, self.interfaces[1])
        self.assertEqual(obj.hello_interval, 10)  # the default, left out of the CSV

    def test_network(self):
        self._ospf_interface()
        obj = self._save(
            OSPFNetworkImportForm,
            device='Device 2',
            ospf_interface='Eth1',
            ip_address='10.0.0.1/30',
        )
        self.assertEqual(obj.ospf_interface.instance, self.instances[1])
        self.assertEqual(obj.ip_address, self.address)

    def test_neighbor(self):
        self._ospf_interface()
        obj = self._save(
            OSPFNeighborImportForm,
            device='Device 2',
            ospf_interface='Eth1',
            ip_address='10.0.0.2',
            priority='1',
        )
        self.assertEqual(obj.priority, 1)
        self.assertEqual(OSPFNeighbor.objects.count(), 1)

    def test_redistribution(self):
        obj = self._save(
            OSPFRedistributionImportForm,
            device='Device 2',
            instance='Main',
            protocol='static',
            metric='10',
            route_policy='TO-OSPF',
        )
        self.assertEqual(obj.instance, self.instances[1])
        self.assertEqual(obj.route_policy, self.policy)
        self.assertEqual(OSPFRedistribution.objects.count(), 1)

    def test_ospf_cannot_redistribute_into_ospf(self):
        # OSPF never takes OSPF routes on the same device, VRF and address family:
        # the only OSPF instance of that VRF is the one itself (#528)
        OSPFInstance.objects.create(
            name='Other',
            device=self.devices[1],
            router_id='9.9.9.9',
            vrf=VRF.objects.create(name='VRF 1'),
        )
        form = OSPFRedistributionImportForm(
            data={
                'device': 'Device 2',
                'instance': 'Main',
                'protocol': 'ospf',
                'ospf_source': 'Other',
                'ospf_match': 'internal,external-1',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('ospf_source', form.errors)

    def test_virtual_link(self):
        obj = self._save(
            OSPFVirtualLinkImportForm,
            device='Device 2',
            instance='Main',
            transit_area='1',
            remote_router_id='5.5.5.5',
        )
        self.assertEqual(obj.transit_area, self.areas[1])
        self.assertEqual(OSPFVirtualLink.objects.count(), 1)

    def test_summary_address(self):
        obj = self._save(
            OSPFSummaryAddressImportForm,
            device='Device 2',
            instance='Main',
            prefix='10.0.0.0/8',
        )
        self.assertEqual(obj.instance, self.instances[1])
        self.assertEqual(OSPFSummaryAddress.objects.count(), 1)

    def test_area_range(self):
        obj = self._save(
            OSPFAreaRangeImportForm,
            device='Device 2',
            instance='Main',
            area='1',
            prefix='10.0.0.0/8',
        )
        self.assertEqual(obj.area, self.areas[1])
        self.assertEqual(OSPFAreaRange.objects.count(), 1)

    def test_prefix_sid(self):
        obj = self._save(
            OSPFPrefixSIDImportForm,
            device='Device 2',
            instance='Main',
            prefix='10.255.0.2/32',
            sid='2',
            node_sid='true',
        )
        self.assertEqual(obj.instance, self.instances[1])
        self.assertEqual(OSPFPrefixSID.objects.count(), 1)

    def test_unknown_names_are_errors(self):
        form = OSPFSummaryAddressImportForm(
            data={'device': 'Device 2', 'instance': 'Nope', 'prefix': '10.0.0.0/8'}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('instance', form.errors)
