from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from users.models import User
from utilities.testing import APITestCase

from netbox_routing_protocols.helpers import route_policy as helpers
from netbox_routing_protocols.models import (
    PrefixList,
    RoutePolicy,
    RoutePolicyEntry,
)
from netbox_routing_protocols.models.objects import IMPLICIT_SEQUENCE


def make_entry(policy, sequence, action='permit', **fields):
    return RoutePolicyEntry.objects.create(
        route_policy=policy, sequence=sequence, action=action, **fields
    )


class FinalDenyTestCase(TestCase):
    """Every route policy ends in a deny of everything, which is data of the model"""

    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')

    def final(self, policy=None):
        return (policy or self.policy).route_policy_entries.get(implicit=True)

    def test_a_new_policy_has_it_at_the_end(self):
        make_entry(self.policy, 10)
        make_entry(self.policy, 20, 'deny')
        entries = list(self.policy.route_policy_entries.all())
        self.assertEqual(
            [(e.sequence, e.action, e.implicit) for e in entries],
            [
                (10, 'permit', False),
                (20, 'deny', False),
                (IMPLICIT_SEQUENCE, 'deny', True),
            ],
        )
        self.assertTrue(entries[-1].matches_everything)

    def test_saving_the_policy_again_does_not_add_another(self):
        self.policy.description = 'Changed'
        self.policy.save()
        self.assertEqual(
            self.policy.route_policy_entries.filter(implicit=True).count(), 1
        )

    def test_it_cannot_be_changed_nor_deleted(self):
        final = self.final()
        with self.assertRaises(ValidationError):
            final.full_clean()
        with self.assertRaises(ProtectedError):
            final.delete()
        self.assertTrue(RoutePolicyEntry.objects.filter(pk=final.pk).exists())

    def test_it_goes_with_the_policy(self):
        policy = RoutePolicy.objects.create(name='Gone')
        policy.delete()
        self.assertFalse(
            RoutePolicyEntry.objects.filter(route_policy_id=policy.pk).exists()
        )

    def test_the_database_allows_only_one_and_in_its_place(self):
        for fields in (
            {'implicit': True, 'sequence': IMPLICIT_SEQUENCE, 'action': 'deny'},
            {'implicit': True, 'sequence': 5, 'action': 'deny'},
            {'implicit': False, 'sequence': 0, 'action': 'permit'},
        ):
            with (
                self.subTest(fields),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                RoutePolicyEntry.objects.create(route_policy=self.policy, **fields)

    def test_the_helpers_leave_it_out(self):
        self.assertEqual(helpers.next_sequence(self.policy), 10)
        make_entry(self.policy, 10)
        self.assertEqual(helpers.next_sequence(self.policy), 20)
        self.assertEqual(helpers.user_entries(self.policy).count(), 1)

    def test_a_policy_full_of_entries_has_no_sequence_left(self):
        make_entry(self.policy, 4294967290)
        with self.assertRaises(ValidationError):
            helpers.next_sequence(self.policy)


class FinalDenyPagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.entry = make_entry(cls.policy, 10)
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')

    def test_the_api_lists_it_last_and_refuses_to_delete_it(self):
        self.client.force_login(self.user)
        url = reverse('plugins-api:netbox_routing_protocols-api:routepolicyentry-list')
        results = self.client.get(url, {'route_policy_id': self.policy.pk}).json()[
            'results'
        ]
        self.assertEqual(
            [(r['sequence'], r['action'], r['implicit']) for r in results],
            [(10, 'permit', False), (IMPLICIT_SEQUENCE, 'deny', True)],
        )
        final = results[-1]
        self.assertEqual(self.client.delete(final['url']).status_code, 409)
        self.assertEqual(
            self.client.patch(
                final['url'], {'action': 'permit'}, content_type='application/json'
            ).status_code,
            400,
        )
        self.assertTrue(RoutePolicyEntry.objects.filter(pk=final['id']).exists())

    def test_the_tab_the_count_and_the_filter(self):
        self.client.force_login(self.user)
        page = self.client.get(self.policy.get_absolute_url() + 'entries/')
        self.assertContains(page, str(IMPLICIT_SEQUENCE))
        response = self.client.get(
            reverse('plugins:netbox_routing_protocols:routepolicy_list')
        )
        row = next(r for r in response.context['table'].data if r.pk == self.policy.pk)
        self.assertEqual(row.entry_count, 1)
        response = self.client.get(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_list')
            + '?implicit=true'
        )
        self.assertContains(response, str(IMPLICIT_SEQUENCE))
        self.assertNotContains(response, self.entry.get_absolute_url())

    def test_the_final_deny_is_not_deleted_in_bulk(self):
        self.client.force_login(self.user)
        final = self.policy.route_policy_entries.get(implicit=True)
        self.client.post(
            reverse('plugins:netbox_routing_protocols:routepolicyentry_bulk_delete'),
            {'pk': [final.pk], 'confirm': True, '_confirm': True},
        )
        self.assertTrue(RoutePolicyEntry.objects.filter(pk=final.pk).exists())

    def test_a_new_policy_by_the_api_has_it(self):
        api = APITestCase()
        del api
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('plugins-api:netbox_routing_protocols-api:routepolicy-list'),
            {'name': 'ByApi'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        policy = RoutePolicy.objects.get(name='ByApi')
        self.assertTrue(policy.route_policy_entries.filter(implicit=True).exists())


class JumpTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first = RoutePolicy.objects.create(name='First')
        cls.second = RoutePolicy.objects.create(name='Second')
        cls.third = RoutePolicy.objects.create(name='Third')

    def entry(self, policy, jump, sequence=10, **fields):
        entry = RoutePolicyEntry(
            route_policy=policy,
            sequence=sequence,
            action='permit',
            jump_policy=jump,
            **fields,
        )
        entry.full_clean()
        return entry

    def test_a_jump_to_another_policy(self):
        self.entry(self.first, self.second).save()
        self.assertEqual(self.second.jumped_from.get().route_policy, self.first)

    def test_a_jump_cannot_make_a_loop(self):
        with self.assertRaises(ValidationError) as ctx:
            self.entry(self.first, self.first)
        self.assertIn('jump_policy', ctx.exception.message_dict)
        self.entry(self.first, self.second).save()
        self.entry(self.second, self.third).save()
        for policy, target in ((self.second, self.first), (self.third, self.first)):
            with self.subTest(f'{policy} -> {target}'):
                with self.assertRaises(ValidationError) as ctx:
                    self.entry(policy, target, sequence=20)
                self.assertIn('jump_policy', ctx.exception.message_dict)

    def test_editing_the_jump_does_not_collide_with_itself(self):
        entry = self.entry(self.first, self.second)
        entry.save()
        entry.jump_policy = self.third
        entry.full_clean()

    def test_a_deny_entry_cannot_jump(self):
        entry = RoutePolicyEntry(
            route_policy=self.first, sequence=10, action='deny', jump_policy=self.second
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()
        self.assertIn('jump_policy', ctx.exception.message_dict)

    def test_a_policy_that_is_a_jump_target_cannot_be_deleted(self):
        self.entry(self.first, self.second).save()
        with self.assertRaises(ProtectedError):
            self.second.delete()
        self.first.delete()
        self.second.delete()


class UnreachableTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.policy = RoutePolicy.objects.create(name='Policy')
        cls.prefixes = PrefixList.objects.create(name='Prefixes', family=4)
        cls.user = User.objects.create_superuser('su', 'su@example.com', 'x')

    def test_a_policy_with_conditions_has_none(self):
        make_entry(self.policy, 10, match_metric=5)
        make_entry(self.policy, 20, match_tag=1)
        self.assertEqual(self.policy.unreachable_entries(), [])
        self.client.force_login(self.user)
        self.assertNotContains(
            self.client.get(self.policy.get_absolute_url()), 'never evaluated'
        )

    def test_the_entries_after_one_without_conditions(self):
        make_entry(self.policy, 10, match_metric=5)
        stopper = make_entry(self.policy, 20)
        later = [make_entry(self.policy, 30), make_entry(self.policy, 40, 'deny')]
        found = self.policy.unreachable_entries()
        self.assertEqual([entry for entry, _by in found], later)
        self.assertEqual({by for _entry, by in found}, {stopper})

    def test_a_list_is_a_condition(self):
        entry = make_entry(self.policy, 10)
        entry.match_prefix_list.add(self.prefixes)
        make_entry(self.policy, 20)
        self.assertEqual(self.policy.unreachable_entries(), [])

    def test_the_final_deny_is_not_reported(self):
        make_entry(self.policy, 10)
        self.assertEqual(self.policy.unreachable_entries(), [])

    def test_the_page_warns(self):
        make_entry(self.policy, 10)
        make_entry(self.policy, 20)
        self.client.force_login(self.user)
        response = self.client.get(self.policy.get_absolute_url())
        self.assertContains(response, 'Entries never evaluated')
        self.assertContains(response, 'Entry 10 has no conditions')


class FinalDenyMigrationTestCase(TransactionTestCase):
    """The route policies that exist before the migration get their final deny"""

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_existing_policies_get_it(self):
        before = [('netbox_routing_protocols', '0087_protocol_route_policies')]
        after = [('netbox_routing_protocols', '0088_routepolicy_jump_and_final_deny')]
        apps = self._migrate(before)
        RoutePolicy = apps.get_model('netbox_routing_protocols', 'RoutePolicy')
        RoutePolicyEntry = apps.get_model(
            'netbox_routing_protocols', 'RoutePolicyEntry'
        )
        policy = RoutePolicy.objects.create(name='Old')
        RoutePolicyEntry.objects.create(
            route_policy=policy, sequence=10, action='permit'
        )

        apps = self._migrate(after)
        RoutePolicyEntry = apps.get_model(
            'netbox_routing_protocols', 'RoutePolicyEntry'
        )
        self.assertEqual(
            list(
                RoutePolicyEntry.objects.order_by('sequence').values_list(
                    'sequence', 'action', 'implicit'
                )
            ),
            [(10, 'permit', False), (IMPLICIT_SEQUENCE, 'deny', True)],
        )
        # and back: the deny is removed
        apps = self._migrate(before)
        RoutePolicyEntry = apps.get_model(
            'netbox_routing_protocols', 'RoutePolicyEntry'
        )
        self.assertEqual(
            list(RoutePolicyEntry.objects.values_list('sequence', flat=True)), [10]
        )
        self._migrate(after)
