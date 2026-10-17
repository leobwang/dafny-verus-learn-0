"""scripts/dvl/benchstrip.py: the content transforms of get_bench.sh's
normalizer (QPLAN §30 Q57). The HumanEval-Verus stripping step on invented
Verus text (proofs removed, the specification and the code kept, a loop's
decreases kept, fn main dropped), the residue check that is independent of
the stripper, the vericoding Dafny transform, and, when the set is installed,
the check that no stripped HumanEval-Verus task keeps a proof body."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import benchstrip as B  # noqa: E402

SAMPLE = '''/* header: assert(x) here is a comment, not code */
use vstd::prelude::*;

verus! {

mod m {
    use vstd::prelude::*;

    pub proof fn named_lemma(n: nat)
        ensures n + 0 == n,
    {
        assert(n + 0 == n);
    }
}

use m::named_lemma;

spec fn total(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { s[0] + total(s.drop_first()) }
}

// A helper lemma only a proof block calls.
proof fn helper_used(s: Seq<int>)
    ensures s.len() >= 0,
{
    assert(s.len() >= 0);
}

/// Documented, with an attribute.
#[verifier::spinoff_prover]
pub proof fn helper_unused(n: nat)
    ensures n + 0 == n,
{
}

broadcast group grp {
    helper_unused,
}

fn sum_up(v: &Vec<u8>) -> (r: u64)
    requires v.len() < 100,
    ensures r >= 0 && (v.len() == 0 ==> { r == 0 }),
{
    let ghost g = v@;
    let mut i: usize = 0;
    let mut acc: u64 = 0;
    // why the bound holds
    assert(v.len() < 100);
    while i < v.len()
        invariant
            i <= v.len(),
            acc <= 255 * i,
            v.len() > 0 ==> {
                &&& i <= 100
            },
        decreases v.len() - i,
    {
        proof {
            helper_used(seq![1int]);
        }
        acc = acc + v[i] as u64;
        i = i + 1;
    }
    for k in 0..3 invariant k <= 3 {
        acc = acc;
    }
    assert forall|k: int| 0 <= k < 3 implies k < 4 by {
        assert(k < 4);
    }
    assert(acc >= 0) by (nonlinear_arith);
    calc! { (==) 1int; { } 1int; }
    reveal(total);
    broadcast use grp;
    assert!(i == v.len());  // runtime check: kept
    acc
}

} // verus!
fn main() {
    assert_eq!(1, 1);
}
'''


class Strip(unittest.TestCase):
    def setUp(self):
        self.out = B.strip_proofs(SAMPLE)

    def test_proofs_are_removed(self):
        for gone in ("assert(", "assert forall", "invariant", "proof {", "helper_unused",
                     "helper_used", "broadcast group", "broadcast use", "let ghost", "reveal(",
                     "calc!", "fn main", "assert_eq!", "nonlinear_arith", "why the bound holds",
                     "spinoff_prover", "Documented"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, self.out.split("*/", 1)[1])

    def test_specification_code_and_measure_are_kept(self):
        for kept in ("/* header: assert(x) here is a comment, not code */",
                     "spec fn total(s: Seq<int>) -> int", "if s.len() == 0 { 0 } else",
                     "requires v.len() < 100,", "ensures r >= 0 && (v.len() == 0 ==> { r == 0 }),",
                     "while i < v.len()", "decreases v.len() - i,", "acc = acc + v[i] as u64;",
                     "for k in 0..3", "assert!(i == v.len());  // runtime check: kept",
                     "use m::named_lemma;", "} // verus!"):
            with self.subTest(kept=kept):
                self.assertIn(kept, self.out)

    def test_a_proof_fn_a_kept_line_names_keeps_its_signature_only(self):
        self.assertIn("pub proof fn named_lemma(n: nat)", self.out)
        self.assertIn("ensures n + 0 == n,", self.out)
        self.assertNotIn("assert(n + 0 == n)", self.out)

    def test_the_residue_check_is_empty_on_the_task_and_not_on_the_answer(self):
        self.assertEqual(B.proof_residue(self.out), [])
        found = {what for _, what in B.proof_residue(SAMPLE)}
        for what in ("assert", "proof block", "let ghost", "reveal", "invariant", "calc!",
                     "broadcast use in a body", "proof fn helper_used keeps a body"):
            with self.subTest(what=what):
                self.assertIn(what, found)

    def test_idempotent(self):
        self.assertEqual(B.strip_proofs(self.out), self.out)

    def test_the_report_counts_what_went(self):
        rep = B.strip_report(SAMPLE)
        self.assertEqual(rep["proof-fn"], 2)
        self.assertEqual(rep["proof-body"], 1)
        self.assertEqual(rep["main"], 1)
        self.assertGreaterEqual(rep["assert"], 3)
        self.assertEqual(rep["loop-clauses"], 2)

    def test_drop_main_changes_nothing_else(self):
        out = B.drop_main(SAMPLE)
        self.assertNotIn("fn main", out)
        self.assertEqual(out, SAMPLE.split("fn main")[0])
        self.assertEqual(B.drop_main(out), out)

    def test_a_file_the_lexer_cannot_balance_is_refused(self):
        with self.assertRaises(B.StripError):
            B.strip_proofs("verus! { fn f() { ( }\n")
        with self.assertRaises(B.StripError):
            B.strip_proofs("fn main() {}\n")          # no verus! block

    def test_strings_chars_and_lifetimes_do_not_confuse_the_lexer(self):
        src = ('verus! {\nfn f<\'a>(x: &\'a str) -> (r: char)\n    ensures true,\n{\n'
               '    let s = "a } { \\" proof { assert(false); }";\n    let c = \'}\';\n'
               '    assert(true);\n    c\n}\n}\n')
        out = B.strip_proofs(src)
        self.assertIn('proof { assert(false); }"', out)
        self.assertIn("let c = '}';", out)
        self.assertNotIn("    assert(true);", out)


class DafnyAxiomAssume(unittest.TestCase):
    def test_an_axiom_assume_becomes_a_counted_hole(self):
        src = "method M() returns (r: int)\n  ensures r > 0\n{\n  assume {:axiom} false;\n}\n"
        self.assertIn("  assume false;\n", B.dafny_axiom_assume_to_hole(src))
        self.assertNotIn("{:axiom}", B.dafny_axiom_assume_to_hole(src))

    def test_apply_respects_the_suffix(self):
        data = b"assume {:axiom} false;"
        self.assertEqual(B.apply("dafny-axiom-assume-to-hole", "tasks/x.rs", data), (data, False))
        self.assertEqual(B.apply("dafny-axiom-assume-to-hole", "tasks/x.dfy", data),
                         (b"assume false;", True))


class InstalledHumanEvalVerus(unittest.TestCase):
    """The installed set (a fetch set: absent in a fresh clone and in CI)."""

    def setUp(self):
        self.d = ROOT / "bench" / "public" / "humaneval-verus"
        if not (self.d / "tasks").is_dir() or not any((self.d / "tasks").glob("human_eval_*.rs")):
            self.skipTest("humaneval-verus is not installed (scripts/get_bench.sh humaneval-verus)")

    def test_no_stripped_task_keeps_a_proof_body(self):
        tasks = sorted((self.d / "tasks").glob("human_eval_*.rs"))
        self.assertGreater(len(tasks), 100)
        for t in tasks:
            with self.subTest(task=t.name):
                text = t.read_text(encoding="utf-8")
                self.assertEqual(B.proof_residue(text), [])
                self.assertEqual(B.strip_proofs(text), text)

    def test_each_task_is_its_answer_stripped(self):
        for t in sorted((self.d / "tasks").glob("human_eval_*.rs")):
            a = self.d / "answers" / t.name
            with self.subTest(task=t.name):
                self.assertTrue(a.is_file())
                self.assertEqual(B.strip_proofs(a.read_text(encoding="utf-8")),
                                 t.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
