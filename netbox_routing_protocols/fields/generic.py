from django.contrib.contenttypes.fields import GenericRelation, GenericRel
from django.db import DEFAULT_DB_ALIAS
from django.db.models import ProtectedError


class NetBoxGenericRel(GenericRel):
    def value_from_object(self, obj):
        """Return the value of this field in the given model instance."""
        if value := getattr(obj, self.related_name).first():
            return value.pk
        return None


class NetBoxGenericRelation(GenericRelation):
    rel_class = NetBoxGenericRel


class ProtectedGenericRelation(NetBoxGenericRelation):
    """
    A generic relation that behaves like on_delete=PROTECT: deleting an object that
    is still referenced raises ProtectedError instead of cascading to the referrers.
    """

    def bulk_related_objects(self, objs, using=DEFAULT_DB_ALIAS):
        referrers = list(super().bulk_related_objects(objs, using))
        if referrers:
            raise ProtectedError(
                f'Cannot delete the selected objects because they are used by '
                f'{self.related_model._meta.verbose_name_plural}.',
                referrers,
            )
        return referrers
