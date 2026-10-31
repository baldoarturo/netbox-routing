from netbox_routing_plugin.tests.eigrp.test_forms import *
from netbox_routing_plugin.tests.isis.test_forms import *
from netbox_routing_plugin.tests.ospf.test_forms import *
from netbox_routing_plugin.tests.static.test_forms import *

__all__ = (
    'StaticRouteTestCase',
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
    'ISISBulkEditFieldsetTestCase',
    'ISISInstanceFormTestCase',
    'ISISInterfaceFormTestCase',
    'ISISInterfaceImportFormTestCase',
    'ISISInstanceImportFormTestCase',
    'ISISSettingFormInitialTestCase',
    'EIGRPRouterTestCase',
    'EIGRPAddressFamilyTestCase',
    'EIGRPNetworkTestCase',
    'EIGRPInterfaceTestCase',
)
