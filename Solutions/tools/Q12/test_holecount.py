"""The reference toolwright's acceptance tests (Q12, rung 10): the reference twin of
tools/Q12/holecount.py run over the course's recorded documents (harness/tests/q/fixtures/,
learner-visible), each expected object written out by hand from the fixture. Author-only,
beside its twin; `python3 Solutions/tools/Q12/test_holecount.py` (scripts/ci.sh --author's
harness job runs it). A learner's own tests (tools/Q12/test_holecount.py) are theirs."""

import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIX = ROOT / "harness" / "tests" / "q" / "fixtures" / "q09"
sys.path.insert(0, str(HERE))
import holecount  # noqa: E402


def run(*paths, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    code = holecount.main([str(p) for p in paths], io.StringIO(stdin), out, err)
    return code, [json.loads(x) for x in out.getvalue().splitlines()], err.getvalue()


class Holecount(unittest.TestCase):
    def test_verified_with_no_finding(self):
        code, rows, err = run(FIX / "dafny/C-01/vcheck-gate.json", FIX / "dafny/C-01/vaudit.json")
        self.assertEqual(code, 0, err)
        self.assertEqual(rows, [{"file": "<root>/tests/corpus/dafny/C-01/main.dfy", "holes": {},
                                 "hole_count": 0, "findings": {}, "verdict": "verified"}])

    def test_holes_by_kind(self):
        code, rows, _ = run(FIX / "dafny/D-09/vcheck-gate.json")
        self.assertEqual(code, 0)
        self.assertEqual(rows[0]["holes"], {"bodyless-method": 2})
        self.assertEqual((rows[0]["hole_count"], rows[0]["verdict"]), (2, "failed"))
        self.assertEqual(rows[0]["findings"], {})       # vcheck's own findings are not the audit's

    def test_a_verified_file_with_assumptions(self):
        code, rows, _ = run(FIX / "dafny/D-02/vcheck-gate.json", FIX / "dafny/D-02/vaudit.json")
        self.assertEqual(code, 0)
        self.assertEqual(rows, [{"file": "<root>/tests/corpus/dafny/D-02/main.dfy", "holes": {},
                                 "hole_count": 0,
                                 "findings": {"audit-axiom": 1, "axiom-attribute": 1},
                                 "verdict": "verified"}])

    def test_a_crate_and_sorted_targets(self):
        code, rows, _ = run(FIX / "verus/V-8/vcheck-gate.json", FIX / "dafny/D-09/vcheck-gate.json")
        self.assertEqual(code, 0)
        self.assertEqual([r["file"] for r in rows], ["<root>/tests/corpus/dafny/D-09/main.dfy",
                                                     "<root>/tests/corpus/verus/V-8"])
        self.assertEqual(rows[1]["holes"], {"external_trait_specification": 1})

    def test_a_bare_document_on_stdin(self):
        doc = json.loads((FIX / "dafny/D-09/vcheck-gate.json").read_text())["document"]
        code, rows, _ = run(stdin=json.dumps(doc))
        self.assertEqual((code, rows[0]["hole_count"]), (0, 2))

    def test_unreadable_input_is_never_zero(self):
        doc = json.loads((FIX / "dafny/D-09/vcheck-gate.json").read_text())["document"]
        del doc["holes"]
        code, rows, err = run(stdin=json.dumps(doc))
        self.assertEqual((code, rows), (1, []))
        self.assertIn("holes", err)
        code, rows, err = run(FIX / "dafny/C-01/vaudit.json", HERE / "no-such-file.json")
        self.assertEqual(code, 1)
        self.assertEqual(len(rows), 1)                  # the readable input still printed
        self.assertIn("no-such-file.json", err)

    def test_it_reads_documents_only(self):
        src = (HERE / "holecount.py").read_text().split("\nimport json\n", 1)[1]   # the code
        for word in ("subprocess", "os.system", "scripts/vcheck", "open(doc", "read_text"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main()
