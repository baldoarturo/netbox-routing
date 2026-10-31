from django.test import TestCase

import netaddr

from ipam.models import Prefix
from netbox_routing_plugin.helpers.prefix_list import (
    describe_entry,
    entry_matches,
    evaluate_prefix,
    find_overlaps,
    match_range,
)
from netbox_routing_plugin.models.objects import *

__all__ = ('PrefixListHelpersTestCase',)


class PrefixListHelpersTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList.objects.create(name='List', family=4)
        cls.v6_list = PrefixList.objects.create(name='List v6', family=6)

    def entry(self, sequence, prefix=None, action='permit', prefix_list=None, **kwargs):
        if prefix is not None:
            prefix = Prefix.objects.filter(
                prefix=prefix
            ).first() or Prefix.objects.create(prefix=prefix)
        return PrefixListEntry.objects.create(
            prefix_list=prefix_list or self.prefix_list,
            sequence=sequence,
            action=action,
            prefix=prefix,
            any_prefix=prefix is None,
            **kwargs,
        )

    def test_match_range(self):
        for kwargs, expected in (
            ({}, (8, 8)),
            ({'le': 24}, (8, 24)),
            ({'ge': 16}, (16, 32)),
            ({'ge': 16, 'le': 24}, (16, 24)),
            ({'ge': 8, 'le': 8}, (8, 8)),
        ):
            with self.subTest(kwargs):
                entry = self.entry(1, '10.0.0.0/8', **kwargs)
                self.assertEqual(match_range(entry), expected)
                entry.delete()

    def test_match_range_of_any(self):
        self.assertEqual(match_range(self.entry(1, le=32)), (0, 32))
        self.assertEqual(match_range(self.entry(2)), (0, 0))
        self.assertEqual(
            match_range(self.entry(3, prefix_list=self.v6_list, ge=64)), (64, 128)
        )

    def test_entry_matches(self):
        entry = self.entry(1, '10.0.0.0/8', ge=16, le=24)
        for value, expected in (
            ('10.1.0.0/16', True),
            ('10.1.2.0/24', True),
            ('10.1.2.0/25', False),
            ('10.0.0.0/8', False),
            ('11.1.0.0/16', False),
            ('2001:db8::/32', False),
        ):
            with self.subTest(value):
                self.assertEqual(
                    entry_matches(entry, netaddr.IPNetwork(value)), expected
                )
        any_entry = self.entry(2, le=32)
        self.assertTrue(entry_matches(any_entry, netaddr.IPNetwork('192.0.2.0/24')))
        self.assertFalse(entry_matches(any_entry, netaddr.IPNetwork('2001:db8::/32')))
        exact = self.entry(3, '10.0.0.0/8')
        self.assertTrue(entry_matches(exact, netaddr.IPNetwork('10.0.0.0/8')))
        self.assertFalse(entry_matches(exact, netaddr.IPNetwork('10.1.0.0/16')))

    def kinds(self, entry):
        return {
            overlap.entry.sequence: overlap.kind for overlap in find_overlaps(entry)
        }

    def test_duplicate(self):
        a = self.entry(10, '10.0.0.0/8', ge=16)
        b = self.entry(20, '10.0.0.0/8', ge=16, le=32, action='deny')
        self.assertEqual(self.kinds(a), {20: 'duplicate'})
        self.assertEqual(self.kinds(b), {10: 'duplicate'})

    def test_shadowed_and_shadows(self):
        broad = self.entry(10, '10.0.0.0/8', le=32)
        narrow = self.entry(20, '10.1.0.0/16', le=24)
        self.assertEqual(self.kinds(narrow), {10: 'shadowed'})
        self.assertEqual(self.kinds(broad), {20: 'shadows'})

    def test_specific_first_is_nested(self):
        narrow = self.entry(10, '10.1.0.0/16', le=24, action='deny')
        broad = self.entry(20, '10.0.0.0/8', le=32)
        self.assertEqual(self.kinds(narrow), {20: 'nested'})
        self.assertEqual(self.kinds(broad), {10: 'nested'})

    def test_partial_overlap(self):
        a = self.entry(10, '10.0.0.0/8', le=16)
        b = self.entry(20, '10.1.0.0/16', ge=16, le=24)
        # the lengths 16 are common, but neither covers the other
        self.assertEqual(self.kinds(a), {20: 'overlaps'})
        self.assertEqual(self.kinds(b), {10: 'overlaps'})

    def test_no_overlap(self):
        a = self.entry(10, '10.0.0.0/8')
        for kwargs in (
            {'prefix': '11.0.0.0/8'},  # disjoint networks
            {'prefix': '10.1.0.0/16'},  # nested, but the lengths never meet
            {'prefix': '2001:db8::/32', 'prefix_list': self.v6_list},
        ):
            self.entry(20 + len(kwargs['prefix']), **kwargs)
        self.assertEqual(self.kinds(a), {})

    def test_any_overlaps_everything_of_the_family(self):
        any_entry = self.entry(10, le=32)
        specific = self.entry(20, '10.0.0.0/8', le=24)
        self.assertEqual(self.kinds(specific), {10: 'shadowed'})
        self.assertEqual(self.kinds(any_entry), {20: 'shadows'})

    def test_a_new_entry_is_compared_with_the_saved_ones(self):
        self.entry(10, '10.0.0.0/8', le=32)
        new = PrefixListEntry(
            prefix_list=self.prefix_list,
            sequence=20,
            action='deny',
            prefix=Prefix.objects.create(prefix='10.1.0.0/16'),
        )
        self.assertEqual(self.kinds(new), {10: 'shadowed'})

    def test_describe_entry(self):
        self.assertEqual(
            describe_entry(self.entry(10, '10.0.0.0/8', ge=16, le=24)),
            '10 permit 10.0.0.0/8 ge 16 le 24',
        )
        self.assertEqual(
            describe_entry(self.entry(20, le=32, action='deny')), '20 deny any le 32'
        )

    def test_evaluate_prefix_orders_by_sequence_and_marks_the_first(self):
        self.entry(10, '10.1.0.0/16', le=24, action='deny')
        self.entry(20, '10.0.0.0/8', le=32)
        other = PrefixList.objects.create(name='Other', family=4)
        self.entry(5, le=32, prefix_list=other)
        entries = PrefixListEntry.objects.select_related('prefix_list', 'prefix')
        results = evaluate_prefix(netaddr.IPNetwork('10.1.2.0/24'), entries)
        self.assertEqual(
            [
                (pl.name, [(e.sequence, first) for e, first in rows])
                for pl, rows in results
            ],
            [('List', [(10, True), (20, False)]), ('Other', [(5, True)])],
        )
        self.assertEqual(
            evaluate_prefix(netaddr.IPNetwork('192.0.2.0/24'), entries)[0][0].name,
            'Other',
        )
