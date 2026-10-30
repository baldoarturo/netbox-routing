"""
Sample communities and community lists of Cogent (AS174), Hurricane Electric (AS6939)
and AS3549, to try the community module in the dev database. Idempotent: running it again
only adds what is missing.

    cd <netbox>/netbox
    NETBOX_CONFIGURATION=configuration_dev PYTHONPATH=<repo>/dev:<repo> \
    PLUGIN_MODULE=netbox_routing_protocols PLUGIN_DEV_DB=netbox_routing_protocols_dev \
        ../venv/bin/python manage.py shell < <repo>/dev/samples/carrier_communities.py

Source: https://bgp.tools/communities/174, /6939 and /3549 (descriptions as they list them);
6939:666 is documented by Hurricane Electric at https://www.he.net/adm/blackhole.html.
The well-known values are in RFC 1997, RFC 7999 and RFC 8326.
"""

from django.db import transaction

from ipam.models import Role
from netbox_routing_protocols.models.community import (
    Community,
    CommunityList,
    CommunityListEntry,
)
from tenancy.models import Tenant

TENANTS = {
    'Cogent': 'cogent',
    'Hurricane Electric': 'hurricane-electric',
    'GTT / Level3 (AS3549)': 'as3549',
}
ROLES = {
    'Local preference': 'local-preference',
    'Export control': 'export-control',
    'Prepend': 'prepend',
    'Route origin': 'route-origin',
    'Blackhole': 'blackhole',
}

# (tenant, role, value, description)
COGENT, HE, GTT = 'Cogent', 'Hurricane Electric', 'GTT / Level3 (AS3549)'
LP, EXPORT, PREPEND, ORIGIN = (
    'Local preference',
    'Export control',
    'Prepend',
    'Route origin',
)
COMMUNITIES = [
    (
        COGENT,
        LP,
        '174:10',
        'Set customer route local preference to 10 (least preferred)',
    ),
    (COGENT, LP, '174:70', 'Set customer route local preference to 70 (below peers)'),
    (
        COGENT,
        LP,
        '174:120',
        'Set customer route local preference to 120 (below customer default)',
    ),
    (
        COGENT,
        LP,
        '174:125',
        'Set customer route local preference to 125 (below customer default)',
    ),
    (
        COGENT,
        LP,
        '174:135',
        'Set customer route local preference to 135 (above customer default)',
    ),
    (
        COGENT,
        LP,
        '174:140',
        'Set customer route local preference to 140 (above customer default)',
    ),
    (
        COGENT,
        EXPORT,
        '174:990',
        'Global - Do not send route to BGP customers, or peers',
    ),
    (COGENT, EXPORT, '174:991', 'Global - Do not send route to peers'),
    (COGENT, EXPORT, '174:3000', 'Do not announce to peers (equivalent to 174:991)'),
    (COGENT, EXPORT, '174:980', 'Do not export outside AS174 in EU (Europe) Region'),
    (
        COGENT,
        EXPORT,
        '174:970',
        'Do not export outside AS174 in NA (North America) Region',
    ),
    (
        COGENT,
        EXPORT,
        '174:960',
        'Do not export outside AS174 in AP (Asia Pacific) Region',
    ),
    (COGENT, PREPEND, '174:3001', 'Prepend 174 1 time to peers'),
    (COGENT, PREPEND, '174:3002', 'Prepend 174 2 times to peers'),
    (COGENT, PREPEND, '174:3003', 'Prepend 174 3 times to peers'),
    (
        COGENT,
        ORIGIN,
        '174:21000',
        'Route is learned from NA (North America) non-customer',
    ),
    (COGENT, ORIGIN, '174:21001', 'Route is NA internal or customer route'),
    (COGENT, ORIGIN, '174:21100', 'Route is learned from EU (Europe) non-customer'),
    (COGENT, ORIGIN, '174:21101', 'Route is an EU internal or customer route'),
    (
        COGENT,
        ORIGIN,
        '174:21200',
        'Route is learned from AP (Asia Pacific) non-customer',
    ),
    (COGENT, ORIGIN, '174:21201', 'Route is an AP internal or customer route'),
    (HE, ORIGIN, '6939:1000', 'Customer Route'),
    (HE, ORIGIN, '6939:9001', 'Learned in North America'),
    (HE, ORIGIN, '6939:9002', 'Learned in EU'),
    (HE, ORIGIN, '6939:9003', 'Learned in APAC'),
    (HE, ORIGIN, '6939:9004', 'Learned in Africa'),
    (HE, ORIGIN, '6939:9005', 'Learned in South America'),
    (HE, ORIGIN, '6939:9006', 'Learned in Oceania'),
    (HE, ORIGIN, '6939:9007', 'Learned in Middle East'),
    (HE, ORIGIN, '6939:8250', 'Learned in France'),
    (HE, ORIGIN, '6939:8276', 'Learned in Germany'),
    (HE, ORIGIN, '6939:8528', 'Learned in Netherlands'),
    (HE, ORIGIN, '6939:8826', 'Learned in United Kingdom'),
    (HE, ORIGIN, '6939:8840', 'Learned in United States of America'),
    (
        HE,
        'Blackhole',
        '6939:666',
        'Drop traffic for the prefix on the Hurricane core (customer blackholing)',
    ),
    (GTT, LP, '3549:100', 'Set BGP Local Pref to 100 (less than peer routes)'),
    (GTT, LP, '3549:200', 'Set BGP Local Pref to 202 (greater than peer routes)'),
    (GTT, LP, '3549:275', 'Set BGP Local Pref to 275 (greater than peer routes)'),
    (GTT, LP, '3549:300', 'Set BGP Local Pref to 300 (equal to default)'),
    (GTT, LP, '3549:350', 'Set BGP Local Pref to 350 (greater than default)'),
]

# well-known communities have no tenant (RFC 1997, RFC 7999, RFC 8326)
WELL_KNOWN = [
    'no-export',
    'no-advertise',
    'no-export-subconfed',
    'blackhole',
    'graceful-shutdown',
]

# (list name, tenant, description, [(action, community value)]); sequence 10, 20, ...
P, D = 'permit', 'deny'
LISTS = [
    (
        'COGENT-CUSTOMER-LOCALPREF',
        COGENT,
        'Local preference communities Cogent accepts from customers',
        [(P, f'174:{n}') for n in (10, 70, 120, 125, 135, 140)],
    ),
    (
        'COGENT-EXPORT-CONTROL',
        COGENT,
        'Do not announce to customers or peers',
        [(P, '174:990'), (P, '174:991'), (P, '174:3000')],
    ),
    (
        'COGENT-PREPEND',
        COGENT,
        'Prepend 1 to 3 times to peers',
        [(P, f'174:{n}') for n in (3001, 3002, 3003)],
    ),
    (
        'COGENT-LEARNED-NA',
        COGENT,
        'Routes Cogent learned in North America',
        [(P, '174:21000'), (P, '174:21001')],
    ),
    (
        'COGENT-LEARNED-EU',
        COGENT,
        'Routes Cogent learned in Europe',
        [(P, '174:21100'), (P, '174:21101')],
    ),
    (
        'HE-CUSTOMER-ROUTES',
        HE,
        'Routes Hurricane Electric learned from its customers',
        [(P, '6939:1000')],
    ),
    (
        'HE-EUROPE-COUNTRIES',
        HE,
        'Routes learned in the main European countries',
        [(P, f'6939:{n}') for n in (8250, 8276, 8528, 8826)],
    ),
    ('HE-BLACKHOLE', HE, 'Customer blackholing', [(P, '6939:666')]),
    (
        'AS3549-LOCALPREF',
        GTT,
        'Local preference communities of AS3549',
        [(P, f'3549:{n}') for n in (100, 200, 275, 300, 350)],
    ),
    (
        'WELL-KNOWN-FILTER',
        None,
        'Do not propagate routes marked no-export or no-advertise, accept blackhole',
        [(D, '65535:65281'), (D, '65535:65282'), (D, '65535:65283'), (P, '65535:666')],
    ),
]


@transaction.atomic
def load():
    tenants = {
        name: Tenant.objects.get_or_create(slug=slug, defaults={'name': name})[0]
        for name, slug in TENANTS.items()
    }
    roles = {
        name: Role.objects.get_or_create(slug=slug, defaults={'name': name})[0]
        for name, slug in ROLES.items()
    }
    made = {'communities': 0, 'lists': 0, 'entries': 0}

    def community(value, tenant=None, role=None, description=''):
        normal = Community(community=value)
        normal.clean()  # the stored (normal) form of the value
        found = Community.objects.filter(
            community=normal.community, tenant=tenant
        ).first()
        if found:
            return found
        item = Community(
            community=value, tenant=tenant, role=role, description=description
        )
        item.full_clean()
        item.save()
        made['communities'] += 1
        return item

    for tenant, role, value, description in COMMUNITIES:
        community(value, tenants[tenant], roles[role], description)
    for value in WELL_KNOWN:
        community(value)

    for name, tenant, description, entries in LISTS:
        lst = CommunityList.objects.filter(name__iexact=name).first()
        if lst is None:
            lst = CommunityList(
                name=name, tenant=tenants.get(tenant), description=description
            )
            lst.full_clean()
            lst.save()
            made['lists'] += 1
        for sequence, (action, value) in enumerate(entries, start=1):
            item = community(
                value, None if value.startswith('65535:') else tenants.get(tenant)
            )
            _, created = CommunityListEntry.objects.get_or_create(
                community_list=lst,
                sequence=sequence * 10,
                defaults={'community': item, 'action': action},
            )
            made['entries'] += created
    print(
        'Created: {communities} communities, {lists} lists, {entries} entries'.format(
            **made
        )
    )


load()
