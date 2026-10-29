from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from netbox_routing_protocols.tables.objects import *
from utilities.exceptions import AbortRequest

from ipam.models import Prefix
from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RoutePolicyTestCase',
    'RoutePolicyEntryTestCase',
)


class ASPathTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'AS Path 1'
        asp = ASPath(
            name=name,
        )
        asp.full_clean()
        asp.save()
        self.assertIsInstance(asp, ASPath)
        self.assertEqual(str(asp), name)

    def test_unique_together(self):
        name = 'AS Path 1'
        asp = ASPath(
            name=name,
        )
        asp.full_clean()
        asp.save()

        asp = ASPath(
            name=name,
        )

        with self.assertRaises(ValidationError):
            asp.full_clean()
        with self.assertRaises(IntegrityError):
            asp.save()


class ASPathEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath(
            name='AS Path',
        )
        cls.aspath.full_clean()
        cls.aspath.save()

    def test_aspath_entry(self):
        for seq, pattern in (
            (1, '^1$'),
            (2, '^2$'),
            (3, '^3$'),
            (4, '^4$'),
        ):
            aspe = ASPathEntry(
                aspath=self.aspath,
                action='permit',
                sequence=seq,
                pattern=pattern,
            )
            aspe.full_clean()
            aspe.save()
            self.assertIsInstance(aspe, ASPathEntry)
            self.assertEqual(str(aspe), f'{self.aspath} permit {seq}')

    def test_sequence_range(self):
        for sequence, valid in (
            (0, False),
            (1, True),
            (32768, True),
            (4294967294, True),
            (4294967295, False),
        ):
            with self.subTest(sequence):
                entry = ASPathEntry(
                    aspath=self.aspath,
                    action='permit',
                    sequence=sequence,
                    pattern='^1$',
                )
                if valid:
                    entry.full_clean()
                    entry.save()
                    entry.refresh_from_db()
                    self.assertEqual(entry.sequence, sequence)
                    entry.delete()
                else:
                    with self.assertRaises(ValidationError) as ctx:
                        entry.full_clean()
                    self.assertIn('sequence', ctx.exception.message_dict)

    def test_pattern_validation(self):
        for pattern, valid in (
            ('^$', True),
            ('^65001_', True),
            ('_(65001|4294967295)$', True),
            ('^1.10$', True),
            ('^[0-9]+$', True),
            ('^64512{2,3}$', True),
            ('.*', True),
            ('', False),
            ('   ', False),
            ('^65001_.*_65002$', True),
            ('^(65001|65002)+$', True),
            ('[[:digit:]]+', True),
            ('^\\(65001\\)$', True),
            ('*65001', False),
            ('^65001||65002$', False),
            ('()', False),
            ('^65001|', False),
            ('^\\d+$', False),
            ('^(?:65001)$', False),
            ('[9-0]', False),
            ('[[:foo:]]', False),
            ('^65001{3,2}$', False),
            ('65001}', False),
            ('^65001\\', False),
            ('^(65001', False),
            ('65001)', False),
            ('^[65001', False),
            ('^65001{2', False),
            ('^4294967296$', False),
            ('^70000.1$', False),
            ('^1.70000$', False),
            ('^²$', False),
            ('^٣$', False),
            ('^１$', False),
            ('^1\u00a0$', False),
            ('^1\t$', False),
        ):
            with self.subTest(pattern):
                entry = ASPathEntry(
                    aspath=self.aspath, action='permit', sequence=1, pattern=pattern
                )
                if valid:
                    entry.full_clean()
                else:
                    with self.assertRaises(ValidationError) as ctx:
                        entry.full_clean()
                    self.assertIn('pattern', ctx.exception.message_dict)

    def test_form_explains_the_pattern(self):
        from netbox_routing_protocols.forms.model_objects.objects import (
            ASPathEntryForm,
        )

        form = ASPathEntryForm()
        self.assertIn('POSIX extended', form.fields['pattern'].help_text)
        self.assertNotIn('Cisco', form.fields['pattern'].help_text)

    def test_name_is_unique_ignoring_case(self):
        ASPath.objects.create(name='Customers')
        with self.assertRaises(ValidationError):
            ASPath(name='CUSTOMERS').full_clean()

    def test_urls_and_cascade_delete(self):
        entry = ASPathEntry.objects.create(
            aspath=self.aspath, action='permit', sequence=10, pattern='^1$'
        )
        self.assertEqual(
            self.aspath.get_absolute_url(),
            reverse('plugins:netbox_routing_protocols:aspath', args=[self.aspath.pk]),
        )
        self.assertEqual(
            entry.get_absolute_url(),
            reverse('plugins:netbox_routing_protocols:aspathentry', args=[entry.pk]),
        )
        self.aspath.delete()
        self.assertFalse(ASPathEntry.objects.filter(pk=entry.pk).exists())

    def test_clean_without_an_aspath_reports_the_required_field_only(self):
        entry = ASPathEntry(action='permit', sequence=10, pattern='^1$')
        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()
        self.assertEqual(set(ctx.exception.message_dict), {'aspath'})
        self.assertEqual(str(ASPathEntry()), 'ASPathEntry object (None)')

    def test_duplicate_sequence_message(self):
        ASPathEntry.objects.create(
            aspath=self.aspath, action='permit', sequence=10, pattern='^1$'
        )
        entry = ASPathEntry(
            aspath=self.aspath, action='deny', sequence=10, pattern='^2$'
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()
        self.assertIn('AS-Path sequence must be unique', str(ctx.exception))


class PrefixListTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'Prefix List 1'
        pl = PrefixList(
            name=name,
        )
        pl.full_clean()
        pl.save()
        self.assertIsInstance(pl, PrefixList)
        self.assertEqual(str(pl), name)

    def test_unique_together(self):
        name = 'Prefix List 1'
        pl = PrefixList(
            name=name,
        )
        pl.full_clean()
        pl.save()

        pl = PrefixList(
            name=name,
        )

        with self.assertRaises(ValidationError):
            pl.full_clean()
        with self.assertRaises(IntegrityError):
            pl.save()


class PrefixListEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList(
            name='Prefix List',
        )
        cls.prefix_list.full_clean()
        cls.prefix_list.save()
        cls.v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)

    def _prefix(self, value):
        prefix = Prefix(prefix=value)
        prefix.full_clean()
        prefix.save()
        return prefix

    def _entry(self, prefix, prefix_list=None, sequence=1, **kwargs):
        entry = PrefixListEntry(
            prefix_list=prefix_list or self.prefix_list,
            action='permit',
            sequence=sequence,
            prefix=prefix,
            **kwargs,
        )
        entry.full_clean()
        entry.save()
        return entry

    def test_prefix_list_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            ple = self._entry(self._prefix(pattern), sequence=seq)
            self.assertIsInstance(ple, PrefixListEntry)
            self.assertEqual(str(ple), f'{self.prefix_list} permit {seq}')

    def test_prefix_is_required(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list, action='permit', sequence=1
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()
        self.assertIn('prefix', ctx.exception.message_dict)

    def test_used_prefix_cannot_be_deleted(self):
        prefix = self._prefix('10.0.1.0/24')
        entry = self._entry(prefix)
        with self.assertRaises(ProtectedError):
            prefix.delete()
        with self.assertRaises(ProtectedError):
            Prefix.objects.filter(pk=prefix.pk).delete()
        self.assertTrue(Prefix.objects.filter(pk=prefix.pk).exists())
        self.assertTrue(PrefixListEntry.objects.filter(pk=entry.pk).exists())

        # Once the entry is gone the prefix can be deleted
        entry.delete()
        prefix.delete()
        self.assertFalse(Prefix.objects.filter(pk=prefix.pk).exists())

    def test_used_prefix_delete_view_shows_error(self):
        user = User.objects.create_superuser('admin149', 'admin@example.com', 'x')
        self.client.force_login(user)
        prefix = self._prefix('10.0.5.0/24')
        self._entry(prefix)
        url = reverse('ipam:prefix_delete', kwargs={'pk': prefix.pk})
        response = self.client.post(url, {'confirm': True}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Prefix.objects.filter(pk=prefix.pk).exists())
        self.assertContains(response, 'Unable to delete', status_code=200)

    def test_unused_prefix_can_be_deleted(self):
        prefix = self._prefix('10.0.3.0/24')
        prefix.delete()
        self.assertFalse(Prefix.objects.filter(prefix='10.0.3.0/24').exists())

    def test_deleting_prefix_list_still_deletes_entries(self):
        entry = self._entry(self._prefix('10.0.4.0/24'))
        self.prefix_list.delete()
        self.assertFalse(PrefixListEntry.objects.filter(pk=entry.pk).exists())
        self.assertTrue(Prefix.objects.filter(prefix='10.0.4.0/24').exists())

    def test_prefix_change_that_invalidates_an_entry_is_refused(self):
        for value, new_value in (
            ('10.1.0.0/24', '10.1.0.0/29'),
            ('10.3.0.0/24', '2001:db8::/32'),
        ):
            with self.subTest(new_value):
                prefix = self._prefix(value)
                entry = self._entry(prefix, ge=28, le=32)
                prefix.prefix = new_value
                with self.assertRaises(AbortRequest) as ctx:
                    prefix.save()
                self.assertIn(str(entry), str(ctx.exception.message))
                prefix.refresh_from_db()
                self.assertEqual(str(prefix.prefix), value)
                entry.delete()

    def test_compatible_prefix_change_is_allowed(self):
        prefix = self._prefix('10.5.0.0/24')
        self._entry(prefix, ge=26, le=32)
        prefix.prefix = '10.5.0.0/25'
        prefix.save()
        prefix.refresh_from_db()
        self.assertEqual(str(prefix.prefix), '10.5.0.0/25')

    def test_unused_prefix_can_change(self):
        prefix = self._prefix('10.7.0.0/24')
        prefix.prefix = '2001:db8::/32'
        prefix.save()

    def test_prefix_edit_view_shows_error(self):
        user = User.objects.create_superuser('admin154', 'admin@example.com', 'x')
        self.client.force_login(user)
        prefix = self._prefix('10.8.0.0/24')
        self._entry(prefix, ge=28)
        url = reverse('ipam:prefix_edit', kwargs={'pk': prefix.pk})
        response = self.client.post(
            url, {'prefix': '10.8.0.0/29', 'status': 'active'}, follow=True
        )
        self.assertContains(response, 'would make prefix list entries invalid')
        prefix.refresh_from_db()
        self.assertEqual(str(prefix.prefix), '10.8.0.0/24')

    def test_bulk_edit_action_ge_le(self):
        user = User.objects.create_superuser('admin157', 'admin@example.com', 'x')
        self.client.force_login(user)
        prefix = self._prefix('10.20.0.0/16')
        entries = [self._entry(prefix, sequence=n) for n in (1, 2)]
        url = reverse('plugins:netbox_routing_protocols:prefixlistentry_bulk_edit')
        response = self.client.post(
            url,
            {
                'pk': [e.pk for e in entries],
                '_apply': True,
                'action': 'deny',
                'ge': 24,
                'le': 28,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        for entry in entries:
            entry.refresh_from_db()
            self.assertEqual((entry.action, entry.ge, entry.le), ('deny', 24, 28))
        # invalid values are refused by the model validation
        response = self.client.post(
            url,
            {'pk': [e.pk for e in entries], '_apply': True, 'ge': 8},
            follow=True,
        )
        entries[0].refresh_from_db()
        self.assertEqual(entries[0].ge, 24)

    def test_tables_render_every_column(self):
        self._entry(self._prefix('10.21.0.0/16'))
        for table_class, queryset in (
            (PrefixListTable, PrefixList.objects.all()),
            (
                PrefixListEntryTable,
                PrefixListEntry.objects.select_related('prefix_list', 'prefix'),
            ),
        ):
            with self.subTest(table_class.__name__):
                table = table_class(queryset)
                for column in table.columns.all():
                    for row in table.rows:
                        row.get_cell(column.name)

    def test_any_entry(self):
        for prefix_list, boundary in ((self.prefix_list, 32), (self.v6_list, 128)):
            with self.subTest(prefix_list.family):
                entry = PrefixListEntry(
                    prefix_list=prefix_list,
                    action='permit',
                    sequence=1,
                    any_prefix=True,
                    le=boundary,
                )
                entry.full_clean()
                entry.save()
                self.assertIsNone(entry.prefix_id)
                # the all zeros prefix has length 0, ge and le are only bounded by the family
                entry.ge = 8
                entry.full_clean()
                entry.le = boundary + 1
                with self.assertRaises(ValidationError):
                    entry.full_clean()
                entry.delete()

    def test_any_and_prefix_are_exclusive(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list,
            action='permit',
            sequence=1,
            any_prefix=True,
            prefix=self._prefix('10.40.0.0/16'),
        )
        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()
        self.assertIn('prefix', ctx.exception.message_dict)

    def test_the_database_requires_a_prefix_or_any(self):
        from django.db import transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            PrefixListEntry.objects.create(
                prefix_list=self.prefix_list, action='permit', sequence=1
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PrefixListEntry.objects.create(
                prefix_list=self.prefix_list,
                action='permit',
                sequence=2,
                any_prefix=True,
                prefix=self._prefix('10.41.0.0/16'),
            )

    def test_next_sequence(self):
        from netbox_routing_protocols.helpers.prefix_list import next_sequence

        prefix = self._prefix('10.50.0.0/16')
        self.assertEqual(next_sequence(self.prefix_list), 10)
        for sequence, expected in ((10, 20), (25, 30), (30, 40), (1, 40), (999, 1000)):
            self._entry(prefix, sequence=sequence)
            self.assertEqual(next_sequence(self.prefix_list), expected)
        # numbers already handed out in the same request count too
        self.assertEqual(next_sequence(self.prefix_list, after=1500), 1510)
        # another list is independent
        self.assertEqual(next_sequence(self.v6_list), 10)
        # the highest sequence leaves no room
        self._entry(prefix, sequence=4294967290)
        with self.assertRaises(ValidationError):
            next_sequence(self.prefix_list)

    def test_sequence_range(self):
        prefix = self._prefix('10.0.11.0/24')
        for sequence, valid in (
            (0, False),
            (1, True),
            (32768, True),
            (4294967294, True),
            (4294967295, False),
        ):
            with self.subTest(sequence):
                entry = PrefixListEntry(
                    prefix_list=self.prefix_list,
                    action='permit',
                    sequence=sequence,
                    prefix=prefix,
                )
                if valid:
                    entry.full_clean()
                    entry.save()
                    entry.refresh_from_db()
                    self.assertEqual(entry.sequence, sequence)
                    entry.delete()
                else:
                    with self.assertRaises(ValidationError) as ctx:
                        entry.full_clean()
                    self.assertIn('sequence', ctx.exception.message_dict)

    def test_family_mismatch_is_rejected(self):
        for prefix_list, value in (
            (self.prefix_list, '2001:db8::/32'),
            (self.v6_list, '10.0.7.0/24'),
        ):
            with self.subTest(f'{prefix_list.family} {value}'):
                entry = PrefixListEntry(
                    prefix_list=prefix_list,
                    action='permit',
                    sequence=1,
                    prefix=self._prefix(value),
                )
                with self.assertRaises(ValidationError):
                    entry.full_clean()

    def test_family_match_is_accepted(self):
        self._entry(
            self._prefix('2001:db8::/32'), prefix_list=self.v6_list, ge=48, le=128
        )

    def test_ge_le_follow_the_list_family(self):
        v4_prefix = self._prefix('11.0.0.0/8')
        v6_prefix = self._prefix('2001::/16')
        for prefix_list, prefix, field, value, valid in (
            (self.prefix_list, v4_prefix, 'le', 32, True),
            (self.prefix_list, v4_prefix, 'le', 33, False),
            (self.prefix_list, v4_prefix, 'ge', 33, False),
            (self.v6_list, v6_prefix, 'le', 128, True),
            (self.v6_list, v6_prefix, 'le', 129, False),
            (self.v6_list, v6_prefix, 'ge', 129, False),
        ):
            with self.subTest(f'{prefix_list.family} {field} {value}'):
                entry = PrefixListEntry(
                    prefix_list=prefix_list,
                    action='permit',
                    sequence=1,
                    prefix=prefix,
                )
                setattr(entry, field, value)
                try:
                    entry.clean()
                except ValidationError as e:
                    self.assertFalse(valid, e)
                    self.assertIn(field, e.message_dict)
                else:
                    self.assertTrue(valid)

    def test_ge_le_are_inclusive_of_the_prefix_length(self):
        # le is "less than or equal" and ge "greater than or equal": the prefix
        # length itself is a valid value for both
        prefix = self._prefix('10.30.0.0/24')
        for ge, le, valid in (
            (None, 24, True),
            (24, None, True),
            (24, 24, True),
            (24, 32, True),
            (25, 32, True),
            (None, 23, False),
            (23, None, False),
            (23, 32, False),
            (24, 23, False),
        ):
            with self.subTest(f'ge={ge} le={le}'):
                entry = PrefixListEntry(
                    prefix_list=self.prefix_list,
                    action='permit',
                    sequence=1,
                    prefix=prefix,
                    ge=ge,
                    le=le,
                )
                if valid:
                    entry.full_clean()
                else:
                    with self.assertRaises(ValidationError):
                        entry.full_clean()

    def test_ge_cannot_be_greater_than_le(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list,
            action='permit',
            sequence=1,
            prefix=self._prefix('12.0.0.0/8'),
            ge=28,
            le=24,
        )
        with self.assertRaises(ValidationError):
            entry.clean()

    def test_family_cannot_be_changed(self):
        self.prefix_list.family = 6
        with self.assertRaises(ValidationError) as ctx:
            self.prefix_list.full_clean()
        self.assertIn('family', ctx.exception.message_dict)
        self.prefix_list.refresh_from_db()
        self.assertEqual(self.prefix_list.family, 4)
        # saving it again with the same family is fine
        self.prefix_list.full_clean()


class RoutePolicyTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'Route Policy 1'
        rm = RoutePolicy(
            name=name,
        )
        rm.full_clean()
        rm.save()
        self.assertIsInstance(rm, RoutePolicy)
        self.assertEqual(str(rm), name)

    def test_unique_together(self):
        name = 'Route Policy 1'
        rm = RoutePolicy(
            name=name,
        )
        rm.full_clean()
        rm.save()

        rm = RoutePolicy(
            name=name,
        )

        with self.assertRaises(ValidationError):
            rm.full_clean()
        with self.assertRaises(IntegrityError):
            rm.save()


class RoutePolicyEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route_policy = RoutePolicy(
            name='Route Policy',
        )
        cls.route_policy.full_clean()
        cls.route_policy.save()

    def test_route_policy_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            rme = RoutePolicyEntry(
                route_policy=self.route_policy,
                action='permit',
                sequence=seq,
                match={'tags': f'{seq}{seq}{seq}{seq}'},
            )
            rme.full_clean()
            rme.save()
            self.assertIsInstance(rme, RoutePolicyEntry)
            self.assertEqual(str(rme), f'{self.route_policy} permit {seq}')


class PrefixSignalTestCase(TestCase):
    """Changing an IPAM prefix that would break prefix list entries is refused"""

    def test_the_message_names_a_few_entries_and_counts_the_rest(self):
        prefix_list = PrefixList.objects.create(name='Signal', family=4)
        prefix = Prefix.objects.create(prefix='10.0.0.0/24')
        for sequence in range(1, 8):
            PrefixListEntry.objects.create(
                prefix_list=prefix_list,
                sequence=sequence,
                action='permit',
                prefix=prefix,
                ge=28,
            )
        prefix.prefix = '10.0.0.0/29'
        with self.assertRaisesMessage(AbortRequest, 'and 2 more'):
            prefix.save()
        prefix.refresh_from_db()
        self.assertEqual(str(prefix.prefix), '10.0.0.0/24')
