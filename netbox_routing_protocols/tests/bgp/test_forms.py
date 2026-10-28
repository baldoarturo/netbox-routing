from django.test import TestCase

from netbox_routing_protocols.forms.model_objects.bgp import (
    BGPPeerAddressFamilyForm,
    BGPRouterForm,
    BGPSettingForm,
)

__all__ = ('BGPSelectorFormTestCase',)


class BGPSelectorFormTestCase(TestCase):
    """
    The forms that assign an object through one of several selectors. A selector that fails
    its own validation (unknown or non numeric id) is missing from cleaned_data: clean() has
    to report the error of the field instead of ending in a KeyError (HTTP 500).
    """

    cases = (
        (
            BGPSettingForm,
            {'key': 'k', 'value': 'v'},
            ('router', 'scope', 'addressfamily'),
        ),
        (
            BGPRouterForm,
            {},
            (
                'region',
                'site_group',
                'site',
                'location',
                'device',
                'cluster_group',
                'cluster',
                'virtual_machine',
            ),
        ),
        (BGPPeerAddressFamilyForm, {}, ('peer', 'peer_group')),
    )

    def test_an_invalid_selector_is_a_form_error(self):
        for form_class, data, fields in self.cases:
            for field in fields:
                for value in (999999, 'abc'):
                    with self.subTest(f'{form_class.__name__} {field}={value}'):
                        form = form_class(data={**data, field: value})
                        self.assertFalse(form.is_valid())
                        self.assertIn(field, form.errors)

    def test_an_invalid_selector_does_not_add_a_misleading_error(self):
        form = BGPSettingForm(data={'key': 'k', 'value': 'v', 'router': 999999})
        self.assertFalse(form.is_valid())
        self.assertNotIn('must be assigned', str(form.errors))

    def test_no_selector_is_still_reported(self):
        form = BGPSettingForm(data={'key': 'k', 'value': 'v'})
        self.assertFalse(form.is_valid())
        self.assertIn('must be assigned to an object', str(form.errors))
        form = BGPPeerAddressFamilyForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('Peer or Peer Group', str(form.errors))

    def test_a_setting_is_valid_with_a_single_object(self):
        from netbox_routing_protocols.models import BGPRouter
        from ipam.models import ASN, RIR

        rir = RIR.objects.create(name='RIR', slug='rir')
        asn = ASN.objects.create(asn=65000, rir=rir)
        router = BGPRouter.objects.create(asn=asn)
        key = BGPSettingForm().fields['key'].choices[0][0]
        form = BGPSettingForm(data={'key': key, 'value': 'v', 'router': router.pk})
        self.assertTrue(form.is_valid(), form.errors)

    def test_the_selectors_are_optional_but_only_one_is_allowed(self):
        form = BGPSettingForm()
        for field in ('router', 'scope', 'addressfamily'):
            self.assertFalse(form.fields[field].required)
