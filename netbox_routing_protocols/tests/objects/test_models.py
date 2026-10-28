from django.contrib.contenttypes.models import ContentType
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

    def test_prefix_list_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            if seq in [
                1,
                3,
            ]:
                prefix = CustomPrefix(prefix=pattern)
            else:
                prefix = Prefix(prefix=pattern)
            prefix.full_clean()
            prefix.save()

            ple = PrefixListEntry(
                prefix_list=self.prefix_list,
                action='permit',
                sequence=seq,
                assigned_prefix=prefix,
            )
            ple.full_clean()
            ple.save()
            self.assertIsInstance(ple, PrefixListEntry)
            self.assertEqual(str(ple), f'{self.prefix_list} permit {seq}')

    def test_prefix_is_required(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list, action='permit', sequence=1
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_type_without_id_is_rejected(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list,
            action='permit',
            sequence=1,
            assigned_prefix_type=ContentType.objects.get_for_model(Prefix),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_nonexistent_prefix_is_rejected(self):
        entry = PrefixListEntry(
            prefix_list=self.prefix_list,
            action='permit',
            sequence=1,
            assigned_prefix_type=ContentType.objects.get_for_model(Prefix),
            assigned_prefix_id=999999,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_prefix_change_that_invalidates_an_entry_is_refused(self):
        for prefix, new_value in (
            (Prefix(prefix='10.1.0.0/24'), '10.1.0.0/29'),
            (CustomPrefix(prefix='10.2.0.0/24'), '10.2.0.0/29'),
            (Prefix(prefix='10.3.0.0/24'), '2001:db8::/32'),
            (CustomPrefix(prefix='10.4.0.0/24'), '2001:db8:1::/48'),
        ):
            with self.subTest(f'{type(prefix).__name__} {new_value}'):
                entry = self._entry(prefix)
                entry.ge = 28
                entry.le = 32
                entry.save()
                old_value = str(prefix.prefix)
                prefix.prefix = new_value
                with self.assertRaises(AbortRequest) as ctx:
                    prefix.save()
                self.assertIn(str(entry), str(ctx.exception.message))
                prefix.refresh_from_db()
                self.assertEqual(str(prefix.prefix), old_value)
                entry.delete()

    def test_compatible_prefix_change_is_allowed(self):
        for prefix, new_value in (
            (Prefix(prefix='10.5.0.0/24'), '10.5.0.0/25'),
            (CustomPrefix(prefix='10.6.0.0/24'), '10.6.0.0/25'),
        ):
            with self.subTest(type(prefix).__name__):
                entry = self._entry(prefix)
                entry.ge = 26
                entry.le = 32
                entry.save()
                prefix.prefix = new_value
                prefix.save()
                prefix.refresh_from_db()
                self.assertEqual(str(prefix.prefix), new_value)
                entry.delete()

    def test_unused_prefix_can_change(self):
        prefix = Prefix.objects.create(prefix='10.7.0.0/24')
        prefix.prefix = '2001:db8::/32'
        prefix.save()

    def test_custom_prefix_edit_view_shows_error(self):
        user = User.objects.create_superuser('admin154', 'admin@example.com', 'x')
        self.client.force_login(user)
        prefix = CustomPrefix(prefix='10.8.0.0/24')
        entry = self._entry(prefix)
        entry.ge = 28
        entry.save()
        url = reverse(
            'plugins:netbox_routing_protocols:customprefix_edit',
            kwargs={'pk': prefix.pk},
        )
        response = self.client.post(url, {'prefix': '10.8.0.0/29'}, follow=True)
        self.assertContains(response, 'would make prefix list entries invalid')
        prefix.refresh_from_db()
        self.assertEqual(str(prefix.prefix), '10.8.0.0/24')

    def test_family_mismatch_is_rejected(self):
        v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)
        for prefix_list, prefix in (
            (self.prefix_list, Prefix(prefix='2001:db8::/32')),
            (self.prefix_list, CustomPrefix(prefix='2001:db8:1::/48')),
            (v6_list, Prefix(prefix='10.0.7.0/24')),
            (v6_list, CustomPrefix(prefix='10.0.8.0/24')),
        ):
            with self.subTest(f'{prefix_list.family} {prefix}'):
                prefix.full_clean()
                prefix.save()
                entry = PrefixListEntry(
                    prefix_list=prefix_list,
                    action='permit',
                    sequence=1,
                    assigned_prefix=prefix,
                )
                with self.assertRaises(ValidationError):
                    entry.full_clean()

    def test_family_match_is_accepted(self):
        v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)
        prefix = CustomPrefix(prefix='2001:db8::/32')
        prefix.full_clean()
        prefix.save()
        entry = PrefixListEntry(
            prefix_list=v6_list,
            action='permit',
            sequence=1,
            assigned_prefix=prefix,
            ge=48,
            le=128,
        )
        entry.full_clean()

    def test_ge_le_follow_the_list_family(self):
        v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)
        v4_prefix = CustomPrefix.objects.create(prefix='11.0.0.0/8')
        v6_prefix = CustomPrefix.objects.create(prefix='2001::/16')
        for prefix_list, prefix, field, value, valid in (
            (self.prefix_list, v4_prefix, 'le', 32, True),
            (self.prefix_list, v4_prefix, 'le', 33, False),
            (self.prefix_list, v4_prefix, 'ge', 33, False),
            (v6_list, v6_prefix, 'le', 128, True),
            (v6_list, v6_prefix, 'le', 129, False),
            (v6_list, v6_prefix, 'ge', 129, False),
        ):
            with self.subTest(f'{prefix_list.family} {field} {value}'):
                entry = PrefixListEntry(
                    prefix_list=prefix_list,
                    action='permit',
                    sequence=1,
                    assigned_prefix=prefix,
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
            assigned_prefix=CustomPrefix.objects.create(prefix='12.0.0.0/8'),
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

    def _entry(self, prefix):
        prefix.full_clean()
        prefix.save()
        entry = PrefixListEntry(
            prefix_list=self.prefix_list,
            action='permit',
            sequence=1,
            assigned_prefix=prefix,
        )
        entry.full_clean()
        entry.save()
        return entry

    def test_used_prefix_cannot_be_deleted(self):
        for prefix in (
            Prefix(prefix='10.0.1.0/24'),
            CustomPrefix(prefix='10.0.2.0/24'),
        ):
            with self.subTest(type(prefix).__name__):
                entry = self._entry(prefix)
                with self.assertRaises(ProtectedError):
                    prefix.delete()
                with self.assertRaises(ProtectedError):
                    type(prefix).objects.filter(pk=prefix.pk).delete()
                self.assertTrue(type(prefix).objects.filter(pk=prefix.pk).exists())
                self.assertTrue(PrefixListEntry.objects.filter(pk=entry.pk).exists())

                # Once the entry is gone the prefix can be deleted
                entry.delete()
                prefix.delete()
                self.assertFalse(type(prefix).objects.filter(pk=prefix.pk).exists())

    def test_used_prefix_delete_view_shows_error(self):
        user = User.objects.create_superuser('admin149', 'admin@example.com', 'x')
        self.client.force_login(user)
        for prefix, view in (
            (Prefix(prefix='10.0.5.0/24'), 'ipam:prefix_delete'),
            (
                CustomPrefix(prefix='10.0.6.0/24'),
                'plugins:netbox_routing_protocols:customprefix_delete',
            ),
        ):
            with self.subTest(type(prefix).__name__):
                self._entry(prefix)
                url = reverse(view, kwargs={'pk': prefix.pk})
                response = self.client.post(url, {'confirm': True}, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(type(prefix).objects.filter(pk=prefix.pk).exists())
                self.assertContains(response, 'Unable to delete', status_code=200)
                PrefixListEntry.objects.all().delete()

    def test_unused_prefix_can_be_deleted(self):
        prefix = Prefix(prefix='10.0.3.0/24')
        prefix.full_clean()
        prefix.save()
        prefix.delete()
        self.assertFalse(Prefix.objects.filter(prefix='10.0.3.0/24').exists())

    def test_deleting_prefix_list_still_deletes_entries(self):
        entry = self._entry(CustomPrefix(prefix='10.0.4.0/24'))
        self.prefix_list.delete()
        self.assertFalse(PrefixListEntry.objects.filter(pk=entry.pk).exists())
        self.assertTrue(CustomPrefix.objects.filter(prefix='10.0.4.0/24').exists())


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
