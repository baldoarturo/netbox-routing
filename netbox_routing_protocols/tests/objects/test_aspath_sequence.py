import uuid

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

from netbox.context import current_request
from users.models import User
from utilities.testing import APITestCase

from netbox_routing_protocols.forms.objects import ASPathEntryForm
from netbox_routing_protocols.helpers.aspath import find_duplicates, next_sequence
from netbox_routing_protocols.models.objects import *


def make_entry(aspath, sequence, pattern, action='permit'):
    return ASPathEntry.objects.create(
        aspath=aspath, sequence=sequence, action=action, pattern=pattern
    )


class ASPathHelpersTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Path')

    def test_next_sequence(self):
        self.assertEqual(next_sequence(self.aspath), 10)
        make_entry(self.aspath, 10, '^1$')
        self.assertEqual(next_sequence(self.aspath), 20)
        make_entry(self.aspath, 25, '^2$')
        self.assertEqual(next_sequence(self.aspath), 30)
        self.assertEqual(next_sequence(self.aspath, after=40), 50)

    def test_duplicates(self):
        first = make_entry(self.aspath, 10, '^65001_')
        second = make_entry(self.aspath, 20, ' ^65001_ ', 'deny')
        other = make_entry(self.aspath, 30, '^65002_')
        self.assertEqual(
            [(d.kind, d.entry) for d in find_duplicates(second)],
            [('shadowed', first)],
        )
        self.assertEqual(
            [(d.kind, d.entry) for d in find_duplicates(first)],
            [('shadows', second)],
        )
        self.assertIn('never reached', find_duplicates(second)[0].message)
        self.assertEqual(find_duplicates(other), [])


class ASPathEntryFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Path')

    def request(self):
        request = RequestFactory().get('/')
        request.user = User.objects.create_superuser('f', 'f@example.com', 'x')
        request.id = uuid.uuid4()
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_sequence_is_suggested_and_assigned(self):
        make_entry(self.aspath, 10, '^1$')
        form = ASPathEntryForm(initial={'aspath': self.aspath.pk})
        self.assertEqual(form.initial['sequence'], 20)
        form = ASPathEntryForm(
            data={'aspath': self.aspath.pk, 'action': 'permit', 'pattern': '^2$'}
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().sequence, 20)

    def test_saving_a_duplicate_warns_but_saves(self):
        make_entry(self.aspath, 10, '^1$')
        request = self.request()
        token = current_request.set(request)
        try:
            form = ASPathEntryForm(
                data={
                    'aspath': self.aspath.pk,
                    'sequence': 20,
                    'action': 'deny',
                    'pattern': '^1$',
                }
            )
            self.assertTrue(form.is_valid(), form.errors)
            entry = form.save()
        finally:
            current_request.reset(token)
        self.assertTrue(ASPathEntry.objects.filter(pk=entry.pk).exists())
        texts = [str(message) for message in request._messages]
        self.assertEqual(len(texts), 1)
        self.assertIn('never reached', texts[0])


class ASPathEntryAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath.objects.create(name='Path')
        cls.other = ASPath.objects.create(name='Other')

    def url(self):
        return reverse('plugins-api:netbox_routing_protocols-api:aspathentry-list')

    def post(self, data):
        return self.client.post(self.url(), data, format='json', **self.header)

    def test_empty_sequence_takes_the_next_one(self):
        self.add_permissions('netbox_routing_protocols.add_aspathentry')
        data = {'aspath': self.aspath.pk, 'action': 'permit', 'pattern': '^1$'}
        response = self.post(data)
        self.assertHttpStatus(response, 201)
        self.assertEqual(response.data['sequence'], 10)
        response = self.post({**data, 'pattern': '^2$'})
        self.assertEqual(response.data['sequence'], 20)

    def test_bulk_entries_are_consecutive(self):
        self.add_permissions('netbox_routing_protocols.add_aspathentry')
        rows = [
            {'aspath': self.aspath.pk, 'action': 'permit', 'pattern': f'^{n}$'}
            for n in range(3)
        ] + [{'aspath': self.other.pk, 'action': 'permit', 'pattern': '^9$'}]
        response = self.post(rows)
        self.assertHttpStatus(response, 201)
        self.assertEqual([row['sequence'] for row in response.data], [10, 20, 30, 10])

    def test_duplicate_is_saved_with_a_warning(self):
        self.add_permissions('netbox_routing_protocols.add_aspathentry')
        make_entry(self.aspath, 10, '^1$')
        response = self.post(
            {
                'aspath': self.aspath.pk,
                'sequence': 20,
                'action': 'deny',
                'pattern': '^1$',
            }
        )
        self.assertHttpStatus(response, 201)
        warnings = response.data['warnings']
        self.assertEqual([w['kind'] for w in warnings], ['shadowed'])
        self.assertEqual(warnings[0]['entry']['sequence'], 10)


class ASPathEntryPageTestCase(TestCase):
    def test_the_page_lists_entries_with_the_same_pattern(self):
        User.objects.create_superuser('page', 'page@example.com', 'x')
        self.client.login(username='page', password='x')
        aspath = ASPath.objects.create(name='Path')
        make_entry(aspath, 10, '^1$')
        second = make_entry(aspath, 20, '^1$')
        response = self.client.get(second.get_absolute_url())
        self.assertContains(response, 'Entries with the same pattern')
        self.assertContains(response, 'shadowed')


class ASPathAPIFieldsTestCase(APITestCase):
    """Tags, custom fields, owner and timestamps are read and written over the API"""

    def post(self, name, data):
        return self.client.post(
            reverse(f'plugins-api:netbox_routing_protocols-api:{name}-list'),
            data,
            format='json',
            **self.header,
        )

    def test_fields_of_the_aspath_and_the_entry(self):
        from extras.models import Tag

        self.add_permissions(
            'netbox_routing_protocols.add_aspath',
            'netbox_routing_protocols.add_aspathentry',
            'extras.view_tag',
        )
        tag = Tag.objects.create(name='edge', slug='edge')
        response = self.post('aspath', {'name': 'API', 'tags': [{'name': 'edge'}]})
        self.assertHttpStatus(response, 201)
        for field in ('owner', 'tags', 'custom_fields', 'created', 'last_updated'):
            self.assertIn(field, response.data)
        self.assertEqual([t['name'] for t in response.data['tags']], ['edge'])
        response = self.post(
            'aspathentry',
            {
                'aspath': response.data['id'],
                'action': 'permit',
                'pattern': '^1$',
                'tags': [tag.pk],
            },
        )
        self.assertHttpStatus(response, 201)
        for field in ('owner', 'tags', 'custom_fields', 'created', 'last_updated'):
            self.assertIn(field, response.data)
        self.assertEqual([t['name'] for t in response.data['tags']], ['edge'])
