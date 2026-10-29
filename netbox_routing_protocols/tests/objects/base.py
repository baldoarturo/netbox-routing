from netbox_routing_protocols.models.objects import *

__all__ = (
    'ParentObjectMixin',
    'ASPathMixin',
    'PrefixListMixin',
    'RoutePolicyMixin',
)


class ParentObjectMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()


class ASPathMixin:
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name=f'{ASPath._meta.verbose_name}')


class PrefixListMixin:
    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList.objects.create(
            name=f'{PrefixList._meta.verbose_name}'
        )


class RoutePolicyMixin:
    @classmethod
    def setUpTestData(cls):
        cls.route_policy = RoutePolicy.objects.create(
            name=f'{RoutePolicy._meta.verbose_name}'
        )
