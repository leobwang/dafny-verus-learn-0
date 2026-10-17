"""Course feedback adapter failures, using invented tasks and no verifier."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "harness")]
from dvl.spec_feedback import SpecFeedback
from dvl import labcode
from fvh import tools


class FeedbackFailure(unittest.TestCase):
    def test_removed_verus_witness_does_not_leave_orphan_documentation(self):
        for docs in ("/// Witness.\n/// More detail.\n", "/** Witness.\n * More detail.\n */\n"):
            text = ("use vstd::prelude::*;\nverus! {\n"
                    "fn stamp(x: u64) -> (r: u64) { x }\n" + docs +
                    "#[inline]\nfn stamp_witness() { let y = stamp(2); }\n}\n")
            result = labcode.without_declaration(text, "verus", "stamp_witness")
            self.assertNotIn("Witness.", result)
            self.assertNotIn("More detail.", result)
            self.assertNotIn("#[inline]", result)
            self.assertNotIn("fn stamp_witness", result)
            self.assertIn("fn stamp(", result)
            self.assertEqual(result.count("{"), result.count("}"))

    def test_incomplete_candidate_is_recorded_without_starting_a_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "bench/local/q/lab2pub/invented/tasks/invented.dfy"
            task = root / rel
            task.parent.mkdir(parents=True)
            task.write_text("method Stamp(x: int) returns (r: int) { r := x; }\n"
                            "method StampWitness() {}\n")
            work = root / "work"
            delivery = work / rel
            delivery.parent.mkdir(parents=True)
            delivery.write_text("method Incomplete(")
            records = root / "feedback.jsonl"
            oracle = SimpleNamespace(outcome=lambda result: "failed")
            # No runner methods or oracle instrumentation exist: using either
            # would fail, rather than silently produce a successful observation.
            feedback = SpecFeedback(root, rel, runner=SimpleNamespace(isolated=True),
                                    oracle=oracle, records=records)
            result = feedback(work, (rel,), SimpleNamespace())
            self.assertEqual(result["unavailable"], "candidate-unparseable")
            self.assertEqual(result["probe_runs"], 0)
            self.assertEqual(result["witness_and_implementation"], "failed")
            self.assertIsNone(result["mutation"])
            self.assertEqual(json.loads(records.read_text())["feedback"], result)

    def test_feedback_refuses_a_host_runner(self):
        with self.assertRaises(tools.ProvenanceError):
            SpecFeedback(ROOT, "invented.dfy", runner=SimpleNamespace(isolated=False))


if __name__ == "__main__":
    unittest.main()
