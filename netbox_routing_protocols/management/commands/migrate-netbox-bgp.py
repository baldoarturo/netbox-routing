import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix
from netbox.context_managers import event_tracking
from netbox_routing_protocols.models.bgp import *
from netbox_routing_protocols.helpers import community as community_helpers
from netbox_routing_protocols.models.community import *
from netbox_routing_protocols.models.objects import *
from users.models import User
from utilities.request import NetBoxFakeRequest


def route_policy_settings(action, set_actions):
    """
    The set_actions of a netbox-bgp rule as fields of a route policy entry, and what could
    not be mapped (a key without a field, a bad value, anything on a deny rule, which only
    denies): (fields, unmapped dict).
    """
    fields, unmapped = {}, {}
    numbers = {
        'local_preference': ('set_local_preference', 4294967295),
        'metric': ('set_metric', 4294967295),
        'tag': ('set_tag', 4294967295),
        'weight': ('set_weight', 65535),
    }
    for key, value in (set_actions or {}).items():
        field = None
        if action == 'permit':
            if key in numbers and str(value).isdigit():
                if int(value) <= numbers[key][1]:
                    field = numbers[key][0], int(value)
            elif key == 'origin' and value in ('igp', 'egp', 'incomplete'):
                field = 'set_origin', value
            elif key in ('as_path_prepend', 'prepend'):
                asns = value.split() if isinstance(value, str) else value
                if isinstance(asns, list) and all(str(a).isdigit() for a in asns):
                    field = 'set_aspath_prepend', [int(a) for a in asns]
        if field:
            fields[field[0]] = field[1]
        else:
            unmapped[key] = value
    return fields, unmapped


def pks_from_through_relationship(item, column):
    local_class = item.__class__
    local_column = getattr(local_class, column)
    remote_class = local_column.rel.related_model

    local_field = f'{local_class._meta.model_name}_id'
    remote_field = f'{remote_class._meta.model_name}_id'

    filter = {f'{local_field}': item.pk}

    pks = []
    for row in local_column.through.objects.filter(**filter):
        pks.append(getattr(row, f'{remote_field}'))

    return pks


class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument('--plugin-version', dest='version', help="Version of Netbox-BGP")

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username='NetBox BGP Migration')
        except User.DoesNotExist:
            user = User(username='NetBox BGP Migration')
            user.save()

        request = NetBoxFakeRequest(
            {
                'META': {},
                'POST': {},
                'GET': {},
                'FILES': {},
                'user': user,
                'path': '',
                'id': uuid.uuid4(),
            }
        )

        from netbox_routing_protocols.models import netbox_bgp

        try:
            with transaction.atomic(), event_tracking(request):
                mapping = {
                    'community': {},
                    'community_list': {},
                    'community_list_entry': {},
                    'prefix_list': {},
                    'prefix_list_entry': {},
                    'aspath': {},
                    'aspath_entry': {},
                    'route_policy': {},
                    'route_policy_entry': {},
                    'router': {},
                    'peer_group': {},
                }

                # One BGP instance per device (the global table); the sessions of a device
                # whose local ASN differs from the instance's keep it as the peer's local AS
                for item in netbox_bgp.BGPSession.objects.all():
                    if not item.device or not item.local_as:
                        raise Exception(
                            _('Every BGP session needs a device and a local ASN')
                        )
                    if item.device.pk in mapping['router']:
                        continue
                    router = BGPInstance(
                        name=item.device.name,
                        device=item.device,
                        asn=item.local_as,
                        description='Migrated from NetBox BGP',
                    )
                    router.full_clean()
                    router.save()
                    mapping['router'][item.device.pk] = router
                    for address_family in ('ipv4-unicast', 'ipv6-unicast'):
                        af = BGPAddressFamily(
                            instance=router, address_family=address_family
                        )
                        af.full_clean()
                        af.save()

                for item in netbox_bgp.Community.objects.all():
                    try:
                        # communities are stored in their normal form
                        entry = Community.objects.get(
                            community=community_helpers.normalize(item.value),
                            tenant=item.tenant,
                        )
                        if not mapping['community'].get(item.pk):
                            mapping['community'][item.pk] = entry
                    except Community.DoesNotExist:
                        entry = Community(
                            community=item.value,
                            status=item.status,
                            role=item.role,
                            tenant=item.tenant,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['community'][item.pk] = entry

                for item in netbox_bgp.CommunityList.objects.all():
                    try:
                        entry = CommunityList.objects.get(name__iexact=item.name)
                        if not mapping['community_list'].get(item.pk):
                            mapping['community_list'][item.pk] = entry
                    except CommunityList.DoesNotExist:
                        # the list takes the type of its communities
                        kinds = {
                            mapping['community'][rule.community.pk].type
                            for rule in item.commlistrules.all()
                        }
                        entry = CommunityList(
                            name=item.name,
                            type=kinds.pop() if len(kinds) == 1 else 'standard',
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['community_list'][item.pk] = entry

                for item in netbox_bgp.CommunityListRule.objects.all():
                    community = mapping['community'][item.community.pk]
                    community_list = mapping['community_list'][item.community_list.pk]

                    try:
                        entry = CommunityListEntry.objects.get(
                            community_list=community_list, community=community
                        )
                        if not mapping['community_list_entry'].get(item.pk):
                            mapping['community_list_entry'][item.pk] = entry
                    except CommunityListEntry.MultipleObjectsReturned:
                        for entry in CommunityListEntry.objects.filter(
                            community_list=community_list, community=community
                        ):
                            if not mapping['community_list_entry'].get(item.pk):
                                mapping['community_list_entry'][item.pk] = entry
                    except CommunityListEntry.DoesNotExist:
                        entry = CommunityListEntry(
                            community_list=community_list,
                            sequence=community_helpers.next_sequence(community_list),
                            action=item.action,
                            community=community,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['community_list_entry'][item.pk] = entry

                for item in netbox_bgp.PrefixList.objects.all():
                    family = 4 if item.family == 'ipv4' else 6
                    try:
                        entry = PrefixList.objects.get(name=item.name)
                        if not mapping['prefix_list'].get(item.pk):
                            mapping['prefix_list'][item.pk] = entry
                    except PrefixList.DoesNotExist:
                        entry = PrefixList(
                            name=item.name,
                            family=family,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['prefix_list'][item.pk] = entry

                for item in netbox_bgp.PrefixListRule.objects.all():
                    prefix_list = mapping['prefix_list'][item.prefix_list.pk]
                    prefix = None
                    if item.prefix:
                        prefix = item.prefix
                    elif item.prefix_custom:
                        # Prefixes are declared in IPAM only
                        prefix = Prefix.objects.filter(
                            prefix=item.prefix_custom
                        ).first()
                        if prefix is None:
                            prefix = Prefix(prefix=item.prefix_custom)
                            prefix.full_clean()
                            prefix.save()

                    try:
                        entry = PrefixListEntry.objects.get(
                            prefix_list=prefix_list, sequence=item.index
                        )
                        if not mapping['prefix_list_entry'].get(item.pk):
                            mapping['prefix_list_entry'][item.pk] = entry
                    except PrefixListEntry.DoesNotExist:
                        entry = PrefixListEntry(
                            prefix_list=prefix_list,
                            sequence=item.index,
                            action=item.action,
                            prefix=prefix,
                            ge=item.ge,
                            le=item.le,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['prefix_list_entry'][item.pk] = entry

                for item in netbox_bgp.ASPathList.objects.all():
                    try:
                        entry = ASPath.objects.get(name=item.name)
                        if not mapping['aspath'].get(item.pk):
                            mapping['aspath'][item.pk] = entry
                    except ASPath.DoesNotExist:
                        entry = ASPath(
                            name=item.name,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['aspath'][item.pk] = entry

                # The entries that exist, by AS-path and sequence: one query, not one per rule
                existing_entries = {
                    (entry.aspath_id, entry.sequence): entry
                    for entry in ASPathEntry.objects.all()
                }
                for item in netbox_bgp.ASPathListRule.objects.all():
                    aspath = mapping['aspath'][item.aspath_list_id]
                    entry = existing_entries.get((aspath.pk, item.index))
                    if entry:
                        if not mapping['aspath_entry'].get(item.pk):
                            mapping['aspath_entry'][item.pk] = entry
                    else:
                        entry = ASPathEntry(
                            aspath=aspath,
                            sequence=item.index,
                            action=item.action,
                            pattern=item.pattern,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        existing_entries[(aspath.pk, item.index)] = entry
                        mapping['aspath_entry'][item.pk] = entry

                for item in netbox_bgp.RoutingPolicy.objects.all():
                    #
                    # Weight is discarded
                    #
                    try:
                        entry = RoutePolicy.objects.get(name=item.name)
                        if not mapping['route_policy'].get(item.pk):
                            mapping['route_policy'][item.pk] = entry
                    except RoutePolicy.DoesNotExist:
                        entry = RoutePolicy(
                            name=item.name,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        mapping['route_policy'][item.pk] = entry

                for item in netbox_bgp.RoutingPolicyRule.objects.all():
                    route_policy = mapping['route_policy'][item.routing_policy.pk]
                    community_list = [
                        mapping['community_list'][cl].pk
                        for cl in item.match_community_list.values_list(
                            'communitylist_id', flat=True
                        )
                    ]
                    aspath = [
                        mapping['aspath'][asp].pk
                        for asp in item.match_aspath_list.values_list(
                            'aspathlist_id', flat=True
                        )
                    ]
                    prefix_list = [
                        mapping['prefix_list'][pl].pk
                        for pl in item.match_ip_address.values_list(
                            'prefixlist_id', flat=True
                        )
                    ]
                    prefix_list.extend(
                        [
                            mapping['prefix_list'][pl].pk
                            for pl in item.match_ipv6_address.values_list(
                                'prefixlist_id', flat=True
                            )
                        ]
                    )
                    set_fields, unmapped = route_policy_settings(
                        item.action, item.set_actions
                    )
                    if item.match_custom or unmapped:
                        # The custom match and the settings that have no field are lost
                        print(
                            f'Route policy {route_policy.name} rule {item.index}: '
                            f'not migrated: {item.match_custom or ""} {unmapped or ""}'
                        )
                    try:
                        entry = RoutePolicyEntry.objects.get(
                            route_policy=route_policy, sequence=item.index
                        )
                        if not mapping['route_policy_entry'].get(item.pk):
                            mapping['route_policy_entry'][item.pk] = entry
                    except RoutePolicyEntry.DoesNotExist:
                        entry = RoutePolicyEntry(
                            route_policy=route_policy,
                            sequence=item.index,
                            action=item.action,
                            **set_fields,
                            description=item.description,
                            comments=item.comments,
                        )
                        entry.full_clean()
                        entry.save()
                        entry.match_prefix_list.set(prefix_list)
                        entry.match_community_list.set(community_list)
                        entry.match_aspath.set(aspath)
                        mapping['route_policy_entry'][item.pk] = entry

                def peer_group_of(item, router):
                    """The peer group of a session in the instance of its device (a
                    netbox-bgp group is global: one copy per instance that uses it)"""
                    key = (item.peer_group.pk, router.pk)
                    if key in mapping['peer_group']:
                        return mapping['peer_group'][key]
                    group = item.peer_group
                    entry = BGPPeerGroup(
                        name=group.name,
                        instance=router,
                        description=group.description,
                        comments=group.comments,
                    )
                    entry.full_clean()
                    entry.save()
                    mapping['peer_group'][key] = entry
                    if (
                        group.import_policies.count() > 1
                        or group.export_policies.count() > 1
                    ):
                        print(
                            f'Only 1 import or export policy is supported per peer group. '
                            f'{group.name} has {group.import_policies.count()} import and '
                            f'{group.export_policies.count()} export policies; only the '
                            f'first of each is applied.'
                        )
                    import_policy = group.import_policies.first()
                    export_policy = group.export_policies.first()
                    for address_family in router.address_families.all():
                        peer_af = BGPPeerAddressFamily(
                            peer_group=entry,
                            address_family=address_family,
                            routepolicy_in=(
                                mapping['route_policy'].get(
                                    import_policy.routingpolicy.pk
                                )
                                if import_policy
                                else None
                            ),
                            routepolicy_out=(
                                mapping['route_policy'].get(
                                    export_policy.routingpolicy.pk
                                )
                                if export_policy
                                else None
                            ),
                        )
                        peer_af.full_clean()
                        peer_af.save()
                    return entry

                for item in netbox_bgp.BGPSession.objects.all():
                    if (
                        item.import_policies.count() > 1
                        or item.export_policies.count() > 1
                    ):
                        print(
                            f'Only 1 import or export policy is supported per peer. '
                            f'{item} has {item.import_policies.count()} import and '
                            f'{item.export_policies.count()} export policies; only the '
                            f'first of each is applied.'
                        )
                    router = mapping['router'][item.device.pk]

                    if item.local_address.address.version == 4:
                        af = router.address_families.filter(
                            address_family='ipv4-unicast'
                        ).first()
                    else:
                        af = router.address_families.filter(
                            address_family='ipv6-unicast'
                        ).first()
                    try:
                        peer = BGPPeer.objects.get(
                            instance=router, peer=item.remote_address
                        )
                    except BGPPeer.DoesNotExist:
                        peer = BGPPeer(
                            name=item.name,
                            instance=router,
                            source=item.local_address,
                            peer=item.remote_address,
                            remote_as=item.remote_as,
                            local_as=(
                                item.local_as if item.local_as != router.asn else None
                            ),
                            peer_group=(
                                peer_group_of(item, router) if item.peer_group else None
                            ),
                            enabled=True if item.status == 'active' else False,
                            tenant=item.tenant,
                            description=item.description,
                            comments=item.comments,
                        )
                        peer.full_clean()
                        peer.save()

                    import_policy = None
                    export_policy = None
                    if item.import_policies:
                        policy = item.import_policies.first()
                        import_policy = mapping['route_policy'].get(
                            policy.routingpolicy.pk
                        )
                    if item.export_policies:
                        policy = item.export_policies.first()
                        export_policy = mapping['route_policy'].get(
                            policy.routingpolicy.pk
                        )

                    try:
                        peeraf = BGPPeerAddressFamily.objects.get(
                            peer=peer, address_family=af
                        )
                    except BGPPeerAddressFamily.DoesNotExist:
                        peeraf = BGPPeerAddressFamily(
                            peer=peer,
                            address_family=af,
                            routepolicy_in=import_policy,
                            routepolicy_out=export_policy,
                            prefixlist_in=(
                                mapping['prefix_list'].get(item.prefix_list_in.pk)
                                if item.prefix_list_in
                                else None
                            ),
                            prefixlist_out=(
                                mapping['prefix_list'].get(item.prefix_list_out.pk)
                                if item.prefix_list_out
                                else None
                            ),
                        )
                        peeraf.full_clean()
                        peeraf.save()
                # raise Exception('Finished')
        except Exception as e:
            print(f'Last item: {item} ({type(item)})')
            print(f'Exception encountered: {e}; rolling back migration')
            raise e

        user.delete()
