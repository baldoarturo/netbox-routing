from django.apps import apps
from django.test import TestCase

from netbox.registry import registry

__all__ = ('SearchCoverageTestCase',)

APP_LABEL = 'netbox_routing_plugin'

# Fields that hold a secret: they must never reach the search cache
SECRET_FIELDS = ('passphrase', 'password', 'secret')


def _models():
    for model in apps.get_app_config(APP_LABEL).get_models():
        if not model._meta.abstract and not model._meta.auto_created:
            yield model


class SearchCoverageTestCase(TestCase):
    def test_every_model_of_the_plugin_is_indexed(self):
        missing = [
            model.__name__
            for model in _models()
            if model._meta.label_lower not in registry['search']
        ]
        self.assertEqual(missing, [], f'models without a search index: {missing}')

    def test_the_indexed_fields_exist(self):
        for model in _models():
            index = registry['search'][model._meta.label_lower]
            for field, _weight in index.fields:
                with self.subTest(model=model.__name__, field=field):
                    # a model field, or an attribute computed by the model
                    self.assertTrue(
                        hasattr(model, field)
                        or field in {f.name for f in model._meta.get_fields()}
                    )

    def test_no_secret_is_indexed(self):
        for model in _models():
            index = registry['search'][model._meta.label_lower]
            for field, _weight in index.fields:
                with self.subTest(model=model.__name__, field=field):
                    self.assertNotIn(field, SECRET_FIELDS)
