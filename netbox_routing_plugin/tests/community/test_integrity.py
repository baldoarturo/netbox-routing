import importlib

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from netbox_routing_plugin.helpers import community as helpers
from netbox_routing_plugin.models.community import *

__all__ = (
    'CommunityParserTestCase',
    'CommunityModelTestCase',
    'CommunityListTestCase',
    'CommunityMigrationTestCase',
)


class CommunityParserTestCase(TestCase):
    def test_valid(self):
        cases = {
            '65000:100': ('standard', '65000:100'),
            '65000:0100': ('standard', '65000:100'),
            '65535:65535': ('standard', '65535:65535'),
            ' 65000:1 ': ('standard', '65000:1'),
            '4259840100': ('standard', '65000:100'),  # 32-bit number: 0xFDE80064
            'no-export': ('standard', '65535:65281'),
            'NO_ADVERTISE': ('standard', '65535:65282'),
            'local-AS': ('standard', '65535:65283'),
            'blackhole': ('standard', '65535:666'),
            'graceful-shutdown': ('standard', '65535:0'),
            'rt:65000:100': ('extended', 'rt:65000:100'),
            'RT:65000:0100': ('extended', 'rt:65000:100'),
            'target:65000:1': ('extended', 'rt:65000:1'),
            'soo:65000:4294967295': ('extended', 'soo:65000:4294967295'),
            'origin:65000:1': ('extended', 'soo:65000:1'),
            'rt:4200000000:65535': ('extended', 'rt:4200000000:65535'),  # RFC 5668
            'rt:192.0.2.1:100': ('extended', 'rt:192.0.2.1:100'),
            'rt:2001:db8::1:100': ('extended', 'rt:2001:db8::1:100'),  # RFC 5701
            '65000:1:2': ('large', '65000:1:2'),  # RFC 8092
            '4200000000:4294967295:0': ('large', '4200000000:4294967295:0'),
            '0065000:001:2': ('large', '65000:1:2'),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(helpers.parse(value), expected)

    def test_invalid(self):
        for value in (
            '',
            'abc',
            '70000:1',  # standard are 16-bit numbers
            '65000:70000',
            '1.2.3.4',
            '4294967296:1:1',  # large above 32 bits
            '1:2:3:4',
            '4294967296',
            'rt:65000',
            'rt:65000:4294967296',  # 2-byte ASN: 4-byte value at most
            'rt:4200000000:65536',  # 4-byte ASN: 2-byte value at most
            'rt:192.0.2.1:65536',
            'rt:300.0.0.1:1',
            'rt:abc:1',
            'foo:65000:1',
            'no-such-name',
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                helpers.parse(value)

    def test_well_known_name(self):
        self.assertEqual(
            helpers.well_known_name('65535:65281'), ('NO_EXPORT', 'RFC 1997')
        )
        self.assertEqual(
            helpers.well_known_name('65535:666'), ('BLACKHOLE', 'RFC 7999')
        )
        self.assertIsNone(helpers.well_known_name('65000:1'))


class CommunityModelTestCase(TestCase):
    def test_clean_normalises_and_sets_type(self):
        community = Community(community='No-Export')
        community.full_clean()
        community.save()
        self.assertEqual(community.community, '65535:65281')
        self.assertEqual(community.type, 'standard')
        self.assertEqual(community.well_known, 'NO_EXPORT (RFC 1997)')

        community = Community(community='rt:65000:1')
        community.full_clean()
        self.assertEqual((community.type, community.well_known), ('extended', None))

    def test_invalid_value_is_reported_on_the_field(self):
        with self.assertRaises(ValidationError) as caught:
            Community(community='70000:1').full_clean()
        self.assertIn('community', caught.exception.message_dict)

    def test_same_community_written_differently_is_a_duplicate(self):
        Community(community='65000:100').save()
        with self.assertRaises(ValidationError) as caught:
            Community(community='65000:0100').full_clean()
        self.assertIn('already exists', str(caught.exception))

    def test_delete_is_blocked_by_a_list_entry(self):
        community = Community.objects.create(community='65000:1')
        lst = CommunityList.objects.create(name='L')
        CommunityListEntry.objects.create(
            community_list=lst, sequence=10, community=community, action='permit'
        )
        with self.assertRaises(ProtectedError):
            community.delete()
        with self.assertRaises(ProtectedError):
            Community.objects.filter(pk=community.pk).delete()
        self.assertTrue(Community.objects.filter(pk=community.pk).exists())

    def test_unused_community_and_list_can_be_deleted(self):
        community = Community.objects.create(community='65000:1')
        lst = CommunityList.objects.create(name='L')
        CommunityListEntry.objects.create(
            community_list=lst, sequence=10, community=community, action='permit'
        )
        lst.delete()  # its entries go with it
        community.delete()


class CommunityListTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.standard = Community.objects.create(community='65000:1')
        cls.extended = Community.objects.create(community='rt:65000:1')

    def test_name_is_unique_ignoring_case(self):
        CommunityList.objects.create(name='Customers')
        with self.assertRaises(ValidationError) as caught:
            CommunityList(name='customers').full_clean()
        self.assertIn('Name must be unique.', str(caught.exception))

    def test_entry_must_match_the_type_of_the_list(self):
        lst = CommunityList.objects.create(name='L')  # standard
        entry = CommunityListEntry(
            community_list=lst, sequence=10, action='permit', community=self.extended
        )
        with self.assertRaises(ValidationError) as caught:
            entry.full_clean()
        self.assertIn('community', caught.exception.message_dict)

        ext = CommunityList.objects.create(name='E', type='extended')
        CommunityListEntry(
            community_list=ext, sequence=10, action='permit', community=self.extended
        ).full_clean()

    def test_type_cannot_change_with_entries_of_another_type(self):
        lst = CommunityList.objects.create(name='L')
        CommunityListEntry.objects.create(
            community_list=lst, sequence=10, action='permit', community=self.standard
        )
        lst.type = 'large'
        with self.assertRaises(ValidationError) as caught:
            lst.full_clean()
        self.assertIn('type', caught.exception.message_dict)

    def test_sequence_is_unique_in_the_list(self):
        lst = CommunityList.objects.create(name='L')
        CommunityListEntry.objects.create(
            community_list=lst, sequence=10, action='permit', community=self.standard
        )
        with self.assertRaises(ValidationError):
            CommunityListEntry(
                community_list=lst, sequence=10, action='deny', community=self.standard
            ).full_clean()

    def test_next_sequence(self):
        lst = CommunityList.objects.create(name='L')
        self.assertEqual(helpers.next_sequence(lst), 10)
        CommunityListEntry.objects.create(
            community_list=lst, sequence=10, action='permit', community=self.standard
        )
        self.assertEqual(helpers.next_sequence(lst), 20)
        self.assertEqual(helpers.next_sequence(lst, after=35), 40)

    def test_find_duplicates(self):
        lst = CommunityList.objects.create(name='L')
        first = CommunityListEntry.objects.create(
            community_list=lst, sequence=10, action='permit', community=self.standard
        )
        second = CommunityListEntry.objects.create(
            community_list=lst, sequence=20, action='deny', community=self.standard
        )
        self.assertEqual(
            [d.kind for d in helpers.find_duplicates(second)], ['shadowed']
        )
        self.assertEqual([d.kind for d in helpers.find_duplicates(first)], ['shadows'])

    def test_entries_form_numbers_a_new_entry(self):
        from netbox_routing_plugin.forms.community import CommunityListEntryForm

        lst = CommunityList.objects.create(name='L')
        data = {
            'community_list': lst.pk,
            'action': 'permit',
            'community': self.standard.pk,
        }
        for expected in (10, 20):
            form = CommunityListEntryForm(data=data)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().sequence, expected)

    def test_api_numbers_new_entries_of_a_bulk_request(self):
        from netbox_routing_plugin.api._serializers.community import (
            CommunityListEntrySerializer,
        )

        lst = CommunityList.objects.create(name='L')
        context = {}
        sequences = []
        for _i in range(2):
            serializer = CommunityListEntrySerializer(
                data={
                    'community_list': lst.pk,
                    'action': 'permit',
                    'community': self.standard.pk,
                },
                context=context,
            )
            serializer.is_valid(raise_exception=True)
            sequences.append(serializer.validated_data['sequence'])
        self.assertEqual(sequences, [10, 20])


class CommunityMigrationTestCase(TestCase):
    def test_data_migration(self):
        migration = importlib.import_module(
            'netbox_routing_plugin.migrations.0083_community_integrity'
        )
        a, b, c = (
            Community.objects.create(community=value)
            for value in ('65000:1', 'rt:65000:2', '65000:3')
        )
        # as they were stored before: not normalised, no type
        Community.objects.filter(pk=a.pk).update(
            community='65000:0001', type='standard'
        )
        Community.objects.filter(pk=b.pk).update(
            community='RT:65000:2', type='standard'
        )
        Community.objects.filter(pk=c.pk).update(community='nonsense')
        ext = CommunityList.objects.create(name='Ext')
        mixed = CommunityList.objects.create(name='Mixed')
        for lst, community, sequence in (
            (ext, b, 1),
            (mixed, a, 2),
            (mixed, b, 3),
            (mixed, c, 4),
        ):
            CommunityListEntry.objects.create(
                community_list=lst,
                community=community,
                sequence=sequence,
                action='permit',
            )

        migration.normalise_and_number(apps, None)

        found = {
            pk: (value, kind)
            for pk, value, kind in Community.objects.values_list(
                'pk', 'community', 'type'
            )
        }
        self.assertEqual(
            found,
            {
                a.pk: ('65000:1', 'standard'),
                b.pk: ('rt:65000:2', 'extended'),
                c.pk: ('nonsense', 'standard'),
            },
        )
        ext.refresh_from_db()
        mixed.refresh_from_db()
        self.assertEqual(ext.type, 'extended')
        self.assertEqual(mixed.type, 'standard')  # mixed: left as it was
        self.assertEqual(
            list(
                CommunityListEntry.objects.filter(community_list=mixed)
                .order_by('sequence')
                .values_list('sequence', flat=True)
            ),
            [10, 20, 30],
        )
