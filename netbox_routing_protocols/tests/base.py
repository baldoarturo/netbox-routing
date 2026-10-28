import json
import re

import netaddr

from django.db.models import Model
from netaddr import IPNetwork

from ipam.models import RIR, ASN, VRF, IPAddress
from utilities.querysets import RestrictedQuerySet

__all__ = (
    'LeanCoreTestsMixin',
    'IPAddressFieldMixin',
    'AutomatedFormDataCreationMixin',
    'AutomatedModelCreationMixin',
    'ASNMixin',
    'VRFMixin',
    'AddressesMixin',
    'BulkEditMixin',
    'PluginBaseURLMixin',
)


# Tests NetBox's API and GUI test classes run for every model that check NetBox
# itself, identical for all of them: permissions, edge cases of the bulk API,
# GraphQL and OPTIONS. LeanCoreTestsMixin switches them off, so they run only on
# one sample model per area (the classes without the mixin) and a new model does
# not add about 25 tests that cannot fail because of the plugin.
_NETBOX_CORE_TESTS = re.compile(
    r'without_permission|anonymous|constrained_permission'
    r'|^test_graphql_'
    r'|^test_options_objects?$'
    r'|^test_update_object_with_etag$'
    r'|^test_bulk_(update|delete)_objects_'
    r'(duplicate_id|malformed_entry|nonexistent_id|string_id|validation_error|no_body)$'
    r'|^test_bulk_create_objects_invalid_item$'
)


class LeanCoreTestsMixin:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name in dir(cls):
            if _NETBOX_CORE_TESTS.search(name) and callable(getattr(cls, name, None)):
                # unittest only collects callables
                setattr(cls, name, None)


class IPAddressFieldMixin:
    def model_to_dict(self, instance, fields, api=False):
        model_dict = super().model_to_dict(instance, fields, api)
        for key, value in list(model_dict.items()):
            if api:
                if type(value) is netaddr.IPAddress:
                    model_dict[key] = str(value)
            elif not api and key in ('router_id', 'remote_router_id', 'ip_address'):
                if type(value) is netaddr.IPAddress:
                    model_dict[key] = str(value)
        return model_dict


class AutomatedModelCreationMixin:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        items = []
        for seq in range(1, 4):
            kwargs = {}
            for field in cls.routing_required_fields:
                if type(field) is tuple:
                    field, mapped_field = field
                else:
                    field, mapped_field = field, None

                if (
                    mapped_field
                    and hasattr(cls, mapped_field)
                    and isinstance(getattr(cls, mapped_field), RestrictedQuerySet)
                ):
                    kwargs[field] = getattr(cls, mapped_field)[seq - 1]
                elif (
                    mapped_field
                    and hasattr(cls, mapped_field)
                    and type(getattr(cls, mapped_field)) in [list, tuple]
                ):
                    kwargs[field] = getattr(cls, mapped_field)[seq - 1]
                elif mapped_field and hasattr(cls, mapped_field):
                    kwargs[field] = getattr(cls, mapped_field)
                elif field == 'name':
                    kwargs[field] = (f'{cls.model._meta.verbose_name}: {seq}',)
                elif field == 'sequence':
                    kwargs[field] = seq
                elif hasattr(cls, field):
                    kwargs[field] = getattr(cls, field)

            instance = cls.model(**kwargs)
            instance.full_clean()
            items.append(instance)
        cls.model.objects.bulk_create(items)


class AutomatedFormDataCreationMixin:

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        try:
            sequence = cls.model.objects.last().sequence + 1
        except Exception:
            sequence = 0

        kwargs = {}
        for field in cls.routing_required_fields:
            if type(field) is tuple:
                field, mapped_field = field
            else:
                field, mapped_field = field, None

            if (
                mapped_field
                and hasattr(cls, mapped_field)
                and isinstance(getattr(cls, mapped_field), RestrictedQuerySet)
            ):
                kwargs[field] = getattr(cls, mapped_field)[-1].pk
            elif (
                mapped_field
                and hasattr(cls, mapped_field)
                and type(getattr(cls, mapped_field)) in [list, tuple]
            ):
                kwargs[field] = getattr(cls, mapped_field)[-1]
            elif (
                mapped_field
                and hasattr(cls, mapped_field)
                and isinstance(getattr(cls, mapped_field), Model)
            ):
                kwargs[field] = getattr(cls, mapped_field).pk
            elif mapped_field and hasattr(cls, mapped_field):
                kwargs[field] = getattr(cls, mapped_field)
            elif field == 'name':
                kwargs[field] = f'{cls.model._meta.verbose_name}: {sequence}'
            elif field == 'sequence':
                kwargs[field] = sequence or 100
            elif hasattr(cls, field) and isinstance(getattr(cls, field), Model):
                kwargs[field] = getattr(cls, field).pk
            elif hasattr(cls, field) and type(getattr(cls, field)) in [
                list,
                tuple,
                dict,
            ]:
                kwargs[field] = json.dumps(getattr(cls, field))
            elif hasattr(cls, field):
                kwargs[field] = getattr(cls, field)

        cls.form_data = kwargs


class ASNMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.rir = RIR.objects.create(name='ARIN')
        for asn in range(64512, 64520):
            ASN.objects.create(rir=cls.rir, asn=asn)

        cls.asn = ASN.objects.first()
        cls.asns = ASN.objects.all()


class VRFMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for vrf_id in range(1, 11):
            VRF.objects.create(name=f'VRF {vrf_id}', rd=f'64512:{vrf_id}')

        cls.vrf = VRF.objects.first()
        cls.vrfs = VRF.objects.all()


class AddressesMixin:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(1, 11):
            IPAddress.objects.create(address=IPNetwork(f'10.0.0.{i}/24'))

        cls.ip_address = IPAddress.objects.first()
        cls.ip_addresses = IPAddress.objects.all()
        cls.peer_address = IPAddress.objects.get(address=IPNetwork('10.0.0.1/24'))
        cls.source_address = IPAddress.objects.get(address=IPNetwork('10.0.0.2/24'))


class BulkEditMixin:
    bulk_edit_data = {
        'description': 'Test Description',
    }


class PluginBaseURLMixin:
    def _get_base_url(self):
        return (
            f'plugins:{self.model._meta.app_label}:{self.model._meta.model_name}_{{}}'
        )
