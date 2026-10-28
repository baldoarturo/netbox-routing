from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from users.models import User
from utilities.exceptions import AbortRequest

from ipam.models import Prefix
from netbox_routing_protocols.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RouteMapTestCase',
    'RouteMapEntryTestCase',
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


class RouteMapTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'Route Map 1'
        rm = RouteMap(
            name=name,
        )
        rm.full_clean()
        rm.save()
        self.assertIsInstance(rm, RouteMap)
        self.assertEqual(str(rm), name)

    def test_unique_together(self):
        name = 'Route Map 1'
        rm = RouteMap(
            name=name,
        )
        rm.full_clean()
        rm.save()

        rm = RouteMap(
            name=name,
        )

        with self.assertRaises(ValidationError):
            rm.full_clean()
        with self.assertRaises(IntegrityError):
            rm.save()


class RouteMapEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route_map = RouteMap(
            name='Route Map',
        )
        cls.route_map.full_clean()
        cls.route_map.save()

    def test_route_map_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            rme = RouteMapEntry(
                route_map=self.route_map,
                action='permit',
                sequence=seq,
                match={'tags': f'{seq}{seq}{seq}{seq}'},
            )
            rme.full_clean()
            rme.save()
            self.assertIsInstance(rme, RouteMapEntry)
            self.assertEqual(str(rme), f'{self.route_map} permit {seq}')
