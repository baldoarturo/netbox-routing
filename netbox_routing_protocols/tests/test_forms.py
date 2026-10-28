from netbox_routing_protocols.tests.eigrp.test_forms import *
from netbox_routing_protocols.tests.isis.test_forms import *
from netbox_routing_protocols.tests.ospf.test_forms import *
from netbox_routing_protocols.tests.static.test_forms import *

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
