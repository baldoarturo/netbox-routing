from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from ipam.models import IPAddress
from utilities.testing import APITestCase

from netbox_routing_protocols.models import (
    CommunityList,
    RoutePolicy,
    RoutePolicyEntry,
)


def make_entry(policy, sequence=10, action='permit', **fields):
    return RoutePolicyEntry(
        route_policy=policy, sequence=sequence, action=action, **fields
    )


class RoutePolicyEntryAttributesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.v4 = IPAddress.objects.create(address='192.0.2.1/24')
        cls.v6 = IPAddress.objects.create(address='2001:db8::1/64')
        cls.communities = CommunityList.objects.create(name='Communities')

    def test_every_attribute_is_saved(self):
        entry = make_entry(
            self.policy,
            match_next_hop=self.v6,
            match_metric=100,
            match_origin='igp',
            match_tag=7,
            match_weight=65535,
            set_local_preference=4294967295,
            set_next_hop=self.v4,
            set_aspath_prepend=[65001, 65001, 4200000000],
            set_community_list=self.communities,
            set_community_mode='additive',
            set_metric=10,
            set_metric_mode='subtract',
            set_origin='incomplete',
            set_tag=8,
            set_weight=1,
        )
        entry.full_clean()
        entry.save()
        entry = RoutePolicyEntry.objects.get(pk=entry.pk)
        self.assertEqual(entry.match_next_hop, self.v6)
        self.assertEqual(entry.set_aspath_prepend, [65001, 65001, 4200000000])
        self.assertEqual(entry.aspath_prepend_text, '65001 65001 4200000000')
        self.assertEqual(entry.set_metric_mode, 'subtract')

    def test_the_ranges(self):
        for field, valid, invalid in (
            ('match_metric', 4294967295, 4294967296),
            ('match_tag', 4294967295, 4294967296),
            ('match_weight', 65535, 65536),
            ('set_local_preference', 4294967295, 4294967296),
            ('set_metric', 4294967295, 4294967296),
            ('set_tag', 4294967295, 4294967296),
            ('set_weight', 65535, 65536),
            ('set_aspath_prepend', [4294967295], [4294967296]),
        ):
            with self.subTest(field):
                make_entry(self.policy, **{field: valid}).full_clean()
                with self.assertRaises(ValidationError) as ctx:
                    make_entry(self.policy, **{field: invalid}).full_clean()
                self.assertIn(field, ctx.exception.message_dict)

    def test_an_origin_must_be_a_bgp_origin(self):
        for field in ('match_origin', 'set_origin'):
            with self.subTest(field), self.assertRaises(ValidationError):
                make_entry(self.policy, **{field: 'bogus'}).full_clean()

    def test_a_deny_entry_only_denies(self):
        for field, value in (
            ('set_local_preference', 100),
            ('set_next_hop', self.v4),
            ('set_aspath_prepend', [65001]),
            ('set_community_list', self.communities),
            ('set_metric', 10),
            ('set_origin', 'igp'),
            ('set_tag', 1),
            ('set_weight', 1),
            ('flow_control', 20),
        ):
            with self.subTest(field):
                with self.assertRaises(ValidationError) as ctx:
                    make_entry(
                        self.policy, action='deny', **{field: value}
                    ).full_clean()
                self.assertIn(field, ctx.exception.message_dict)

    def test_a_deny_entry_can_match(self):
        make_entry(
            self.policy,
            action='deny',
            match_next_hop=self.v4,
            match_metric=1,
            match_origin='egp',
            match_tag=2,
            match_weight=3,
        ).full_clean()

    def test_a_community_list_needs_its_mode(self):
        with self.assertRaises(ValidationError) as ctx:
            make_entry(self.policy, set_community_list=self.communities).full_clean()
        self.assertIn('set_community_mode', ctx.exception.message_dict)
        make_entry(
            self.policy,
            set_community_list=self.communities,
            set_community_mode='replace',
        ).full_clean()

    def test_the_metric_mode_defaults_to_set_and_needs_a_metric(self):
        entry = make_entry(self.policy, set_metric=5)
        entry.full_clean()
        self.assertEqual(entry.set_metric_mode, 'set')
        with self.assertRaises(ValidationError) as ctx:
            make_entry(self.policy, set_metric_mode='add').full_clean()
        self.assertIn('set_metric', ctx.exception.message_dict)

    def test_an_ip_address_in_use_cannot_be_deleted(self):
        make_entry(self.policy, match_next_hop=self.v4).save()
        make_entry(self.policy, sequence=20, set_next_hop=self.v6).save()
        for address in (self.v4, self.v6):
            with self.assertRaises(ProtectedError):
                address.delete()

    def test_deleting_the_community_list_clears_the_setting(self):
        entry = make_entry(
            self.policy,
            set_community_list=self.communities,
            set_community_mode='additive',
        )
        entry.save()
        self.communities.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.set_community_list)

    def test_the_json_fields_are_gone(self):
        names = {field.name for field in RoutePolicyEntry._meta.get_fields()}
        self.assertFalse({'match', 'set', 'match_community'} & names)


class RoutePolicyEntryAttributesAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.policy = RoutePolicy.objects.create(name='Policy')
        self.v4 = IPAddress.objects.create(address='192.0.2.1/24')
        self.url = reverse(
            'plugins-api:netbox_routing_protocols-api:routepolicyentry-list'
        )
        self.add_permissions(
            'netbox_routing_protocols.add_routepolicyentry',
            'netbox_routing_protocols.view_routepolicyentry',
        )

    def post(self, **data):
        return self.client.post(
            self.url,
            {'route_policy': self.policy.pk, 'sequence': 10, **data},
            format='json',
            **self.header,
        )

    def test_the_attributes_go_through_the_api(self):
        response = self.post(
            action='permit',
            match_next_hop=self.v4.pk,
            match_origin='igp',
            set_aspath_prepend=[65001, 65001],
            set_origin='egp',
            set_metric=5,
            set_metric_mode='add',
        )
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['set_aspath_prepend'], [65001, 65001])
        self.assertEqual(response.data['match_next_hop']['id'], self.v4.pk)
        self.assertEqual(response.data['match_origin']['value'], 'igp')
        self.assertEqual(response.data['set_metric_mode']['value'], 'add')

    def test_a_deny_entry_with_a_setting_is_refused(self):
        response = self.post(action='deny', set_metric=5)
        self.assertHttpStatus(response, 400)
        self.assertIn('set_metric', response.data)
        self.assertFalse(RoutePolicyEntry.objects.exists())
