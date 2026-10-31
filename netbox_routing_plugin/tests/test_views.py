from netbox_routing_plugin.tests.eigrp.test_views import *
from netbox_routing_plugin.tests.isis.test_views import *
from netbox_routing_plugin.tests.ospf.test_views import *
from netbox_routing_plugin.tests.static.test_views import *

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
