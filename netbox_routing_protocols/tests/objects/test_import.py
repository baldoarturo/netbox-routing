from django.test import TestCase
from django.urls import reverse

from ipam.models import Prefix, VRF
from users.models import User

from netbox_routing_protocols.forms.bulk_import import (
    ASPathEntryImportForm,
    ASPathImportForm,
    PrefixListEntryImportForm,
    PrefixListImportForm,
)
from netbox_routing_protocols.models.objects import (
    ASPath,
    ASPathEntry,
    PrefixList,
    PrefixListEntry,
)

__all__ = (
    'PrefixListImportTestCase',
    'PrefixListImportOverlapTestCase',
    'ASPathImportTestCase',
    'ASPathImportDuplicatesTestCase',
)


class PrefixListImportTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.v4 = PrefixList.objects.create(name='v4', family=4)
        cls.v6 = PrefixList.objects.create(name='v6', family=6)
        cls.prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        cls.v6_prefix = Prefix.objects.create(prefix='2001:db8::/32')

    def entry(self, **kwargs):
        data = {'prefix_list': 'v4', 'action': 'permit', 'prefix': '10.0.0.0/8'}
        data.update(kwargs)
        return PrefixListEntryImportForm(data=data)

    def test_list_family_defaults_to_ipv4(self):
        form = PrefixListImportForm(data={'name': 'new'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().family, 4)
        form = PrefixListImportForm(data={'name': 'new6', 'family': '6'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().family, 6)

    def test_entry_by_cidr_takes_the_next_sequence(self):
        for expected in (10, 20):
            form = self.entry()
            self.assertTrue(form.is_valid(), form.errors)
            entry = form.save()
            self.assertEqual((entry.prefix, entry.sequence), (self.prefix, expected))

    def test_explicit_sequence_ge_le_and_eq(self):
        form = self.entry(sequence='7', ge='16', le='24')
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual((entry.sequence, entry.ge, entry.le), (7, 16, 24))
        form = self.entry(eq='16')
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual((entry.ge, entry.le), (16, 16))
        self.assertFalse(self.entry(eq='16', ge='9').is_valid())

    def test_any(self):
        for name, prefix_list, le in (('v4', self.v4, 32), ('v6', self.v6, 128)):
            form = self.entry(prefix_list=name, prefix='ANY')
            self.assertTrue(form.is_valid(), form.errors)
            entry = form.save()
            self.assertTrue(entry.any_prefix)
            self.assertIsNone(entry.prefix)
            self.assertEqual(entry.le, le)

    def test_the_prefix_must_exist_in_ipam(self):
        form = self.entry(prefix='192.0.2.0/24')
        self.assertFalse(form.is_valid())
        self.assertIn('create it first', str(form.errors['prefix']))
        self.assertFalse(Prefix.objects.filter(prefix='192.0.2.0/24').exists())

    def test_an_invalid_prefix_is_a_form_error(self):
        form = self.entry(prefix='not-a-prefix')
        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    def test_the_family_of_the_list_is_checked(self):
        form = self.entry(prefix_list='v6')
        self.assertFalse(form.is_valid())

    def test_the_same_cidr_in_several_vrfs_needs_the_vrf(self):
        vrf = VRF.objects.create(name='red')
        other = Prefix.objects.create(prefix='10.0.0.0/8', vrf=vrf)
        form = self.entry()
        self.assertFalse(form.is_valid())
        self.assertIn('vrf', str(form.errors['prefix']))
        form = self.entry(vrf='red')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().prefix, other)

    def test_import_view_with_csv(self):
        user = User.objects.create_superuser('importer', 'i@example.com', 'x')
        self.client.force_login(user)
        csv = (
            'prefix_list,action,prefix,sequence,le\n'
            'v4,permit,10.0.0.0/8,,24\n'
            'v4,deny,any,,\n'
            'v6,permit,2001:db8::/32,5,48\n'
        )
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:prefixlistentry_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': ','},
        )
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None))
        self.assertEqual(
            list(
                PrefixListEntry.objects.order_by(
                    'prefix_list__name', 'sequence'
                ).values_list('prefix_list__name', 'sequence', 'action', 'le')
            ),
            [('v4', 10, 'permit', 24), ('v4', 20, 'deny', 32), ('v6', 5, 'permit', 48)],
        )

    def test_list_import_view(self):
        user = User.objects.create_superuser('importer', 'i@example.com', 'x')
        self.client.force_login(user)
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:prefixlist_bulk_import'),
            {
                'data': 'name,family\nfrom-csv,6\n',
                'format': 'csv',
                'csv_delimiter': ',',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PrefixList.objects.get(name='from-csv').family, 6)


class PrefixListImportOverlapTestCase(TestCase):
    """The import saves overlapping entries and tells the user, once per pair"""

    @classmethod
    def setUpTestData(cls):
        cls.v4 = PrefixList.objects.create(name='v4', family=4)
        cls.other = PrefixList.objects.create(name='other', family=4)
        Prefix.objects.create(prefix='10.0.0.0/8')
        Prefix.objects.create(prefix='10.1.0.0/16')
        cls.user = User.objects.create_superuser('importer', 'i@example.com', 'x')

    def _import(self, csv):
        self.client.force_login(self.user)
        return self.client.post(
            reverse('plugins:netbox_routing_protocols:prefixlistentry_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': ','},
            follow=True,
        )

    def _warnings(self, response):
        return [
            str(m) for m in response.context['messages'] if m.level_tag == 'warning'
        ]

    def test_overlaps_are_summarized_once_per_pair(self):
        response = self._import(
            'prefix_list,action,prefix,sequence\n'
            'v4,permit,10.0.0.0/8,10\n'
            'v4,permit,10.0.0.0/8,20\n'
            'v4,permit,10.1.0.0/16,30\n'
        )
        self.assertEqual(PrefixListEntry.objects.count(), 3)
        warnings = self._warnings(response)
        self.assertEqual(len(warnings), 1)
        self.assertIn('Prefix list v4', warnings[0])
        # 10/8 twice: one duplicate; and the /16 is another prefix: no overlap with them
        self.assertIn('1 duplicate', warnings[0])

    def test_an_import_without_overlaps_has_no_warning(self):
        response = self._import(
            'prefix_list,action,prefix,sequence\nv4,permit,10.0.0.0/8,10\nother,permit,10.0.0.0/8,10\n'
        )
        self.assertEqual(PrefixListEntry.objects.count(), 2)
        self.assertEqual(self._warnings(response), [])

    def test_overlaps_with_existing_entries_are_included(self):
        self._import('prefix_list,action,prefix,sequence\nv4,permit,10.0.0.0/8,10\n')
        response = self._import(
            'prefix_list,action,prefix,sequence\nv4,deny,10.0.0.0/8,20\n'
        )
        warnings = self._warnings(response)
        self.assertEqual(len(warnings), 1)
        self.assertIn('1 duplicate', warnings[0])


class ASPathImportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Path')
        cls.user = User.objects.create_superuser('importer', 'i@example.com', 'x')

    def entry(self, **kwargs):
        data = {'aspath': 'Path', 'action': 'permit', 'pattern': '^65001_'}
        data.update(kwargs)
        return ASPathEntryImportForm(data=data)

    def test_aspath_form(self):
        form = ASPathImportForm(data={'name': 'new', 'description': 'd'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().description, 'd')

    def test_an_empty_sequence_takes_the_next_one(self):
        for expected in (10, 20):
            form = self.entry()
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().sequence, expected)
        form = self.entry(sequence='7')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 7)

    def test_the_pattern_and_the_sequence_are_validated(self):
        for data in (
            {'pattern': '^(65001'},
            {'pattern': '^4294967296$'},
            {'sequence': '0'},
            {'action': 'maybe'},
            {'aspath': 'Missing'},
        ):
            with self.subTest(data):
                self.assertFalse(self.entry(**data).is_valid())

    def test_import_views_with_csv(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:aspath_bulk_import'),
            {'data': 'name\nfrom-csv\n', 'format': 'csv', 'csv_delimiter': ','},
        )
        self.assertEqual(response.status_code, 302)
        csv = (
            'aspath,action,pattern,sequence\n'
            'from-csv,permit,^65001_,\n'
            'from-csv,deny,^65002_,\n'
            'Path,permit,.*,5\n'
        )
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:aspathentry_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': ','},
        )
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None))
        self.assertEqual(
            list(
                ASPathEntry.objects.order_by('aspath__name', 'sequence').values_list(
                    'aspath__name', 'sequence', 'action', 'pattern'
                )
            ),
            [
                ('Path', 5, 'permit', '.*'),
                ('from-csv', 10, 'permit', '^65001_'),
                ('from-csv', 20, 'deny', '^65002_'),
            ],
        )

    def test_an_invalid_row_imports_nothing(self):
        self.client.force_login(self.user)
        csv = 'aspath,action,pattern\nPath,permit,^1$\nPath,permit,^(2\n'
        self.client.post(
            reverse('plugins:netbox_routing_protocols:aspathentry_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': ','},
        )
        self.assertFalse(ASPathEntry.objects.exists())


class ASPathImportDuplicatesTestCase(TestCase):
    def test_the_import_summarizes_entries_with_the_same_pattern(self):
        user = User.objects.create_superuser('importer', 'i@example.com', 'x')
        self.client.force_login(user)
        aspath = ASPath.objects.create(name='Path')
        ASPathEntry.objects.create(
            aspath=aspath, sequence=5, action='permit', pattern='^1$'
        )
        csv = 'aspath,action,pattern\nPath,deny,^1$\nPath,permit,^2$\nPath,permit,^2$\n'
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:aspathentry_bulk_import'),
            {'data': csv, 'format': 'csv', 'csv_delimiter': ','},
            follow=True,
        )
        texts = [str(message) for message in response.context['messages']]
        summary = [text for text in texts if 'same pattern' in text]
        self.assertEqual(len(summary), 1, texts)
        self.assertIn('AS-path Path', summary[0])
        self.assertIn('1 shadowed, 1 shadows', summary[0])
        self.assertEqual(ASPathEntry.objects.count(), 4)

    def test_no_summary_without_duplicates(self):
        user = User.objects.create_superuser('importer', 'i@example.com', 'x')
        self.client.force_login(user)
        ASPath.objects.create(name='Path')
        response = self.client.post(
            reverse('plugins:netbox_routing_protocols:aspathentry_bulk_import'),
            {
                'data': 'aspath,action,pattern\nPath,permit,^1$\nPath,permit,^2$\n',
                'format': 'csv',
                'csv_delimiter': ',',
            },
            follow=True,
        )
        texts = [str(message) for message in response.context['messages']]
        self.assertFalse([text for text in texts if 'same pattern' in text], texts)
