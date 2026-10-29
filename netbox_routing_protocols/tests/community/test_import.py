from django.test import TestCase

from netbox_routing_protocols.forms.bulk_import.community import *
from netbox_routing_protocols.models.community import *

__all__ = ('CommunityImportTestCase',)


class CommunityImportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lst = CommunityList.objects.create(name='L')
        cls.ext = CommunityList.objects.create(name='E', type='extended')
        cls.standard = Community.objects.create(community='65000:1')
        cls.extended = Community.objects.create(community='rt:65000:1')

    def entry_form(self, **data):
        base = {'community_list': 'L', 'community': '65000:1', 'action': 'permit'}
        return CommunityListEntryImportForm(data={**base, **data})

    def test_an_empty_sequence_takes_the_next_one(self):
        for expected in (10, 20):
            form = self.entry_form()
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().sequence, expected)

    def test_a_given_sequence_is_kept(self):
        form = self.entry_form(sequence='5')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 5)

    def test_a_community_of_another_type_is_rejected(self):
        form = self.entry_form(community='rt:65000:1')
        self.assertFalse(form.is_valid())
        self.assertIn('community', form.errors)
        form = self.entry_form(community_list='E', community='rt:65000:1')
        self.assertTrue(form.is_valid(), form.errors)

    def test_a_taken_sequence_is_rejected(self):
        self.entry_form(sequence='10').save()
        form = self.entry_form(sequence='10', action='deny')
        self.assertFalse(form.is_valid())

    def test_the_type_of_a_list(self):
        form = CommunityListImportForm(data={'name': 'Large', 'type': 'large'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().type, 'large')
        form = CommunityListImportForm(data={'name': 'Plain'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().type, 'standard')

    def test_a_community_is_normalised_on_import(self):
        form = CommunityImportForm(data={'community': 'No-Export', 'status': 'active'})
        self.assertTrue(form.is_valid(), form.errors)
        community = form.save()
        self.assertEqual(
            (community.community, community.type), ('65535:65281', 'standard')
        )
        form = CommunityImportForm(data={'community': '70000:1', 'status': 'active'})
        self.assertFalse(form.is_valid())
