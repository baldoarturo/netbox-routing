from django.test import TestCase

from netbox_routing_plugin.models import PrefixList, RoutePolicy, RoutePolicyEntry
from netbox_routing_plugin.tables import RoutePolicyEntryTable


class RoutePolicyEntryColumnsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        policy = RoutePolicy.objects.create(name='Policy')
        cls.plain = RoutePolicyEntry.objects.create(
            route_policy=policy, sequence=10, action='permit'
        )
        cls.full = RoutePolicyEntry.objects.create(
            route_policy=policy,
            sequence=20,
            action='permit',
            match_tag=7,
            match_weight=5,
            set_local_preference=200,
            set_weight=9,
        )
        cls.full.match_prefix_list.add(PrefixList.objects.create(name='bogons'))

    def render(self, entry, column):
        table = RoutePolicyEntryTable(RoutePolicyEntry.objects.filter(pk=entry.pk))
        return str(table.rows[0].get_cell(column))

    def test_entry_without_conditions(self):
        self.assertIn('any', self.render(self.plain, 'match'))
        self.assertIn('—', self.render(self.plain, 'set'))

    def test_match_lists_every_condition(self):
        text = self.render(self.full, 'match')
        for part in ('bogons', 'Tag: 7', 'Weight: 5'):
            self.assertIn(part, text)

    def test_set_lists_every_action(self):
        text = self.render(self.full, 'set')
        self.assertIn('local-preference 200', text)
        self.assertIn('weight 9', text)
