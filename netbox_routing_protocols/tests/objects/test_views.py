from django.db.models import ForeignKey

from ipam.models import Prefix
from utilities.testing import ViewTestCases

from netbox_routing_protocols.models.objects import *
from netbox_routing_protocols.tests.base import (
    LeanCoreTestsMixin,
    AutomatedModelCreationMixin,
    AutomatedFormDataCreationMixin,
    BulkEditMixin,
)
from netbox_routing_protocols.tests.objects.base import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RouteMapTestCase',
    'RouteMapEntryTestCase',
)


class NBRObjectMixin:

    @classmethod
    def setUpTestData(cls):
        name = cls.model._meta.verbose_name
        items = []

        for seq in range(1, 4):
            items.append(
                cls.model(
                    name=f'{name} {seq}',
                ),
            )
        cls.model.objects.bulk_create(items)

        cls.form_data = {
            'name': f'{name} 4',
        }

        cls.bulk_edit_data = {
            'description': 'Test Description',
        }


class NBRObjectEntryMixin:

    @classmethod
    def setUpTestData(cls):
        parent_field = None
        parent = None
        for parent_field in cls.model._meta.fields:
            if isinstance(parent_field, ForeignKey) and parent_field.name != 'owner':
                parent = parent_field.related_model(
                    name=parent_field.related_model._meta.verbose_name
                )
                parent.full_clean()
                parent.save()
                break

        items = []
        for seq in range(1, 4):
            args = {
                parent_field.name: parent,
                'action': 'permit',
                'sequence': seq,
                cls.key_field: cls.key_value,
            }
            items.append(
                cls.model(**args),
            )
        cls.model.objects.bulk_create(items)

        cls.form_data = {
            parent_field.name: parent.pk,
            'action': 'permit',
            'sequence': 9999,
            cls.key_field: cls.key_value,
        }

        cls.bulk_edit_data = {
            'description': 'Test Description',
        }


class ASPathTestCase(
    LeanCoreTestsMixin,
    AutomatedModelCreationMixin,
    AutomatedFormDataCreationMixin,
    BulkEditMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = ASPath

    routing_required_fields = ('name',)

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:aspath_{}'


class ASPathEntryTestCase(
    LeanCoreTestsMixin,
    AutomatedModelCreationMixin,
    AutomatedFormDataCreationMixin,
    BulkEditMixin,
    ASPathMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = ASPathEntry

    action = 'permit'
    pattern = '^.*$'
    routing_required_fields = ('aspath', 'pattern', 'sequence', 'action')

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:aspathentry_{}'


class PrefixListTestCase(
    LeanCoreTestsMixin,
    AutomatedModelCreationMixin,
    AutomatedFormDataCreationMixin,
    BulkEditMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = PrefixList

    family = 4
    routing_required_fields = (
        'name',
        'family',
    )

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:prefixlist_{}'


class PrefixListEntryTestCase(
    AutomatedModelCreationMixin,
    AutomatedFormDataCreationMixin,
    BulkEditMixin,
    PrefixListMixin,
    NBRObjectEntryMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = PrefixListEntry

    action = 'permit'
    routing_required_fields = (
        'prefix_list',
        ('prefix', 'prefixes'),
        'sequence',
        'action',
    )

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:prefixlistentry_{}'

    @classmethod
    def setUpTestData(cls):
        cls.prefix = Prefix.objects.create(prefix='10.0.0.0/8')
        cls.prefixes = [cls.prefix] * 10

        super().setUpTestData()

        cls.form_data['prefix'] = cls.form_data['prefix'].pk


class RouteMapTestCase(
    LeanCoreTestsMixin,
    AutomatedFormDataCreationMixin,
    AutomatedModelCreationMixin,
    BulkEditMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = RouteMap
    routing_required_fields = ('name',)

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:routemap_{}'


class RouteMapEntryTestCase(
    LeanCoreTestsMixin,
    AutomatedFormDataCreationMixin,
    AutomatedModelCreationMixin,
    RouteMapMixin,
    BulkEditMixin,
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    # ViewTestCases.BulkImportObjectsViewTestCase,
    model = RouteMapEntry
    action = 'permit'
    set = {}
    match = {
        'tags': 1234,
    }
    routing_required_fields = ('match', 'set', 'route_map', 'action', 'sequence')

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def _get_base_url(self):
        return 'plugins:netbox_routing_protocols:routemapentry_{}'
