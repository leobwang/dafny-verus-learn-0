"""Tool-free tests for the lab gate's code check on a Lab 2 card (the user's decision D27,
2026-10-14; scripts/dvl/labcode.py, `scripts/vcheck --gate --lab-task`):

  * on a public card (bench/local/q/lab2pub/) a delivery may add its specification, one
    witness call, definitions, lemmas and proof annotations (invariants, assertions, proof
    blocks, lemma calls, ghost variables); one that changes executable code is a
    `lab-code-changed` finding, in Dafny and in Verus;
  * on a local card (bench/local/q/lab2/) the same delivery's proof annotations are a finding
    too, with a message that says so;
  * a task form that is no Lab 2 card gets no code check; `lab_gate(..., code=False)` (the
    CLI's `--lab-code own`) waives it;
  * S1's mutant source (labcode.mutant_source) is the delivery's annotated body on a public
    card and the shipped body on a local one;
  * the shipped Lab 2 forms pass the check against themselves.

The fixtures are invented programs written into throwaway trees at the cards' course paths;
nothing here runs Dafny or Verus.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_lab_code_static.py'
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
common = core.common
from dvl import labcode as LC  # noqa: E402

# --- invented cards ----------------------------------------------------------------------------

V_FORM = """// An invented Lab 2 card.
use vstd::prelude::*;

verus! {

pub open spec fn larger(a: u32, b: u32) -> u32 {
    if a > b { a } else { b }
}

fn pick(a: u32, b: u32, flip: bool) -> (r: u32)
{
    let mut r: u32 = a;
    let mut t: u8 = 0;
    while t < 3
        decreases 3 - t,
    {
        if flip && b > r {
            r = b;
        }
        t = t + 1;
    }
    r
}

/// A non-vacuity witness for `pick`: one call whose `requires` hold.
fn pick_witness() {
}

} // verus!
"""

V_ANNOTATED = V_FORM.replace("""fn pick(a: u32, b: u32, flip: bool) -> (r: u32)
{""", """pub open spec fn floor_of(a: u32) -> u32 {
    a
}

proof fn lemma_step(t: int)
    ensures t < t + 1,
{
}

fn pick(a: u32, b: u32, flip: bool) -> (r: u32)
    requires
        a < 4000,
    ensures
        r >= floor_of(a),
{""").replace("""    while t < 3
        decreases 3 - t,
    {""", """    while t < 3
        invariant
            t <= 3,
            r >= a,
        decreases 3 - t,
    {
        // one proof step
        proof {
            lemma_step(t as int);
        }
        assert(r >= a);
        let ghost before = t;""").replace("""fn pick_witness() {
}""", """fn pick_witness() {
    let q = pick(7, 9, true);
}""")

D_FORM = """// An invented Lab 2 card.
function Step(x: int): int
{
  if x < 0 then 0 else x
}

predicate Tall(x: int)
{
  x > 3
}

method CountUp(s: seq<int>) returns (n: int)
{
  n := 0;
  var i := 0;
  while i < |s|
  {
    if Step(s[i]) > 3 {
      n := n + 1;
    }
    i := i + 1;
  }
}

/** A non-vacuity witness for `CountUp`: one call whose `requires` hold. */
method CountUpWitness()
{
}
"""

D_ANNOTATED = D_FORM.replace("""method CountUp(s: seq<int>) returns (n: int)
{""", """ghost function Big(s: seq<int>): int
{
  |s|
}

lemma Small(i: int)
  ensures i <= i + 1
{
}

method CountUp(s: seq<int>) returns (n: int)
  requires |s| < 1000
  ensures 0 <= n <= Big(s)
{""").replace("""  while i < |s|
  {""", """  ghost var seen := 0;
  while i < |s|
    invariant 0 <= i <= |s|
    invariant 0 <= n <= i
    decreases |s| - i
  {
    Small(i);
    assert n <= i;
    seen := seen + 1;""").replace("""method CountUpWitness()
{
}""", """method CountUpWitness()
{
  var r := CountUp([1, 5]);
}""")


def _code_edit(lang, text):
    """The annotated delivery with one executable change."""
    return text.replace("r = b;", "r = a;") if lang == "verus" else \
        text.replace("n := n + 1;", "n := n + 2;")


class CardTree(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-labcode-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def card(self, stratum, lang, form):
        cid = "xp1-he000" if stratum == "lab2pub" else ("x01-count" if lang == "dafny"
                                                         else "y01-count")
        ext = ".rs" if lang == "verus" else ".dfy"
        p = self.tmp / "bench" / "local" / "q" / stratum / cid / "tasks" / f"{cid}{ext}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(form, encoding="utf-8")
        return p

    def delivery(self, lang, text):
        p = self.tmp / ("delivery.rs" if lang == "verus" else "delivery.dfy")
        p.write_text(text, encoding="utf-8")
        return p

    def kinds(self, task, delivery):
        return [f.kind for f in LC.code_findings(task, delivery)]


CASES = (("verus", V_FORM, V_ANNOTATED), ("dafny", D_FORM, D_ANNOTATED))


class PublicCard(CardTree):
    def test_an_annotation_only_delivery_passes(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                self.assertEqual(LC.card_rule(t), "annotations")
                self.assertEqual(self.kinds(t, self.delivery(lang, ann)), [])
                self.assertEqual(self.kinds(t, t), [])

    def test_a_delivery_that_edits_executable_code_fails(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                got = LC.code_findings(t, self.delivery(lang, _code_edit(lang, ann)))
                self.assertEqual([f.kind for f in got], ["lab-code-changed"])
                name = "pick" if lang == "verus" else "CountUp"
                self.assertIn(name, got[0].message)
                self.assertNotIn("r = a", got[0].message)     # names the scope, never code
                self.assertNotIn("n + 2", got[0].message)

    def test_added_or_removed_executable_declarations_fail(self):
        extra = {"verus": ("fn pick_witness() {", "fn helper() -> u32 {\n    1\n}\n\n"
                                                  "fn pick_witness() {"),
                 "dafny": ("method CountUpWitness()", "method Helper() returns (r: int)\n{\n"
                                                      "  r := 1;\n}\n\nmethod CountUpWitness()")}
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                a, b = extra[lang]
                self.assertEqual(self.kinds(t, self.delivery(lang, ann.replace(a, b, 1))),
                                 ["lab-code-changed"])
        # a function the code calls is code: changing it is a change (Dafny)
        t = self.card("lab2pub", "dafny", D_FORM)
        changed = D_ANNOTATED.replace("if x < 0 then 0 else x", "if x < 1 then 0 else x")
        self.assertEqual(self.kinds(t, self.delivery("dafny", changed)), ["lab-code-changed"])
        # a definition the code does not call is not (Dafny's compiled predicate, unused)
        unused = D_ANNOTATED.replace("  x > 3\n", "  x > 4\n")
        self.assertEqual(self.kinds(t, self.delivery("dafny", unused)), [])

    def test_a_loop_measure_and_a_witness_body_are_the_deliverys(self):
        t = self.card("lab2pub", "verus", V_FORM)
        d = V_ANNOTATED.replace("decreases 3 - t,", "decreases 3 - t + 0,")
        self.assertEqual(self.kinds(t, self.delivery("verus", d)), [])
        t = self.card("lab2pub", "dafny", D_FORM)
        d = D_ANNOTATED.replace("var r := CountUp([1, 5]);", "var r := CountUp([]);\n  "
                                                             "var q := CountUp([9]);")
        self.assertEqual(self.kinds(t, self.delivery("dafny", d)), [])

    def test_an_unreadable_pair_is_unchecked_never_a_pass(self):
        t = self.card("lab2pub", "verus", V_FORM)
        self.assertEqual(self.kinds(t, self.delivery("dafny", D_ANNOTATED)),
                         ["lab-code-unchecked"])
        self.assertEqual(self.kinds(t, self.delivery("verus", "fn x() {")),
                         ["lab-code-unchecked"])


D_FORM2 = """// A second invented Lab 2 card: a target beside another method.
method Bump(a: array<int>)
  modifies a
{
  if a.Length > 0 {
    a[0] := 1;
  }
}

method Total(a: array<int>) returns (r: int)
{
  r := 0;
  var i := 0;
  while i < a.Length
  {
    r := r + a[i];
    i := i + 1;
  }
}

/** A non-vacuity witness for `Total`: one call whose `requires` hold. */
method TotalWitness()
{
}
"""

D_LEMMA = """lemma Small(i: int)
  ensures i <= i + 1
{
}

method Total("""


def _d2(*edits):
    text = D_FORM2.replace("method Total(", D_LEMMA, 1)
    for a, b in edits:
        assert a in text, a
        text = text.replace(a, b, 1)
    return text


class PublicCardGhostCode(CardTree):
    """DV6 review: a ghost statement that runs code, or shadows a code name, is code."""

    def check(self, delivery_text):
        t = self.card("lab2pub", "dafny", D_FORM2)
        return self.kinds(t, self.delivery("dafny", delivery_text))

    def test_a_ghost_var_that_calls_a_method_is_code(self):
        d = _d2(("  r := 0;\n  var i := 0;", "  r := 0;\n  ghost var g := Bump(a);\n  var i := 0;"))
        self.assertEqual(self.check(d), ["lab-code-changed"])

    def test_a_ghost_var_that_allocates_is_code(self):
        d = _d2(("  r := 0;\n  var i := 0;",
                 "  r := 0;\n  ghost var g := new int[3];\n  var i := 0;"))
        self.assertEqual(self.check(d), ["lab-code-changed"])

    def test_a_ghost_var_that_shadows_an_out_parameter_is_code(self):
        d = _d2(("    i := i + 1;\n  }", "    i := i + 1;\n    ghost var r := 0;\n  }\n  r := 42;"))
        self.assertEqual(self.check(d), ["lab-code-changed"])
        # a ghost var that shadows a parameter or a local, alone, is code too
        d = _d2(("  r := 0;\n  var i := 0;", "  r := 0;\n  ghost var a := 0;\n  var i := 0;"))
        self.assertEqual(self.check(d), ["lab-code-changed"])

    def test_an_honest_ghost_var_and_its_update_pass(self):
        d = _d2(("  r := 0;\n  var i := 0;", "  r := 0;\n  ghost var seen := 0;\n  var i := 0;"),
                ("    i := i + 1;\n  }", "    i := i + 1;\n    seen := seen + 1;\n  }"))
        self.assertEqual(self.check(d), [])

    def test_a_label_and_a_labelled_assertion_pass(self):
        d = _d2(("  r := 0;\n  var i := 0;", "  label Start:\n  r := 0;\n  var i := 0;"),
                ("    i := i + 1;\n  }", "    i := i + 1;\n  }\n  label L:\n  assert r == r;"))
        self.assertEqual(self.check(d), [])

    def test_a_qualified_lemma_call_passes(self):
        d = _d2(("    i := i + 1;\n  }", "    _default.Small(i);\n    i := i + 1;\n  }"))
        self.assertEqual(self.check(d), [])
        # a qualified call of a non-ghost method stays code
        d = _d2(("    i := i + 1;\n  }", "    _default.Bump(a);\n    i := i + 1;\n  }"))
        self.assertEqual(self.check(d), ["lab-code-changed"])


class CardRulePaths(CardTree):
    """DV6 review: the rule does not hang on the path's spelling."""

    def test_a_relative_path_from_the_card_directory(self):
        import os
        t = self.card("lab2pub", "dafny", D_FORM)
        cwd = os.getcwd()
        os.chdir(t.parent.parent)
        self.addCleanup(os.chdir, cwd)
        self.assertEqual(LC.card_rule("tasks/" + t.name), "annotations")
        self.assertEqual(LC.card_rule("./tasks/" + t.name), "annotations")
        got = LC.code_findings(Path("tasks") / t.name,
                               self.delivery("dafny", _code_edit("dafny", D_ANNOTATED)))
        self.assertEqual([f.kind for f in got], ["lab-code-changed"])

    def test_a_copy_of_a_shipped_form_takes_its_rule(self):
        forms = sorted((C.ROOT / "bench/local/q/lab2pub").glob("*/tasks/*.dfy"))
        local = sorted((C.ROOT / "bench/local/q/lab2").glob("*/tasks/*.dfy"))
        if not forms or not local:
            self.skipTest("no shipped Lab 2 form")
        for src, rule in ((forms[0], "annotations"), (local[0], "spec")):
            cp = self.tmp / "scratch" / src.name
            cp.parent.mkdir(parents=True, exist_ok=True)
            cp.write_bytes(src.read_bytes())
            self.assertEqual(LC.card_rule(cp), rule)

    def test_a_stray_path_under_a_stratum_is_unchecked(self):
        p = self.tmp / "bench" / "local" / "q" / "lab2pub" / "loose.dfy"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(D_FORM, encoding="utf-8")
        self.assertEqual(self.kinds(p, self.delivery("dafny", D_ANNOTATED)), ["lab-code-unchecked"])
        # a file outside every stratum, of no form's bytes: no code check
        q = self.tmp / "elsewhere.dfy"
        q.write_text(D_FORM, encoding="utf-8")
        self.assertEqual(self.kinds(q, self.delivery("dafny", D_ANNOTATED)), [])


class CodeMutant(CardTree):
    """labcode.code_mutant: S1's filter for mutants that change only annotations (DV6)."""

    def test_annotation_only_and_code_mutants(self):
        for lang, form, ann, ann_edit, code_edit in (
                ("verus", V_FORM, V_ANNOTATED, ("t <= 3,", "t <= 4,"), ("r = b;", "r = a;")),
                ("dafny", D_FORM, D_ANNOTATED, ("invariant 0 <= n <= i", "invariant 0 <= n <= i + 1"),
                 ("n := n + 1;", "n := n + 2;"))):
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                body = LC.mutant_source(t, ann)["body"]
                for (a, b), want in ((ann_edit, False), (code_edit, True)):
                    self.assertIn(a, body)
                    self.assertEqual(LC.code_mutant(t, ann, body.replace(a, b, 1)), want)
                self.assertFalse(LC.code_mutant(t, ann, body))

    def test_a_local_card_mutates_the_shipped_body(self):
        t = self.card("lab2", "dafny", D_FORM)
        body = LC.mutant_source(t, D_FORM)["body"]
        self.assertTrue(LC.code_mutant(t, D_FORM, body.replace("n := n + 1;", "n := n + 2;", 1)))


class LocalCard(CardTree):
    def test_the_specification_and_the_witness_pass(self):
        verus = V_FORM.replace("""fn pick(a: u32, b: u32, flip: bool) -> (r: u32)
{""", """fn pick(a: u32, b: u32, flip: bool) -> (r: u32)
    ensures
        r >= a,
{""").replace("fn pick_witness() {\n}", "fn pick_witness() {\n    let q = pick(1, 2, false);\n}")
        self.assertNotEqual(verus, V_FORM)
        spec_only = {"verus": verus,
                     "dafny": D_FORM.replace("method CountUp(s: seq<int>) returns (n: int)\n{",
                                             "method CountUp(s: seq<int>) returns (n: int)\n"
                                             "  ensures n >= 0\n{")}
        for lang, form, _ in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2", lang, form)
                self.assertEqual(LC.card_rule(t), "spec")
                self.assertEqual(self.kinds(t, self.delivery(lang, spec_only[lang])), [])

    def test_proof_annotations_are_a_public_cards_only(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2", lang, form)
                got = LC.code_findings(t, self.delivery(lang, ann))
                self.assertEqual([f.kind for f in got], ["lab-code-changed"])
                self.assertIn("proof annotations", got[0].message)
                self.assertIn("D27", got[0].message)
                got = LC.code_findings(t, self.delivery(lang, _code_edit(lang, ann)))
                self.assertIn("executable code", got[0].message)


class Rules(unittest.TestCase):
    def test_the_rule_comes_from_the_course_path(self):
        for path, rule in (
                ("bench/local/q/lab2pub/vp1-he100/tasks/vp1-he100.rs", "annotations"),
                ("/work/lab-task/bench/local/q/lab2pub/dp1-he048/tasks/dp1-he048.dfy",
                 "annotations"),
                ("lab-task/bench/local/q/lab2/d01-third-limb/tasks/d01-third-limb.dfy", "spec"),
                ("bench/local/q/lab1/dh4-tonat-mono/tasks/dh4-tonat-mono.dfy", None),
                ("bench/local/q/lab2/oracle/tasks/tmpx.dfy", None),
                ("bench/local/q/crate/c01/tasks/c01.rs", None),
                ("tests/wrappers/fixtures/dafny/lab/task.dfy", None)):
            self.assertEqual(LC.card_rule(path), rule, path)

    def test_no_card_no_check(self):
        lab = C.ROOT / "tests" / "wrappers" / "fixtures" / "dafny" / "lab"
        self.assertEqual(LC.code_findings(lab / "task.dfy", lab / "levered.dfy"), [])


class LabGate(CardTree):
    def _res(self, lang, delivery):
        return common.Result(lang, str(delivery), 0, "verified", "verify", 2)

    def test_the_gate_fails_a_code_change_and_the_waiver_passes_it(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                d = self.delivery(lang, _code_edit(lang, ann))
                res = core.lab_gate(self._res(lang, d), t, d, audit=lambda: [])
                self.assertEqual((res.verdict, [f.kind for f in res.findings]),
                                 ("failed", ["lab-code-changed"]))
                res = core.lab_gate(self._res(lang, d), t, d, audit=lambda: [], code=False)
                self.assertEqual((res.verdict, res.findings), ("verified", []))
                d = self.delivery(lang, ann)
                res = core.lab_gate(self._res(lang, d), t, d, audit=lambda: [])
                self.assertEqual((res.verdict, res.findings), ("verified", []))

    def test_the_audit_does_not_run_after_a_code_change(self):
        t = self.card("lab2pub", "dafny", D_FORM)
        d = self.delivery("dafny", _code_edit("dafny", D_ANNOTATED))
        ran = []
        core.lab_gate(self._res("dafny", d), t, d, audit=lambda: ran.append(1) or [])
        self.assertEqual(ran, [])

    def test_lab_code_needs_lab_task(self):
        rc, out, err = C.tool("vcheck", "--gate", "--lab-code", "own",
                              C.ROOT / "tests/wrappers/fixtures/dafny/lab/kept.dfy")
        self.assertEqual(rc, 2, out + err)
        self.assertIn("--lab-code goes with --gate --lab-task", err)


class MutantSource(CardTree):
    """S1's mutant kill on a public card mutates the delivery's annotated body (D27)."""

    def test_a_public_card_mutates_the_deliverys_annotated_body(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2pub", lang, form)
                src = LC.mutant_source(t, ann)
                self.assertEqual(src["rule"], "annotations")
                self.assertIn("invariant", src["body"])
                self.assertIn("r >= a" if lang == "verus" else "n <= i", src["body"])
                self.assertIn("lemma_step" if lang == "verus" else "Small(i)", src["header"] +
                              src["body"])
                self.assertTrue(src["footer"].lstrip().startswith(("///", "/**")))

    def test_a_local_card_mutates_the_shipped_body(self):
        for lang, form, ann in CASES:
            with self.subTest(lang=lang):
                t = self.card("lab2", lang, form)
                src = LC.mutant_source(t, ann)
                self.assertEqual(src["rule"], "spec")
                self.assertNotIn("invariant", src["body"])
                shipped = LC.mutant_source(t, form)["body"]
                self.assertEqual(src["body"], shipped)

    def test_no_card_no_mutant_source(self):
        with self.assertRaises(LC.CodeError):
            LC.mutant_source("tests/wrappers/fixtures/dafny/lab/task.dfy", D_FORM)


class ShippedCards(unittest.TestCase):
    def test_every_shipped_lab2_form_passes_against_itself(self):
        forms = sorted((C.ROOT / "bench" / "local" / "q").glob("lab2*/*/tasks/*"))
        self.assertEqual(len(forms), 30)
        for p in forms:
            rel = p.relative_to(C.ROOT)
            with self.subTest(form=rel.as_posix()):
                self.assertIsNotNone(LC.card_rule(rel))
                self.assertEqual(LC.code_findings(rel, rel, ttext=p.read_text(encoding="utf-8"),
                                                  dtext=p.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
