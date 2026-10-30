from django import forms
from django.test import TestCase

from ipam.models import Prefix
from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.models.community import *

from netbox_routing_protocols.choices import ActionChoices
from netbox_routing_protocols.forms.objects import *

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

    def test_object(self):
        form = ASPathForm(
            data={
                'name': 'AS Path List 1',
                'description': 'Description',
                'comment': 'Comment',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_minimal_object(self):
        form = ASPathForm(
            data={
                'name': 'AS Path List 1',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_form_invalid(self):
        form = ASPathForm(
            data={
                'name': 'AS Path List 1 Too Long Name Needs to be over 100 characters long and enough characters to cau'
                'se an error with the form validation',
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class ASPathEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(
            name='AS Path List 1',
        )

    def test_object(self):
        form = ASPathEntryForm(
            data={
                'aspath': self.aspath,
                'sequence': 1,
                'action': ActionChoices.PERMIT,
                'pattern': '^2242$',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_form_invalid(self):
        form = ASPathEntryForm(data={'aspath': self.aspath, 'pattern': '^2242$'})
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class PrefixListTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_object(self):
        form = PrefixListForm(
            data={
                'name': 'Prefix List 1',
                'family': 4,
                'description': 'Description',
                'comment': 'Comment',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_minimal_object(self):
        form = PrefixListForm(
            data={
                'name': 'Prefix List 1',
                'family': 6,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_form_invalid(self):
        form = PrefixListForm(
            data={
                'name': 'Prefix List 1',
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()

    def test_family_is_a_radio_selector(self):
        form = PrefixListForm()
        self.assertIsInstance(form.fields['family'].widget, forms.RadioSelect)

    def test_family_cannot_be_changed(self):
        prefix_list = PrefixList.objects.create(name='Prefix List 2', family=4)
        form = PrefixListForm(
            instance=prefix_list,
            data={'name': 'Prefix List 2', 'family': 6, 'description': 'changed'},
        )
        self.assertTrue(form.fields['family'].disabled)
        self.assertTrue(form.is_valid())
        form.save()
        prefix_list.refresh_from_db()
        self.assertEqual(prefix_list.family, 4)
        self.assertEqual(prefix_list.description, 'changed')

    def test_filter_forms_have_fields(self):
        form = PrefixListFilterForm()
        self.assertTrue({'q', 'family', 'tag'} <= set(form.fields))
        form = PrefixListEntryFilterForm()
        self.assertTrue(
            {
                'q',
                'prefix_list_id',
                'family',
                'action',
                'prefix_id',
                'any_prefix',
                'ge',
                'le',
                'tag',
            }
            <= set(form.fields)
        )

    def test_bulk_edit_forms(self):
        # the family cannot be changed once defined, so it is not bulk editable
        self.assertNotIn('family', PrefixListBulkEditForm(PrefixList).fields)
        form = PrefixListEntryBulkEditForm(PrefixListEntry)
        self.assertTrue({'prefix_list', 'action', 'ge', 'le'} <= set(form.fields))
        self.assertTrue({'ge', 'le', 'description'} <= set(form.nullable_fields))


class PrefixListEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList.objects.create(
            name='Prefix List 1',
            family=4,
        )
        cls.prefix = Prefix(prefix='10.0.0.0/8')
        cls.prefix.full_clean()
        cls.prefix.save()

    def _data(self, **kwargs):
        data = {
            'prefix_list': self.prefix_list,
            'sequence': 1,
            'action': ActionChoices.PERMIT,
            'prefix': self.prefix.pk,
        }
        data.update(kwargs)
        return data

    def test_prefix(self):
        form = PrefixListEntryForm(data=self._data())
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_prefix_is_required(self):
        data = self._data()
        del data['prefix']
        form = PrefixListEntryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    def test_invalid_prefix_id_is_a_form_error(self):
        # An unknown or non-numeric id is a form error on the field, not a 500
        for value in (999999, 'abc'):
            with self.subTest(value):
                form = PrefixListEntryForm(data=self._data(prefix=value))
                self.assertFalse(form.is_valid())
                self.assertIn('prefix', form.errors)

    def test_invalid_prefix_list_is_a_form_error(self):
        form = PrefixListEntryForm(data=self._data(prefix_list=999999))
        self.assertFalse(form.is_valid())
        self.assertIn('prefix_list', form.errors)

    def test_le_above_family_boundary(self):
        form = PrefixListEntryForm(data=self._data(le=33))
        self.assertFalse(form.is_valid())
        self.assertIn('le', form.errors)

    def test_fieldsets_only_use_existing_fields(self):
        form = PrefixListEntryForm()
        shown = []
        for fieldset in form.fieldsets:
            for item in fieldset.items:
                shown.extend(getattr(item, 'items', None) or [item])
        names = {item for item in shown if isinstance(item, str)}
        self.assertLessEqual(names, set(form.fields))
        self.assertTrue({'prefix', 'ge', 'le', 'tags', 'owner'} <= names)

    def test_any_has_no_prefix_and_matches_any_length(self):
        v6_list = PrefixList.objects.create(name='Prefix List v6', family=6)
        for sequence, (prefix_list, le) in enumerate(
            ((self.prefix_list, 32), (v6_list, 128)), start=1
        ):
            with self.subTest(prefix_list.family):
                data = self._data(
                    prefix_list=prefix_list, any_prefix=True, sequence=sequence
                )
                del data['prefix']
                form = PrefixListEntryForm(data=data)
                self.assertTrue(form.is_valid(), form.errors)
                entry = form.save()
                self.assertIsNone(entry.prefix_id)
                self.assertTrue(entry.any_prefix)
                self.assertEqual((entry.ge, entry.le), (None, le))
        # nothing is created in IPAM
        self.assertFalse(
            Prefix.objects.filter(prefix__in=['0.0.0.0/0', '::/0']).exists()
        )

    def test_any_keeps_explicit_ge_le(self):
        data = self._data(any_prefix=True, ge=24)
        del data['prefix']
        form = PrefixListEntryForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual((entry.ge, entry.le), (24, None))

    def test_prefix_or_any_is_required(self):
        data = self._data()
        del data['prefix']
        form = PrefixListEntryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    def test_any_option_is_shown_with_the_prefix(self):
        form = PrefixListEntryForm()
        self.assertIn('any_prefix', form.fields)
        self.assertFalse(form.fields['prefix'].required)

    def test_sequence_is_assigned_when_empty(self):
        for expected in (10, 20):
            data = self._data()
            del data['sequence']
            form = PrefixListEntryForm(data=data)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.save().sequence, expected)

    def test_sequence_cannot_be_emptied_when_editing(self):
        entry = PrefixListEntryForm(data=self._data(sequence=5))
        entry = entry.save() if entry.is_valid() else None
        form = PrefixListEntryForm(data=self._data(sequence=''), instance=entry)
        self.assertTrue(form.fields['sequence'].required)
        self.assertFalse(form.is_valid())
        self.assertIn('sequence', form.errors)
        entry.refresh_from_db()
        self.assertEqual(entry.sequence, 5)

    def test_arbitrary_sequence_is_kept(self):
        form = PrefixListEntryForm(data=self._data(sequence=7))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 7)

    def test_sequence_is_suggested_for_a_known_list(self):
        form = PrefixListEntryForm(initial={'prefix_list': self.prefix_list.pk})
        self.assertEqual(form.initial['sequence'], 10)
        self.assertFalse(form.fields['sequence'].required)
        form = PrefixListEntryForm(data=self._data(sequence=25))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        form = PrefixListEntryForm(initial={'prefix_list': str(self.prefix_list.pk)})
        self.assertEqual(form.initial['sequence'], 30)
        # nothing to suggest without a list, or when editing
        self.assertNotIn('sequence', PrefixListEntryForm().initial)
        entry = PrefixListEntry.objects.get()
        self.assertEqual(PrefixListEntryForm(instance=entry).initial['sequence'], 25)

    def test_exact_keeps_ge_and_le_empty(self):
        form = PrefixListEntryForm(data=self._data(exact=True))
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual((entry.ge, entry.le), (None, None))

    def test_exact_excludes_ge_le(self):
        for extra in ({'ge': 16}, {'le': 24}):
            with self.subTest(extra):
                form = PrefixListEntryForm(data=self._data(exact=True, **extra))
                self.assertFalse(form.is_valid())
                self.assertIn('exact', form.errors)

    def test_exact_inputs_are_disabled_in_the_page(self):
        form = PrefixListEntryForm(data=self._data(exact=True))
        self.assertIn('disabled', str(form['ge']))
        self.assertNotIn('disabled', str(PrefixListEntryForm()['le']))
        self.assertIn('id_ge', form.fields['exact'].widget.attrs['onchange'])

    def test_any_and_exact_is_only_the_all_zeros_prefix(self):
        data = self._data(any_prefix=True, exact=True)
        del data['prefix']
        form = PrefixListEntryForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        entry = form.save()
        self.assertEqual((entry.ge, entry.le), (None, None))

    def test_form_invalid(self):
        form = PrefixListEntryForm(data={'prefix_list': self.prefix_list})
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class RoutePolicyTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_object(self):
        form = RoutePolicyForm(
            data={
                'name': 'Route Policy 1',
                'description': 'Description',
                'comment': 'Comment',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_minimal_object(self):
        form = RoutePolicyForm(
            data={
                'name': 'Route Policy 1',
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())

    def test_form_invalid(self):
        form = RoutePolicyForm(
            data={
                'name': 'Route Policy 1 Too Long Name Needs to be over 100 characters long and enough characters to cau'
                'se an error with the form validation',
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class RoutePolicyEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route_policy = RoutePolicy.objects.create(
            name='Route Policy 1',
        )
        cls.community_list = CommunityList.objects.create(name='List')

    def test_object(self):
        form = RoutePolicyEntryForm(
            data={
                'route_policy': self.route_policy,
                'sequence': 1,
                'action': ActionChoices.PERMIT,
                'match_prefix_list': [],
                'match_community_list': [self.community_list.pk],
                'match_aspath': [],
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())
        self.assertEqual(
            list(form.instance.match_community_list.all()),
            [
                self.community_list,
            ],
        )

    def test_form_invalid(self):
        form = RoutePolicyEntryForm(
            data={
                'route_policy': self.route_policy,
            }
        )
        self.assertFalse(form.is_valid())
        with self.assertRaises(ValueError):
            form.save()


class PrefixListFormWidgetsTestCase(TestCase):
    def test_family_radios_are_not_form_controls(self):
        html = str(PrefixListForm()['family'])
        self.assertEqual(html.count('type="radio"'), 2)
        self.assertEqual(html.count('form-check-input'), 2)
        self.assertNotIn('form-control', html)

    def test_a_new_entry_permits_by_default(self):
        form = PrefixListEntryForm()
        self.assertEqual(form['action'].value(), ActionChoices.PERMIT)
