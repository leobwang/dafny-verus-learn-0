"""The named-call gate (the user's D90): every library-call item that opts in with
`// gate: named-calls` is recorded mechanically in its reference twin, so the
module-wide reading of R07's short library holes is checked, not just stated.

The static half (scripts/named_call_gate.py) is checked here on the committed
twins and on small invented twin files; the dynamic half (each recorded `cfree:`
answer fails verification) is the empty-body gate's forms check, which runs in
the empty-body job and in `scripts/firsttry.sh <ID> --empty-body`.

Run: python3 -B -m unittest discover -s tests/ci -p 'test_named_call_gate.py'
"""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("named_call_gate", ROOT / "scripts" / "named_call_gate.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

GOOD = """module X {
  // item: R99.H1d
  // uses: library-call
  // gate: named-calls
  lemma A(xs: seq<int>)
    ensures P(xs)
  {
    // @hole-begin R99.H1d
    S.LemmaOne(xs);  // found-by: grep
    S.LemmaTwo(xs);  // found-by: docs
    // @hole-end R99.H1d
  }
  // cfree: { S.LemmaTwo(xs); }
  // cfree: { S.LemmaOne(xs); }
}
"""


def run_on(text):
    d = Path(tempfile.mkdtemp(prefix="ncg-"))
    try:
        p = d / "Solutions" / "dafny" / "R" / "R99_X" / "R99_X.dfy"
        p.parent.mkdir(parents=True)
        p.write_text(text, encoding="utf-8")
        return G.check(d)
    finally:
        shutil.rmtree(d)


class Committed(unittest.TestCase):
    def test_every_gated_twin_item_is_recorded(self):
        gated, probs = G.check(ROOT)
        self.assertEqual(probs, [])
        for iid in ("R07.T1d", "R07.H1d", "R07.H2d", "R07.H3d",
                    "R07.T1v", "R07.H1v", "R07.H2v", "R07.H3v", "R07.H4v", "R07.H5v"):
            self.assertIn(iid, gated, f"{iid} carries no `gate: named-calls` record")


class Fixtures(unittest.TestCase):
    def test_a_recorded_item_passes(self):
        gated, probs = run_on(GOOD)
        self.assertEqual((gated, probs), (["R99.H1d"], []))

    def test_a_missing_removal_answer_is_refused(self):
        gated, probs = run_on(GOOD.replace("  // cfree: { S.LemmaOne(xs); }\n", ""))
        self.assertEqual(len(probs), 1)
        self.assertIn("removes exactly its call number 2 of 2", probs[0])

    def test_a_call_without_found_by_is_refused(self):
        gated, probs = run_on(GOOD.replace("S.LemmaTwo(xs);  // found-by: docs", "S.LemmaTwo(xs);"))
        self.assertEqual(len(probs), 1)
        self.assertIn("no `// found-by:` note", probs[0])

    def test_an_answer_that_removes_nothing_does_not_count(self):
        text = GOOD.replace("  // cfree: { S.LemmaTwo(xs); }\n",
                            "  // cfree: { S.LemmaOne(xs); S.LemmaTwo(xs); }\n")
        gated, probs = run_on(text)
        self.assertEqual(len(probs), 1)
        self.assertIn("call number 1 of 2", probs[0])

    def test_an_ungated_item_is_not_checked(self):
        gated, probs = run_on(GOOD.replace("  // gate: named-calls\n", "").replace("  // cfree: { S.LemmaOne(xs); }\n", ""))
        self.assertEqual((gated, probs), ([], []))

    def test_a_gated_item_without_a_hole_region_is_refused(self):
        text = GOOD.replace("    // @hole-begin R99.H1d\n", "").replace("    // @hole-end R99.H1d\n", "")
        gated, probs = run_on(text)
        self.assertEqual(len(probs), 1)
        self.assertIn("holds no `@hole-begin R99.H1d` region", probs[0])


if __name__ == "__main__":
    unittest.main()
