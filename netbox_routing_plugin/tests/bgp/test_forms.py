from django.test import TestCase

from netbox_routing_plugin.forms.model_objects.bgp import (
    BGPPeerAddressFamilyForm,
    BGPPeerForm,
)

__all__ = ('BGPSelectorFormTestCase',)


class BGPSelectorFormTestCase(TestCase):
    """
    A selector that fails its own validation (unknown or non numeric id) has to be a
    form error, not a KeyError (HTTP 500) in clean().
    """

    cases = (
        (BGPPeerAddressFamilyForm, {}, ('peer', 'peer_group', 'address_family')),
        (BGPPeerForm, {}, ('instance', 'peer', 'peer_group')),
    )

    def test_an_invalid_selector_is_a_form_error(self):
        for form_class, data, fields in self.cases:
            for field in fields:
                for value in (999999, 'abc'):
                    with self.subTest(f'{form_class.__name__} {field}={value}'):
                        form = form_class(data={**data, field: value})
                        self.assertFalse(form.is_valid())
                        self.assertIn(field, form.errors)
