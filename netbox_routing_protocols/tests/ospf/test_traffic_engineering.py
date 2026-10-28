from django.core.exceptions import ValidationError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing_protocols.models import OSPFArea, OSPFInstance, OSPFInterface

__all__ = ('OSPFTrafficEngineeringTestCase',)


class OSPFTrafficEngineeringTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.interface = Interface.objects.create(
            name='Interface 1', device=cls.device, type='virtual'
        )
        cls.instance = OSPFInstance.objects.create(
            name='Instance 1', device=cls.device, router_id='1.1.1.1'
        )
        cls.area = OSPFArea.objects.create(instance=cls.instance, area_id='1')

    def _enable(self, instance_opaque=True, area_te=True):
        OSPFInstance.objects.filter(pk=self.instance.pk).update(
            opaque_capability=instance_opaque
        )
        OSPFArea.objects.filter(pk=self.area.pk).update(traffic_engineering=area_te)
        self.instance.refresh_from_db()
        self.area.refresh_from_db()

    def _interface(self, **kwargs):
        return OSPFInterface(
            instance=self.instance, area=self.area, interface=self.interface, **kwargs
        )

    def _assert_invalid(self, obj, field):
        with self.assertRaises(ValidationError) as cm:
            obj.full_clean()
        self.assertIn(field, cm.exception.error_dict)

    def test_everything_is_off_by_default(self):
        self.assertFalse(self.instance.opaque_capability)
        self.assertIsNone(self.instance.te_router_address)
        self.assertFalse(self.area.traffic_engineering)
        interface = self._interface()
        interface.full_clean()
        self.assertIsNone(interface.te_metric)

    def test_the_router_address_is_a_unicast_address_and_needs_opaque_lsas(self):
        self.instance.opaque_capability = True
        self.instance.te_router_address = '10.255.0.1'
        self.instance.full_clean()
        for address in ('127.0.0.1', '224.0.0.5', '0.0.0.0'):
            with self.subTest(address=address):
                self.instance.te_router_address = address
                self._assert_invalid(self.instance, 'te_router_address')
        self.instance.te_router_address = '10.255.0.1'
        self.instance.opaque_capability = False
        self._assert_invalid(self.instance, 'te_router_address')

    def test_the_area_needs_the_opaque_lsas_of_the_instance(self):
        self.area.traffic_engineering = True
        self._assert_invalid(self.area, 'traffic_engineering')
        self._enable(instance_opaque=True, area_te=False)
        self.area.traffic_engineering = True
        self.area.full_clean()

    def test_the_opaque_lsas_cannot_be_removed_while_an_area_uses_them(self):
        self._enable()
        self.instance.opaque_capability = False
        self._assert_invalid(self.instance, 'opaque_capability')

    def test_interface_attributes_need_traffic_engineering_in_the_area(self):
        self._enable(area_te=False)
        for field, value in (
            ('te_metric', 10),
            ('te_max_reservable_bandwidth', 1000000),
            ('te_admin_group', 5),
        ):
            with self.subTest(field=field):
                self._assert_invalid(self._interface(**{field: value}), field)
        self._enable()
        self._interface(
            te_metric=10, te_max_reservable_bandwidth=1000000, te_admin_group=5
        ).full_clean()

    def test_interface_attribute_limits(self):
        self._enable()
        for field, valid, invalid in (
            ('te_metric', (0, 4294967295), 4294967296),
            ('te_admin_group', (0, 4294967295), 4294967296),
            ('te_max_reservable_bandwidth', (1,), 0),
        ):
            with self.subTest(field=field):
                for value in valid:
                    self._interface(**{field: value}).full_clean()
                self._assert_invalid(self._interface(**{field: invalid}), field)

    def test_traffic_engineering_cannot_be_disabled_while_interfaces_use_it(self):
        self._enable()
        OSPFInterface.objects.create(
            instance=self.instance,
            area=self.area,
            interface=self.interface,
            te_metric=5,
        )
        self.area.traffic_engineering = False
        self._assert_invalid(self.area, 'traffic_engineering')
