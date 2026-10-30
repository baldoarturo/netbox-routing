from netbox_routing_protocols.tests.eigrp.test_filtersets import *
from netbox_routing_protocols.tests.isis.test_filtersets import *
from netbox_routing_protocols.tests.ospf.test_filtersets import *
from netbox_routing_protocols.tests.static.test_filtersets import *

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
