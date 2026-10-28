# from django.urls import reverse
# from netaddr.ip import IPAddress
# from rest_framework import status

# from dcim.models import Interface
# from ipam.models import VRF
from utilities.testing import APIViewTestCases  # , APITestCase, create_test_device

# from netbox_routing_protocols.models import EIGRPRouter, EIGRPAddressFamily, EIGRPNetwork, EIGRPInterface
# from netbox_routing_protocols.tests.base import IPAddressFieldMixin

__all__ = (
    'EIGRPRouterTestCase',
    'EIGRPAddressFamilyTestCase',
    'EIGRPNetworkTestCase',
    'EIGRPInterfaceTestCase',
)


class EIGRPRouterTestCase(APIViewTestCases):
    pass


class EIGRPAddressFamilyTestCase(APIViewTestCases):
    pass


class EIGRPNetworkTestCase(APIViewTestCases):
    pass


class EIGRPInterfaceTestCase(APIViewTestCases):
    pass
