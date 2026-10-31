from netbox_routing_plugin.tests.eigrp.test_filtersets import *
from netbox_routing_plugin.tests.isis.test_filtersets import *
from netbox_routing_plugin.tests.ospf.test_filtersets import *
from netbox_routing_plugin.tests.static.test_filtersets import *

__all__ = (
    'StaticRouteTestCase',
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
    'ISISInstanceFilterSetTestCase',
    'ISISAttributeFilterSetTestCase',
    'ISISRoutingFilterSetTestCase',
    'ISISInterfaceFilterSetTestCase',
    'ISISSettingFilterSetTestCase',
    'ISISSRv6LocatorFilterSetTestCase',
    'EIGRPRouterTestCase',
    'EIGRPAddressFamilyTestCase',
    'EIGRPNetworkTestCase',
    'EIGRPInterfaceTestCase',
)
