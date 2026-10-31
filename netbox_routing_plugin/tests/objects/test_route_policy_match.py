import netaddr
from django.test import TestCase
from django.urls import reverse

from ipam.models import IPAddress, Prefix
from users.models import User

from netbox_routing_plugin.helpers import route_policy as helpers
from netbox_routing_plugin.models import (
    ASPath,
    ASPathEntry,
    Community,
    CommunityList,
    CommunityListEntry,
    PrefixList,
    PrefixListEntry,
    RoutePolicy,
    RoutePolicyEntry,
)


def route(**kwargs):
    if 'prefix' in kwargs:
        kwargs['prefix'] = netaddr.IPNetwork(kwargs['prefix'])
    if 'next_hop' in kwargs:
        kwargs['next_hop'] = netaddr.IPAddress(kwargs['next_hop'])
    return helpers.Route(**kwargs)


class EvaluateTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.other = RoutePolicy.objects.create(name='Other')
        cls.prefixes = PrefixList.objects.create(name='Prefixes', family=4)
        PrefixListEntry.objects.create(
            prefix_list=cls.prefixes,
            sequence=10,
            action='permit',
            prefix=Prefix.objects.create(prefix='10.0.0.0/8'),
            le=24,
        )
        cls.aspath = ASPath.objects.create(name='Path')
        ASPathEntry.objects.create(
            aspath=cls.aspath, sequence=10, action='permit', pattern='^65001 '
        )
        cls.communities = CommunityList.objects.create(name='Communities')
        for sequence, value in ((10, '65001:100'), (20, '65001:200')):
            CommunityListEntry.objects.create(
                community_list=cls.communities,
                sequence=sequence,
                action='permit',
                community=Community.objects.create(community=value),
            )
        cls.hop = IPAddress.objects.create(address='192.0.2.1/24')

    def entry(self, sequence, action='permit', policy=None, **fields):
        return RoutePolicyEntry.objects.create(
            route_policy=policy or self.policy,
            sequence=sequence,
            action=action,
            **fields,
        )

    def decide(self, **attrs):
        outcome = helpers.evaluate(self.policy, route(**attrs))
        deciding = outcome['steps'][-1]['entry']
        return outcome['result'], deciding

    def test_nothing_matches_the_final_deny_decides(self):
        self.entry(10, match_metric=5)
        result, deciding = self.decide(metric=6)
        self.assertEqual(result, 'deny')
        self.assertTrue(deciding.implicit)

    def test_the_first_match_decides(self):
        first = self.entry(10, 'deny', match_metric=5)
        self.entry(20, match_metric=5)
        self.assertEqual(self.decide(metric=5), ('deny', first))

    def test_the_conditions_are_an_and_and_the_objects_of_a_kind_an_or(self):
        entry = self.entry(10, match_origin='igp')
        entry.match_prefix_list.add(self.prefixes)
        self.assertEqual(self.decide(prefix='10.1.0.0/16', origin='igp')[0], 'permit')
        self.assertEqual(self.decide(prefix='10.1.0.0/16', origin='egp')[0], 'deny')
        self.assertEqual(self.decide(prefix='11.0.0.0/8', origin='igp')[0], 'deny')
        other = PrefixList.objects.create(name='None', family=4)
        entry.match_prefix_list.add(other)
        self.assertEqual(self.decide(prefix='10.1.0.0/16', origin='igp')[0], 'permit')

    def test_a_prefix_list_that_denies_is_not_a_match(self):
        denying = PrefixList.objects.create(name='Denying', family=4)
        PrefixListEntry.objects.create(
            prefix_list=denying,
            sequence=10,
            action='deny',
            prefix=Prefix.objects.create(prefix='172.16.0.0/12'),
        )
        self.entry(10).match_prefix_list.add(denying)
        self.assertEqual(self.decide(prefix='172.16.0.0/12')[0], 'deny')

    def test_the_as_path(self):
        self.entry(10).match_aspath.add(self.aspath)
        self.assertEqual(self.decide(as_path='65001 65002')[0], 'permit')
        self.assertEqual(self.decide(as_path='65002 65001')[0], 'deny')

    def test_the_community_list_is_match_all(self):
        self.entry(10).match_community_list.add(self.communities)
        self.assertEqual(self.decide(communities=['65001:100'])[0], 'deny')
        both = ['65001:200', '65001:100', '65002:1']
        self.assertEqual(self.decide(communities=both)[0], 'permit')

    def test_the_next_hop_and_the_numbers(self):
        self.entry(10, match_next_hop=self.hop, match_tag=3, match_weight=7)
        self.assertEqual(
            self.decide(next_hop='192.0.2.1', tag=3, weight=7)[0], 'permit'
        )
        self.assertEqual(self.decide(next_hop='192.0.2.2', tag=3, weight=7)[0], 'deny')
        self.assertEqual(self.decide(next_hop='192.0.2.1', tag=4, weight=7)[0], 'deny')

    def test_a_condition_on_a_field_not_given_is_not_met(self):
        self.entry(10, match_metric=5)
        step = helpers.evaluate(self.policy, route())['steps'][0]
        self.assertFalse(step['matched'])
        self.assertEqual(step['checks'][0][2], 'not given')

    def test_the_settings_of_the_deciding_entry(self):
        self.entry(
            10,
            set_local_preference=200,
            set_aspath_prepend=[65001, 65001],
            set_metric=5,
            set_metric_mode='add',
            set_origin='egp',
        )
        step = helpers.evaluate(self.policy, route())['steps'][0]
        self.assertEqual(
            step['settings'],
            [
                'local-preference 200',
                'as-path prepend 65001 65001',
                'metric add 5',
                'origin egp',
            ],
        )

    def test_a_jump_goes_on_in_the_other_policy_and_does_not_come_back(self):
        self.entry(10, jump_policy=self.other, match_metric=1)
        self.entry(20)
        self.entry(10, 'deny', policy=self.other, match_tag=9)
        self.entry(20, policy=self.other, match_tag=1)
        outcome = helpers.evaluate(self.policy, route(metric=1, tag=9))
        self.assertEqual(outcome['result'], 'deny')
        self.assertEqual(
            [(s['policy'].name, s['entry'].sequence) for s in outcome['steps']],
            [('Policy', 10), ('Other', 10)],
        )
        # the other policy decides, even if the entries after the jump would permit
        outcome = helpers.evaluate(self.policy, route(metric=1, tag=2))
        self.assertEqual(outcome['result'], 'deny')
        self.assertTrue(outcome['steps'][-1]['entry'].implicit)
        self.assertEqual(outcome['steps'][-1]['policy'], self.other)


class RoutePolicyMatchViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        RoutePolicyEntry.objects.create(
            route_policy=cls.policy, sequence=10, action='permit', match_metric=5
        )
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')
        cls.url = reverse('plugins:netbox_routing_plugin:routepolicy_match')

    def setUp(self):
        self.client.force_login(self.user)

    def test_the_page_and_the_results(self):
        self.assertContains(self.client.get(self.url), 'Route Policy Match')
        response = self.client.get(self.url, {'metric': 5})
        self.assertContains(response, 'Policy')
        self.assertContains(response, 'Permit')
        response = self.client.get(self.url, {'metric': 6, 'policy': self.policy.pk})
        self.assertContains(response, 'final')

    def test_htmx_gets_only_the_results(self):
        response = self.client.get(self.url, {'metric': 5}, HTTP_HX_REQUEST='true')
        self.assertNotContains(response, '<html')
        self.assertContains(response, 'Permit')

    def test_a_bad_value_is_an_error_not_a_crash(self):
        for params in (
            {'prefix': 'x'},
            {'next_hop': 'y'},
            {'metric': 'z'},
            {'weight': '70000'},
            {'origin': 'bogus'},
            {'as_path': 'not numbers'},
            {'communities': 'bad'},
        ):
            with self.subTest(params):
                response = self.client.get(self.url, params)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'alert-warning')

    def test_it_needs_the_permission(self):
        user = User.objects.create_user('plain', 'p@example.com', 'x')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
