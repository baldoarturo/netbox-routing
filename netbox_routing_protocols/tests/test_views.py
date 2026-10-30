from netbox_routing_protocols.tests.eigrp.test_views import *
from netbox_routing_protocols.tests.isis.test_views import *
from netbox_routing_protocols.tests.ospf.test_views import *
from netbox_routing_protocols.tests.static.test_views import *

__all__ = (
    'StaticRouteTestCase',
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
    'ISISInstanceViewTestCase',
    'ISISInterfaceViewTestCase',
    'ISISBulkEditViewsTestCase',
    'ISISViewExportsTestCase',
    # 'EIGRPRouterTestCase',
    # 'EIGRPAddressFamilyTestCase',
    # 'EIGRPNetworkTestCase',
    # 'EIGRPInterfaceTestCase',
)
