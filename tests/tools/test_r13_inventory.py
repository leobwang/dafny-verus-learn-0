"""R13 delivery view: source provenance, half isolation and evaluator blindness."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r13_inventory',ROOT/'tools/R13/inventory.py')
inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)

class InventoryTests(unittest.TestCase):
    def test_fixed_draw_is_only_r_and_has_original_bytes(self):
        import hashlib
        view=inv.inventory()
        self.assertEqual(len(view['deliveries']),12)
        self.assertEqual({(d['lang'],d['id']) for d in view['deliveries']},inv.DRAW)
        for d in view['deliveries']:
            self.assertEqual(d['half'],'R')
            self.assertTrue(d['source_available'])
            for p,sha in d['files_sha256'].items():
                self.assertEqual(sha,hashlib.sha256((ROOT/p).read_bytes()).hexdigest())

    def test_labels_are_never_inspected_or_published(self):
        original=inv.load_half
        class DeliveryOnly:
            def __init__(self,f): self.delivery=f.delivery
            @property
            def label(self): raise AssertionError('evaluator-only labels read')
        def stripped(*a,**kw):return tuple(DeliveryOnly(f) for f in original(*a,**kw))
        with patch.object(inv,'load_half',stripped):
            view=inv.inventory(all_rows=True)
        for d in view['deliveries']:
            self.assertEqual(set(d),{'id','lang','half','target','files_sha256','source_available'})
        self.assertEqual(len(view['deliveries']),52)
        self.assertTrue(any(not d['source_available'] for d in view['deliveries']))

    def test_fixed_draw_cannot_silently_drop_a_missing_delivery(self):
        with patch.object(inv,'load_half',return_value=()):
            with self.assertRaisesRegex(ValueError,'incomplete'):inv.inventory()

    def test_delivery_path_cannot_leave_fixture(self):
        from types import SimpleNamespace
        fake=SimpleNamespace(delivery=SimpleNamespace(id='G02',lang='dafny',half='R',
                              target='CLAUDE.md',files=('CLAUDE.md',)))
        with patch.object(inv,'load_half',return_value=(fake,)):
            with self.assertRaisesRegex(ValueError,'leaves its fixture'):inv.inventory(all_rows=True)
if __name__=='__main__':unittest.main()
