from netbox.forms import NetBoxModelFilterSetForm
from netbox_routing_protocols.models.objects import *

__all__ = (
    'PrefixListFilterForm',
    'PrefixListEntryFilterForm',
    'RouteMapFilterForm',
    'RouteMapEntryFilterForm',
    'ASPathFilterForm',
    'ASPathEntryFilterForm',
)


class PrefixListFilterForm(NetBoxModelFilterSetForm):
    model = PrefixList


class PrefixListEntryFilterForm(NetBoxModelFilterSetForm):
    model = PrefixListEntry


class RouteMapFilterForm(NetBoxModelFilterSetForm):
    model = RouteMap


class RouteMapEntryFilterForm(NetBoxModelFilterSetForm):
    model = RouteMapEntry


class ASPathFilterForm(NetBoxModelFilterSetForm):
    model = ASPath


class ASPathEntryFilterForm(NetBoxModelFilterSetForm):
    model = ASPathEntry
