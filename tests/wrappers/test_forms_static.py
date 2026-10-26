"""Tool-free tests for the DV3b tools items: per-item construct forms and the
`// cfree:` lines (QPLAN §6 Q43: scripts/dvl/forms.py and firsttry), the solver
options and the sweep of vcheck --brittleness (§6 Q29), and open statements in
the freeze pin (§6 Q44: specfreeze's open_specs and the reference lint).

Nothing here runs Dafny or Verus: every case is pure text, a refusal before a
run, or a sweep made of invented Result rows. Every program below is an
invented toy (neutral test material for the gates): none is course content, an
exercise, an answer or text from the reference tree.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_forms_static.py'
"""

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
import unittest.mock
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
firsttry = C.load_script("firsttry")
from dvl import common  # noqa: E402
from dvl import forms as F  # noqa: E402

REFERENCE = C.ROOT / "tests" / "wrappers" / "fixtures" / "tools" / "reference"
CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
LIB_RS = "verus/q/q04_proof_craft/src/lib.rs"
EXIT_RS = "verus/q/q04_proof_craft/src/exit.rs"


def blocks_of(text):
    """{item id: (lo, hi)} and the H/X/T block list of an invented file."""
    rel = "x.rs" if "verus!" in text else "x.dfy"
    items, errs = firsttry.ci.parse_items(rel, text)
    assert not errs, errs
    got = {it["id"]: (it["line_start"], it["line_end"]) for it in items}
    return got, [v for it, v in zip(items, got.values()) if it["kind"] in "HXT"]


def check(text, lang, iid, rules, given=None):
    got, blocks = blocks_of(text)
    return F.check_static(F.parse(text, lang), lang, rules, got[iid], blocks, given)


# =====================================================================================
# The vocabulary and the marker lines
# =====================================================================================

class FormVocabulary(unittest.TestCase):
    def test_parse_rules(self):
        self.assertEqual(F.parse_rules("bv-exec, nl-steps:2, stable"),
                         (["bv-exec", "nl-steps:2", "stable"], []))
        rules, probs = F.parse_rules("trigger, nl-steps:0, nl-steps, foo,  , trigger")
        self.assertEqual(rules, ["trigger"])
        self.assertEqual(len(probs), 4)
        self.assertTrue(all("not a form rule" in p or "empty" in p for p in probs))
        self.assertEqual(F.rule_name("nl-steps:12"), "nl-steps")
        self.assertIsNone(F.rule_name("nl-steps:x"))
        self.assertEqual(F.lang_problems(["bv-exec", "no-nl", "nl-steps:2", "trigger", "stable"],
                                         "d"), ["bv-exec", "no-nl", "nl-steps:2"])
        self.assertEqual(F.lang_problems(["trigger", "stable", "bv-exec"], "v"), [])

    def test_form_lines_union(self):
        raw = ["// item: Q04.H5v S3", "// uses: calc", "// form: bv-exec", "fn f() {}",
               "    //   form:  stable, bv-exec", "// formless: x", "# form: trigger"]
        self.assertEqual([(ln, r) for ln, r, _ in F.form_lines(raw, 1, len(raw))],
                         [(3, ["bv-exec"]), (5, ["stable", "bv-exec"]), (7, ["trigger"])])
        self.assertEqual(F.block_rules(raw, 1, 5), ["bv-exec", "stable"])
        self.assertEqual(F.block_rules(raw, 4, 4), [])

    def test_cfree_bodies(self):
        raw = ["// cfree: { a }", "// cfree: { b", "//   cfree:   c }", "x",
               "// cfree: { d }", "// cfree: { e } { f }", "// cfree: { g } tail",
               "// cfree: { h"]
        bodies, probs = F.cfree_bodies(raw, 1, 7)
        self.assertEqual(bodies, ["{ a }", "{ b\n  c }", "{ d }", "{ e }", "{ f }", "{ g }"])
        self.assertEqual(probs, ["a `cfree:` line holds text outside its `{ … }` body"])
        self.assertEqual(F.cfree_bodies(raw, 8, 8), ([], ["a `cfree:` body leaves a brace "
                                                          "open"]))


# =====================================================================================
# The static checks (invented Verus and Dafny toys)
# =====================================================================================

VERUS = """use vstd::prelude::*;

verus! {

pub fn triple(a: u64) -> (r: u64)
    requires
        a < 100,
{
    a * 3
}

pub fn same(a: u64) -> (r: u64)
{
    a
}

pub proof fn square_nonneg(x: nat)
    ensures
        x * x >= 0,
{
    assert(x * x >= 0) by (nonlinear_arith);
}

// item: Q04.H5v S3
// form: bv-exec
pub fn pack(hi: u8, lo: u8) -> (r: u16)
    ensures
        r as nat == hi as nat * 256 + lo as nat,
{
    proof {
        assert(hi as u16 * 256 <= 65280) by (nonlinear_arith);
    }
    let h = &hi;
    let w = *h;
    let ghost g = w as nat * 2;
    assert(w as nat * 2 >= 0);
    let r = ((hi as u16) << 8u16) | (lo as u16);
    r
}

// item: Q04.H6v S3
// form: bv-exec
pub fn pack_div(p: u16) -> (r: u8)
{
    (p / 256) as u8
}

// item: Q04.H7v S3
// form: bv-exec
pub fn pack_method(p: u16) -> (r: u16)
{
    p.wrapping_mul(2)
}

// item: Q04.H8v S3
// form: bv-exec
pub fn pack_helper(a: u64) -> (r: u64)
    requires
        a < 100,
{
    same(a) + triple(a)
}

// item: Q04.H9v S3
// form: bv-exec
pub proof fn no_exec(x: nat)
{
}

// item: Q04.H10v S3
// form: no-nl, nl-steps:2
pub proof fn zeros(a: nat, b: nat, z: nat)
    requires
        z == 0,
    ensures
        a * z + z * b == 0,
{
    // assert(a * z + z * b == 0) by (nonlinear_arith) requires z == 0;
    assert(a * z == 0) by (nonlinear_arith) requires z == 0;
    assert(z * b == 0) by (nonlinear_arith)
        requires
            z == 0,
    {
    }
    assert(0 <= a) by (nonlinear_arith);
}

// item: Q04.H11v S3
// form: no-nl
pub proof fn via_helper(x: nat)
    ensures
        x * x >= 0,
{
    square_nonneg(x);
}

// item: Q04.H12v S3
// form: trigger, stable
pub proof fn all_small(s: Seq<u8>)
    ensures
        forall|i: int| 0 <= i < s.len() ==> #[trigger] s[i] <= 255,
{
    // forall|i: int| #![trigger s[i]] true
}

// item: Q04.H13v S3
// form: trigger, stable
#[verifier::rlimit(4)]
pub proof fn all_small_again(s: Seq<u8>)
    ensures
        true,
{
    assert forall|i: int| 0 <= i < s.len() implies #[trigger] s[i] <= 255 by {}
}

} // verus!
"""


class FormChecksVerus(unittest.TestCase):
    def test_bv_exec(self):
        ok = check(VERUS, "v", "Q04.H5v", ["bv-exec"])["bv-exec"]
        self.assertEqual(ok, (True, ""))            # proof, assert, ghost, deref, spec clause
        self.assertEqual(check(VERUS, "v", "Q04.H6v", ["bv-exec"])["bv-exec"][0], False)
        self.assertIn("`/` in exec code at line",
                      check(VERUS, "v", "Q04.H6v", ["bv-exec"])["bv-exec"][1])
        self.assertIn("a `wrapping_mul` call",
                      check(VERUS, "v", "Q04.H7v", ["bv-exec"])["bv-exec"][1])
        # a helper outside every item block is the item's exec code too
        ok, why = check(VERUS, "v", "Q04.H8v", ["bv-exec"])["bv-exec"]
        self.assertFalse(ok)
        line = VERUS.split("\n").index("    a * 3") + 1
        self.assertEqual(why, f"`*` in exec code at line {line}")
        self.assertEqual(check(VERUS, "v", "Q04.H9v", ["bv-exec"])["bv-exec"],
                         (False, "the block holds no exec fn"))

    def test_no_nl_and_nl_steps(self):
        got = check(VERUS, "v", "Q04.H10v", ["no-nl", "nl-steps:2", "nl-steps:3"])
        self.assertFalse(got["no-nl"][0])
        self.assertEqual(got["nl-steps:2"], (True, ""))     # the unscoped third step is not one
        self.assertFalse(got["nl-steps:3"][0])
        self.assertIn("2 scoped `nonlinear_arith` step(s)", got["nl-steps:3"][1])
        ok, why = check(VERUS, "v", "Q04.H11v", ["no-nl"])["no-nl"]
        self.assertFalse(ok)
        self.assertIn("in a helper the block calls", why)
        self.assertEqual(check(VERUS, "v", "Q04.H12v", ["no-nl"])["no-nl"], (True, ""))
        attr = VERUS.replace("pub proof fn square_nonneg", "#[verifier::nonlinear]\n"
                             "pub proof fn square_nonneg").replace(
            "    assert(x * x >= 0) by (nonlinear_arith);\n", "")
        ok, why = check(attr, "v", "Q04.H11v", ["no-nl"])["no-nl"]
        self.assertFalse(ok)
        self.assertIn("a nonlinear attribute", why)

    def test_trigger_and_stable(self):
        got = check(VERUS, "v", "Q04.H12v", ["trigger", "stable"])
        # the trigger in the frozen statement (the ensures) is not the answer's
        self.assertEqual(got["trigger"][0], False)
        self.assertEqual(got["stable"], (True, ""))
        got = check(VERUS, "v", "Q04.H13v", ["trigger", "stable"])
        self.assertEqual(got["trigger"], (True, ""))
        self.assertFalse(got["stable"][0])
        self.assertIn("a resource attribute at line", got["stable"][1])
        body = VERUS.replace("    // forall|i: int| #![trigger s[i]] true\n",
                             "    assert(forall|i: int| #![trigger s[i]] 0 <= i < s.len() ==> "
                             "s[i] <= 255);\n")
        self.assertEqual(check(body, "v", "Q04.H12v", ["trigger"])["trigger"], (True, ""))
        self.assertEqual(check(VERUS, "v", "Q04.H5v", ["trigger"])["trigger"],
                         (False, "no explicit trigger (`#[trigger]` or `#![trigger …]`) in the "
                                 "block"))

    def test_given_declarations_are_not_the_answer(self):
        two = VERUS.replace("\n} // verus!", "\npub proof fn given_step(s: Seq<u8>)\n"
                            "    ensures\n        true,\n{\n    assert(forall|i: int| "
                            "#![trigger s[i]] 0 <= i < s.len() ==> s[i] <= 255);\n}\n"
                            "\n} // verus!")
        two = two.replace("    assert forall|i: int| 0 <= i < s.len() implies #[trigger] s[i] <= "
                          "255 by {}\n", "")
        # unknown shipped block: every fn of the block after the first counts
        self.assertEqual(check(two, "v", "Q04.H13v", ["trigger"])["trigger"], (True, ""))
        # a declaration the block shipped with is given code, not the answer
        self.assertFalse(check(two, "v", "Q04.H13v", ["trigger"], given={"given_step"})
                         ["trigger"][0])
        src = F.parse(two, "v")
        got, _ = blocks_of(two)
        self.assertEqual(F.block_decl_names(src, "v", got["Q04.H13v"]), {"given_step"})

    def test_wrong_language_and_unknown(self):
        got = check(VERUS, "v", "Q04.H5v", ["frob"])
        self.assertEqual(got["frob"], (False, "not a form rule"))


DAFNY = """module M {
  function Twice(n: nat): nat { n + n }

  // item: Q04.H1d S3
  // form: trigger, stable
  lemma AllTwice(s: seq<nat>)
    ensures forall i {:trigger s[i]} :: 0 <= i < |s| ==> Twice(s[i]) >= s[i]
  {
    // forall i {:trigger Twice(i)} | 0 <= i < |s| ensures true {}
  }

  // item: Q04.H2d S3
  // form: trigger, stable
  lemma {:resource_limit 100} AllTwice2(s: seq<nat>)
    ensures true
  {
    forall i {:trigger s[i]} | 0 <= i < |s|
      ensures Twice(s[i]) >= s[i]
    {
    }
  }

  // item: Q04.H3d S3
  // form: bv-exec
  lemma Plain(n: nat)
    ensures Twice(n) == 2 * n
  {
  }
}
"""


class FormChecksDafny(unittest.TestCase):
    def test_trigger_stable_and_language(self):
        got = check(DAFNY, "d", "Q04.H1d", ["trigger", "stable"])
        self.assertFalse(got["trigger"][0])          # the statement's trigger, a commented one
        self.assertEqual(got["stable"], (True, ""))
        got = check(DAFNY, "d", "Q04.H2d", ["trigger", "stable"])
        self.assertEqual(got["trigger"], (True, ""))
        line = DAFNY.split("\n").index("  lemma {:resource_limit 100} AllTwice2(s: seq<nat>)") + 1
        self.assertEqual(got["stable"], (False, f"a resource attribute at line {line}"))
        self.assertEqual(check(DAFNY, "d", "Q04.H3d", ["bv-exec"])["bv-exec"],
                         (False, "a Verus form on a Dafny block"))
        at = DAFNY.replace("lemma {:resource_limit 100} AllTwice2", "@ResourceLimit(\"1e3\")\n"
                           "  lemma AllTwice2")
        self.assertFalse(check(at, "d", "Q04.H2d", ["stable"])["stable"][0])


# Invented toys for the argument rules (DV5a kits): a compiled function the
# answer must not call, and a predicate whose body must be a formula.
NOCALL = """module T {
  function Weight(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0] + Weight(s[1..])
  }

  // item: Q04.H8d S1
  // form: no-call:Weight
  method Small(s: seq<nat>) returns (b: bool)
    ensures b <==> Weight(s) == 0
  {
    assert Weight([]) == 0;
    b := Weight(s) == 0;
  }
}
"""

# Verus (DV5c): a fn the answer must not reach, directly or through a helper
# of the same file outside every block.
NOCALL_V = """use vstd::prelude::*;
verus! {

pub fn pour(x: u64) -> u64 { x }

fn relay(x: u64) -> u64 { pour(x) }

// item: Q04.H8v S1
// form: no-call:pour
pub fn steady(x: u64) -> (r: u64)
    ensures r == x,
{
    let t = relay(x);
    t
}

} // verus!
"""

# Verus (DV5c fix round): an adder of the learner's own, reached from the block.
ADDER_V = """use vstd::prelude::*;
verus! {

pub struct Num { pub v: Vec<u64> }

impl Num {
    pub open spec fn to_nat(&self) -> nat { self.v@.len() }
}

pub open spec fn seq_to_nat(s: Seq<u64>) -> nat { s.len() }

pub fn join(a: &Num, b: &Num) -> (r: Num)
    ensures
        r.v@.len() >= 0,
        r.to_nat() == a.to_nat() + b.to_nat(),
{
    Num { v: Vec::new() }
}

// item: Q04.H8v S1
// form: no-adder
pub fn twice(a: &Num, b: &Num) -> (r: Num)
{
    let t = join(a, b);
    t
}

} // verus!
"""

FORMULA = """module A {
  ghost predicate P(x: int) { x + 1 > 0 }
}

module C {
  import opened A

  // item: Q04.H9d S8
  // form: formula:P
  lemma PExact(x: int)
    ensures P(x) <==> x > -1
  {
  }
}
"""


class FormArgumentRules(unittest.TestCase):
    def test_vocabulary(self):
        self.assertEqual(F.rule_name("no-call:Weight"), "no-call")
        self.assertEqual(F.rule_arg("formula:P"), "P")
        self.assertIsNone(F.rule_name("no-call:"))
        self.assertIsNone(F.rule_name("formula:1x"))
        rules, probs = F.parse_rules("no-call:Weight, formula:P")
        self.assertEqual((rules, probs), (["no-call:Weight", "formula:P"], []))
        self.assertEqual(F.lang_problems(["no-call:Weight"], "v"), [])
        self.assertEqual(F.lang_problems(["formula:P"], "v"), ["formula:P"])

    def test_no_call(self):
        got = check(NOCALL, "d", "Q04.H8d", ["no-call:Weight"])
        self.assertFalse(got["no-call:Weight"][0])
        self.assertIn("a compiled call of `Weight`", got["no-call:Weight"][1])
        ghost_only = NOCALL.replace("    b := Weight(s) == 0;\n", "    b := |s| == 0;\n")
        self.assertEqual(check(ghost_only, "d", "Q04.H8d", ["no-call:Weight"])["no-call:Weight"],
                         (True, ""))

    def test_no_call_verus(self):
        rule = "no-call:pour"
        self.assertFalse(check(NOCALL_V, "v", "Q04.H8v", [rule])[rule][0])
        ok, why = check(NOCALL_V, "v", "Q04.H8v", [rule])[rule]
        self.assertIn("a call of `pour`", why)
        self.assertIn("in a helper the block calls", why)
        direct = NOCALL_V.replace("    let t = relay(x);\n", "    let t = pour(x);\n")
        ok, why = check(direct, "v", "Q04.H8v", [rule])[rule]
        self.assertFalse(ok)
        self.assertNotIn("helper", why)
        method = NOCALL_V.replace("    let t = relay(x);\n", "    let t = x.pour();\n")
        self.assertFalse(check(method, "v", "Q04.H8v", [rule])[rule][0])
        clean = NOCALL_V.replace("    let t = relay(x);\n", "    let t = x;\n")
        self.assertEqual(check(clean, "v", "Q04.H8v", [rule])[rule], (True, ""))

    def test_formula(self):
        self.assertEqual(check(FORMULA, "d", "Q04.H9d", ["formula:P"])["formula:P"], (True, ""))
        for body, why in (("{ var y := x + 1; y > 0 }", "`var`"),
                          ("{ Q(x) }", "a call of `Q`"),
                          ("{ match x case _ => true }", "`match`")):
            text = FORMULA.replace("{ x + 1 > 0 }", body)
            ok, msg = check(text, "d", "Q04.H9d", ["formula:P"])["formula:P"]
            self.assertFalse(ok, body)
            self.assertIn(why, msg)
        ok, msg = check(FORMULA, "d", "Q04.H9d", ["formula:Q"])["formula:Q"]
        self.assertFalse(ok)
        self.assertIn("no declaration `Q`", msg)

    def test_no_call_in_a_bare_call_statement(self):
        """A bare call statement (a lemma or method call) assigns nothing: its
        arguments are no compiled use (DV5c fix round)."""
        lem = NOCALL.replace("  // item: Q04.H8d S1",
                             "  lemma Zero(n: nat) ensures n >= 0 {}\n\n  // item: Q04.H8d S1")
        bare = lem.replace("    b := Weight(s) == 0;\n", "    Zero(Weight(s));\n    b := |s| == 0;\n")
        self.assertEqual(check(bare, "d", "Q04.H8d", ["no-call:Weight"])["no-call:Weight"],
                         (True, ""))
        still = lem.replace("    b := Weight(s) == 0;\n",
                            "    Zero(Weight(s));\n    b := Weight(s) == 0;\n")
        self.assertFalse(check(still, "d", "Q04.H8d", ["no-call:Weight"])["no-call:Weight"][0])

    def test_no_adder(self):
        """A helper of the learner's own that states a whole-number sum (DV5c)."""
        text = ADDER_V
        rule = "no-adder"
        self.assertEqual(F.rule_name(rule), "no-adder")
        self.assertEqual(F.lang_problems([rule], "d"), [rule])
        ok, why = check(text, "v", "Q04.H8v", [rule])[rule]
        self.assertFalse(ok)
        self.assertIn("`join` (line", why)
        self.assertIn("states a whole-number sum", why)
        for old, new in (("r.to_nat() == a.to_nat() + b.to_nat()",
                          "a.to_nat() + b.to_nat() == r.to_nat()"),
                         ("r.to_nat() == a.to_nat() + b.to_nat()",
                          "seq_to_nat(r.v@) == a.to_nat() + b.to_nat() as int")):
            self.assertFalse(check(text.replace(old, new), "v", "Q04.H8v", [rule])[rule][0], new)
        # a product in the sum (a row added in place), or no helper reached, passes
        row = text.replace("r.to_nat() == a.to_nat() + b.to_nat()",
                           "r.to_nat() == a.to_nat() + 7 * b.to_nat()")
        self.assertEqual(check(row, "v", "Q04.H8v", [rule])[rule], (True, ""))
        gone = text.replace("    let t = join(a, b);\n", "    let t = Num { v: Vec::new() };\n")
        self.assertEqual(check(gone, "v", "Q04.H8v", [rule])[rule], (True, ""))

    def test_cfree_decl_lines(self):
        raw = ["// cfree-decl: fn h() {}", "// cfree-decl:", "// cfree: { 1 }", "// cfree: { 2 }",
               "// x", "// cfree: { 3 }"]
        got, probs = F.cfree_answers(raw, 1, len(raw))
        self.assertEqual(got, [("{ 1 }", "fn h() {}\n"), ("{ 2 }", "fn h() {}\n"), ("{ 3 }", "")])
        self.assertEqual(probs, [])
        self.assertEqual(F.cfree_bodies(raw, 1, len(raw))[0], ["{ 1 }", "{ 2 }", "{ 3 }"])
        self.assertEqual(F.cfree_answers(["// cfree-decl: fn h() {}", "// y"], 1, 2)[1],
                         ["`cfree-decl:` lines with no `cfree:` line directly below them"])
        # firsttry puts the declarations under the HELPERS line, outside every block
        twin = ADDER_V.replace("pub fn join", "// HELPERS: yours, here.\n\npub fn join0").replace(
            "    let t = join(a, b);", "    let t = Num { v: Vec::new() };")
        rel = "x.rs"
        items, _ = firsttry.ci.parse_items(rel, twin)
        it = next(x for x in items if x["id"] == "Q04.H8v")
        decl = ADDER_V[ADDER_V.index("pub fn join"):ADDER_V.index("// item:")].rstrip()
        var = firsttry.body_variant(twin, rel, "v", it, "{ let t = join(a, b); t }", None, decl)
        lines = var.split("\n")
        self.assertEqual(lines[lines.index("// HELPERS: yours, here.") + 2], "pub fn join(a: &Num, "
                         "b: &Num) -> (r: Num)")
        self.assertFalse(firsttry.static_forms(var, rel, it, ["no-adder"])["no-adder"][0])

    def test_cfree_targets(self):
        raw = ["  // cfree[P]: { x > -1 }", "  // cfree[P]: { var y := x; y > -1 }",
               "  ghost predicate Q(x: int) { true }", "  // cfree[Q]: { true",
               "  // cfree[Q]: }"]
        got, probs = F.cfree_targets(raw)
        self.assertEqual(got, [("P", "{ x > -1 }"), ("P", "{ var y := x; y > -1 }"),
                               ("Q", "{ true\n}")])
        self.assertEqual(probs, [])
        self.assertEqual(F.cfree_targets(["// cfree[P]: x"])[1],
                         ["cfree[P]: a `cfree:` line holds text outside its `{ … }` body"])


# Invented toys for the loop-direction rule (DV5c): a loop over the entries of a
# sequence, written once with each loop direction; the given check after it holds no
# loop. The Dafny toy's statement says only that the total is at least the first entry
# (no fold invariant, no slice lemma: DV6 fix round, as an earlier toy matched a course
# answer); `Q04.H8d` is the toy's own invented item id.
LOOPDIR_D = """module L {
  function Total(s: seq<nat>): nat
  {
    |s|
  }

  // item: Q04.H8d S4
  // form: loop-dir:up
  method Sum(s: seq<nat>) returns (t: nat)
    ensures |s| > 0 ==> t >= s[0]
  {
    t := 0;
    var i := |s|;
    while i > 0
      invariant 0 <= i <= |s|
      invariant i < |s| ==> t >= s[i]
    {
      t := s[i - 1] + t;
      i := i - 1;
    }
  }

  method SumCheck()
  {
    var t := Sum([1, 2]);
  }
}
"""

LOOPDIR_V = """use vstd::prelude::*;
verus! {

pub open spec fn tally(s: Seq<u8>) -> nat
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { tally(s.drop_last()) + s.last() as nat }
}

// item: Q04.H11v S4
// form: loop-dir:k:down
pub fn count(v: &Vec<u8>) -> (r: u64)
    requires v.len() < 1000,
    ensures r == tally(v@),
{
    let mut r: u64 = 0;
    let mut k: usize = 0;
    while k < v.len()
        invariant
            k <= v.len(),
            r == tally(v@.subrange(0, k as int)),
            r <= k * 255,
        decreases v.len() - k,
    {
        proof { assert(v@.subrange(0, k + 1).drop_last() =~= v@.subrange(0, k as int)); }
        r = r + v[k] as u64;
        k = k + 1;
    }
    proof { assert(v@.subrange(0, v.len() as int) =~= v@); }
    r
}

} // verus!
"""


ANCHOR = ("no loop both reads an argument of the item at its counter and assigns what the "
          "result is computed from")


class FormLoopDirection(unittest.TestCase):
    def test_vocabulary(self):
        for rule, arg in (("loop-dir:up", (None, "up")), ("loop-dir:down", (None, "down")),
                          ("loop-dir:i:up", ("i", "up")), ("loop-dir:k2:down", ("k2", "down"))):
            self.assertEqual(F.rule_name(rule), "loop-dir")
            self.assertEqual(F.loop_dir_arg(rule), arg)
        for bad in ("loop-dir", "loop-dir:", "loop-dir:left", "loop-dir:1i:up", "loop-dir:i:"):
            self.assertIsNone(F.rule_name(bad), bad)
        rules, probs = F.parse_rules("loop-dir:up, loop-dir:sideways")
        self.assertEqual(rules, ["loop-dir:up"])
        self.assertIn("loop-dir:[<x>:]up|down", probs[0])
        self.assertEqual(F.lang_problems(["loop-dir:up", "loop-dir:i:down"], "d"), [])
        self.assertEqual(F.lang_problems(["loop-dir:up"], "v"), [])

    def test_dafny_direction(self):
        line = LOOPDIR_D.split("\n").index("    while i > 0") + 1
        self.assertEqual(check(LOOPDIR_D, "d", "Q04.H8d", ["loop-dir:down"])["loop-dir:down"],
                         (True, ""))
        self.assertEqual(check(LOOPDIR_D, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"],
                         (False, f"the while loop at line {line} counts down, not up"))
        self.assertEqual(check(LOOPDIR_D, "d", "Q04.H8d", ["loop-dir:i:down"])[
            "loop-dir:i:down"], (True, ""))
        ok, why = check(LOOPDIR_D, "d", "Q04.H8d", ["loop-dir:j:down"])["loop-dir:j:down"]
        self.assertEqual((ok, why), (False, "no loop on `j` in the block's answer region"))
        up = LOOPDIR_D.replace("var i := |s|;", "var i := 0;").replace(
            "while i > 0", "while i < |s|").replace("i := i - 1;", "i := i + 1;")
        self.assertEqual(check(up, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"], (True, ""))
        # a step that is not +/- e, and a shadowing declaration, give no direction
        for old, new in (("i := i - 1;", "i := i / 2;"),
                         ("i := i - 1;", "i, t := i - 1, t;"),
                         ("i := i - 1;", "var i := 0;")):
            ok, why = check(LOOPDIR_D.replace(old, new), "d", "Q04.H8d",
                            ["loop-dir:down"])["loop-dir:down"]
            self.assertFalse(ok, new)
            self.assertIn("has no direction", why)
        # a guard identifier assigned another way (a flag) is no counter
        flag = LOOPDIR_D.replace("while i > 0", "while i > 0 && t >= 0").replace(
            "t := s[i - 1] + t;", "t := s[i - 1] + t; t := t;")
        self.assertEqual(check(flag, "d", "Q04.H8d", ["loop-dir:down"])["loop-dir:down"],
                         (True, ""))
        # no loop at all; a `for … downto` loop; a loop in the given check is not the answer
        nol = LOOPDIR_D.replace("while i > 0", "if i > 0")
        self.assertEqual(check(nol, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"],
                         (False, "no loop in the block's answer region"))
        fd = nol.replace("    t := 0;\n", "    t := 0;\n    for j := |s| downto 0 { t := s[j] + t; }\n")
        self.assertFalse(check(fd, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"][0])
        self.assertEqual(check(fd, "d", "Q04.H8d", ["loop-dir:j:down"])["loop-dir:j:down"],
                         (True, ""))
        given = nol.replace("    var t := Sum([1, 2]);",
                            "    var t := Sum([1, 2]);\n    var n := 0;\n"
                            "    while n < 3 { n := n + 1; }")
        self.assertEqual(check(given, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"],
                         (False, ANCHOR))             # given unknown: the check's loop is in
        #                                               the region, but computes nothing
        self.assertEqual(check(given, "d", "Q04.H8d", ["loop-dir:up"], given={"SumCheck"})[
            "loop-dir:up"], (False, "no loop in the block's answer region"))
        # comments never count
        com = nol.replace("    t := 0;\n", "    t := 0;\n    // while i < |s| { i := i + 1; }\n")
        self.assertFalse(check(com, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"][0])

    def test_verus_direction(self):
        line = LOOPDIR_V.split("\n").index("    while k < v.len()") + 1
        self.assertEqual(check(LOOPDIR_V, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"],
                         (True, ""))
        self.assertEqual(check(LOOPDIR_V, "v", "Q04.H11v", ["loop-dir:up"])["loop-dir:up"],
                         (True, ""))
        self.assertEqual(check(LOOPDIR_V, "v", "Q04.H11v", ["loop-dir:k:down"])[
            "loop-dir:k:down"], (False, f"the while loop at line {line} steps `k` up, not down"))
        # `=~=` inside an assertion is no assignment; `+=` and `-=` are steps
        down = LOOPDIR_V.replace("k = k + 1;", "k -= 1;")
        self.assertEqual(check(down, "v", "Q04.H11v", ["loop-dir:down"])["loop-dir:down"],
                         (True, ""))
        both = LOOPDIR_V.replace("k = k + 1;", "k += 2;\n        k = k - 1;")
        ok, why = check(both, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"]
        self.assertEqual((ok, why), (False, f"the while loop at line {line} assigns `k` other "
                                            "than by a step, not up"))
        never = LOOPDIR_V.replace("k = k + 1;", "r = r;")
        self.assertEqual(check(never, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"],
                         (False, f"the while loop at line {line} never steps `k`, not up"))
        loop = LOOPDIR_V.replace("while k < v.len()", "loop")
        self.assertIn("a `loop` has no guard",
                      check(loop, "v", "Q04.H11v", ["loop-dir:up"])["loop-dir:up"][1])
        # DV5c gaps lane: a guardless `loop` whose top-level exit is `if <c> { break }`
        # takes the exit condition's identifiers as its guard
        brk = loop.replace("    {\n        proof { assert(v@.subrange(0, k + 1)",
                           "    {\n        if k >= v.len() { break; }\n"
                           "        proof { assert(v@.subrange(0, k + 1)")
        self.assertEqual(check(brk, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"],
                         (True, ""))
        self.assertFalse(check(brk, "v", "Q04.H11v", ["loop-dir:k:down"])["loop-dir:k:down"][0])
        brk_down = brk.replace("k = k + 1;", "k = k - 1;")
        self.assertFalse(check(brk_down, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"][0])
        rev = LOOPDIR_V.replace("    let mut k: usize = 0;\n",
                                "    let mut k: usize = 0;\n    for j in (0..3).rev() { }\n")
        self.assertIn("counts down",
                      check(rev, "v", "Q04.H11v", ["loop-dir:up"])["loop-dir:up"][1])
        fwd = rev.replace(".rev()", "")
        self.assertEqual(check(fwd, "v", "Q04.H11v", ["loop-dir:up"])["loop-dir:up"], (True, ""))

    def test_reads_from_the_same_end(self):
        """DV5c fix round: the loop must read the sequence the way it counts, and
        carry the computation."""
        up = LOOPDIR_D.replace("var i := |s|;", "var i := 0;").replace(
            "while i > 0", "while i < |s|").replace("i := i - 1;", "i := i + 1;")
        line = up.split("\n").index("    while i < |s|") + 1
        self.assertEqual(check(up, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"], (True, ""))
        # an index counted back from the end, with the same counter
        rev = up.replace("t := s[i - 1] + t;", "t := s[|s| - i - 1] + t;")
        ok, why = check(rev, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"]
        self.assertFalse(ok)
        self.assertIn(f"the while loop at line {line} reads index", why)
        self.assertIn("which subtracts `i`", why)
        # through a definition in the body, and through a second counter stepping down
        via = up.replace("t := s[i - 1] + t;", "var j := |s| - i; t := s[j] + t;")
        self.assertIn("which subtracts `i`",
                      check(via, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"][1])
        two = up.replace("var i := 0;", "var i := 0;\n    var k := |s|;").replace(
            "t := s[i - 1] + t;", "k := k - 1; t := s[k] + t;")
        self.assertIn("and `k` steps down",
                      check(two, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"][1])
        # an index computed by a product or a call
        prod = up.replace("t := s[i - 1] + t;", "t := s[2 * i] + t;")
        self.assertIn("computed from `i` other than by adding it",
                      check(prod, "d", "Q04.H8d", ["loop-dir:up"])["loop-dir:up"][1])
        # a loop that only counts, beside an answer without one, is no loop of the form
        pad = LOOPDIR_D.replace("    while i > 0", "    t := Total(s);\n    var n := 0;\n"
                                "    while n < 1 { n := n + 1; }\n    while false")
        self.assertEqual(check(pad, "d", "Q04.H8d", ["loop-dir:n:up"])["loop-dir:n:up"],
                         (False, "no loop on `n` " + ANCHOR[len("no loop "):]))
        # Verus: `let j = v.len() - k` read through its definition
        vrev = LOOPDIR_V.replace("r = r + v[k] as u64;",
                                 "let j: usize = v.len() - 1 - k;\n        r = r + v[j] as u64;")
        self.assertIn("which subtracts `k`",
                      check(vrev, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"][1])
        self.assertEqual(check(LOOPDIR_V, "v", "Q04.H11v", ["loop-dir:k:up"])["loop-dir:k:up"],
                         (True, ""))

    def test_the_construct_free_answer_is_killed_in_the_forms_gate(self):
        """A twin's `cfree:` loop the other way, laid in by body_variant, fails the form."""
        twin = LOOPDIR_D.replace("  // form: loop-dir:up\n",
                                 "  // form: loop-dir:up\n  // cfree: { t := 0; }\n")
        rel = "x.dfy"
        items, _ = firsttry.ci.parse_items(rel, twin)
        it = next(x for x in items if x["id"] == "Q04.H8d")
        self.assertFalse(firsttry.static_forms(twin, rel, it, ["loop-dir:up"])["loop-dir:up"][0])
        body = ("{ t := 0; var i := 0; while i < |s| invariant 0 <= i <= |s| "
                "{ t := t + s[i]; i := i + 1; } }")
        variant = firsttry.body_variant(twin, rel, "d", it, body)
        self.assertEqual(firsttry.static_forms(variant, rel, it, ["loop-dir:up"]),
                         {"loop-dir:up": (True, "")})


# =====================================================================================
# firsttry: the hollow lint, the report, the judges (no verifier runs)
# =====================================================================================

def git_baseline(root):
    C.load_script("vcheck")
    import subprocess
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    import os
    for args in (("init", "-q", "-b", "main"), ("add", "-A"), ("commit", "-q", "-m", "shipped"),
                 ("switch", "-q", "-c", "work")):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                       env={**os.environ, **env})


class FormsInFirstTry(unittest.TestCase):
    def setUp(self):
        self.root = C.build_root(git=False)

    def tearDown(self):
        C.remove_root(self.root)

    def rep(self, rel, old, new):
        C.replace_in(self.root / rel, old, new)

    def line_of(self, rel, needle):
        return next(i for i, x in enumerate((self.root / rel).read_text().split("\n"), 1)
                    if needle in x)

    def test_a_shipped_measure_does_not_hide_an_open_spec(self):
        """Δ197's open item (DV5c): a declaration shipped WITH a `decreases` whose
        twin adds an `ensures` is an open spec; a twin that changes the shipped
        measure is not."""
        dl = ("module M {\n  function Evens(s: seq<nat>): seq<nat>\n    decreases |s|\n  {\n"
              "    if |s| <= 1 then s else [s[0]] + Evens(s[2..])\n  }\n}\n")
        dt = dl.replace("    decreases |s|\n", "    ensures |Evens(s)| <= |s|\n    decreases |s|\n")
        self.assertEqual(core.open_spec_symbols("x.dfy", "d", ltext=dl, ttext=dt,
                                                tpath="x.dfy"), ["M.Evens"])
        moved = dt.replace("    decreases |s|\n", "    decreases |s|, 0\n")
        self.assertEqual(core.open_spec_symbols("x.dfy", "d", ltext=dl, ttext=moved,
                                                tpath="x.dfy"), [])
        # an added measure alone is still no open spec, and one with an ensures still is
        bare = dl.replace("    decreases |s|\n", "")
        self.assertEqual(core.open_spec_symbols("x.dfy", "d", ltext=bare, ttext=dl,
                                                tpath="x.dfy"), [])
        self.assertEqual(core.open_spec_symbols("x.dfy", "d", ltext=bare, ttext=dt,
                                                tpath="x.dfy"), ["M.Evens"])
        vl = ("use vstd::prelude::*;\nverus! {\npub fn halve(n: u64) -> (r: u64)\n"
              "    decreases n,\n{\n    if n < 2 { 0 } else { 1 + halve(n - 2) }\n}\n}\n")
        vt = vl.replace("    decreases n,\n", "    ensures\n        r <= n,\n    decreases n,\n")
        self.assertEqual(core.open_spec_symbols("x.rs", "v", ltext=vl, ttext=vt,
                                                tpath="x.rs"), ["halve"])

    def test_lint_hollow(self):
        self.rep(LIB_RS, "// uses: calc\n// pair: Q04.H1d\n",
                 "// uses: calc\n// pair: Q04.H1d\n// form: no-nl, stable\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("Q04 lint-hollow: OK", out)
        self.rep(LIB_RS, "// form: no-nl, stable\n", "// form: no-nl, frob\n")
        self.rep(CORE, "  // uses: calc\n  lemma SumFormula",
                 "  // uses: calc\n  // form: bv-exec\n  lemma SumFormula")
        self.rep(CORE, "  // item: Q04.W1d S1\n", "  // item: Q04.W1d S1\n  // form: trigger\n")
        self.rep(EXIT_RS, "pub open spec fn double", "// form: stable\n\npub open spec fn double")
        self.rep(EXIT_RS, "// uses: lemma-call\npub proof fn double_mono",
                 "// uses: lemma-call\n// cfree: { }\npub proof fn double_mono")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 1, out + err)
        for want in (f"{LIB_RS}:{self.line_of(LIB_RS, '// form: no-nl, frob')}: Q04.H1v: `frob` "
                     "is not a form rule",
                     f"{CORE}:{self.line_of(CORE, '// form: bv-exec')}: Q04.H3d: the form "
                     "bv-exec applies to Verus blocks only",
                     f"{CORE}:{self.line_of(CORE, '// form: trigger')}: Q04.W1d: a `form:` line "
                     "on a W item; only H, X and T blocks that hold code carry forms",
                     f"{EXIT_RS}:{self.line_of(EXIT_RS, '// form: stable')}: a `form:` line "
                     "outside every item block",
                     f"{EXIT_RS}:{self.line_of(EXIT_RS, '// cfree:')}: a `cfree:` line belongs "
                     "in the reference twin only"):
            self.assertIn(want, out)

    def test_report_reports_a_finished_block_and_a_deleted_form_still_binds(self):
        self.rep(LIB_RS, "// uses: calc\n// pair: Q04.H1d\n",
                 "// uses: calc\n// pair: Q04.H1d\n// form: no-nl\n")
        git_baseline(self.root)
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertNotIn(": form: ", out)                    # the hole is open: not judged yet
        self.assertIn("forms not met 0", out)
        self.rep(LIB_RS, '    #[verifier::proof_note("Q04.H1v")] assume(false);\n',
                 "    assert(x + 0 == x) by (nonlinear_arith);\n")
        line = self.line_of(LIB_RS, "// item: Q04.H1v")
        nl = self.line_of(LIB_RS, "by (nonlinear_arith)")
        want = (f"{LIB_RS}:{line}: form: Q04.H1v: form no-nl not met (`nonlinear_arith` at line "
                f"{nl})")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn(want, out)
        self.assertIn("forms not met 1", out)
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("forms not met 1,", out)
        # deleting the form line does not lift the form (the shipped block's lines count)
        self.rep(LIB_RS, "// form: no-nl\n", "")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertIn(f"{LIB_RS}:{line}: form: Q04.H1v: form no-nl not met", out)
        # without the step the form holds
        self.rep(LIB_RS, "    assert(x + 0 == x) by (nonlinear_arith);\n", "    assert(true);\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertIn("forms not met 0", out)

    def test_judge_block_and_report_note(self):
        self.rep(EXIT_RS, "// need: pub proof fn double_is_twice(n: nat)\n",
                 "// need: pub proof fn double_is_twice(n: nat)\n// form: stable\n")
        ctx = firsttry.Ctx(self.root, "Q04")
        it = next(i for i in ctx.items if i["id"] == "Q04.X1v")
        self.rep(EXIT_RS, '    #[verifier::proof_note("Q04.X1v")] assume(false);\n', "")
        ctx = firsttry.Ctx(self.root, "Q04")
        it = next(i for i in ctx.items if i["id"] == "Q04.X1v")
        st, reasons = firsttry.judge_block(ctx, EXIT_RS, it, [], [], (),
                                           [("stable", "x is failed under seed 2")])
        self.assertEqual((st, reasons), ("fail", ["form stable not met (x is failed under "
                                                  "seed 2)"]))
        self.assertEqual(firsttry.item_forms(ctx, it), ["stable"])
        self.rep(CORE, "  // uses: calc\n  lemma SumFormula",
                 "  // uses: calc\n  // form: stable\n  lemma SumFormula")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertIn("note: the `stable` form of Q04.H3d is checked by --report --strict", out)


class Res:
    """An invented dvl Result, enough for the judges."""

    def __init__(self, verdict="verified", per=None, diags=(), stage="verify"):
        self.verdict, self.per_symbol, self.stage = verdict, dict(per or {}), stage
        self.diagnostics, self.holes, self.raw_dir = list(diags), [], "/nonexistent"


def rows(*results, solvers=(None,), seeds=(1, 2, 3)):
    out, k = [], 0
    for sv in solvers:
        for s in seeds:
            out.append(core.Row(sv, s, results[k], {}))
            k += 1
    return out


class StableJudge(unittest.TestCase):
    TEXT = ("module M {\n  lemma Given()\n    ensures true\n  {\n  }\n\n"
            "  // item: Q04.H1d S3\n  lemma Item(x: nat)\n    ensures x >= 0\n  {\n  }\n\n"
            "  lemma Helper2()\n    ensures true\n  {\n  }\n\n"
            "  // item: Q04.H2d S3\n  lemma Other()\n    ensures true\n  {\n  }\n}\n")

    def judge(self, rs):
        items, _ = firsttry.ci.parse_items("x.dfy", self.TEXT)
        it = next(i for i in items if i["id"] == "Q04.H1d")
        return firsttry.stable_judge(rs, Path("/nonexistent/x.dfy"), self.TEXT, "x.dfy", it)

    def test_rows(self):
        ok = {"M.Given": "verified", "M.Item": "verified", "M.Other": "failed"}
        self.assertEqual(self.judge(rows(*[Res(per=ok)] * 3)), (True, ""))
        # Helper2 sits in H1d's block (the block runs to the next marker)
        bad = dict(ok, **{"M.Helper2": "inconclusive"})
        got = self.judge(rows(Res(per=ok), Res(per=bad), Res(per=ok)))
        self.assertEqual(got, (False, "its declaration at line 13 is inconclusive under seed 2"))
        self.assertEqual(self.judge(rows(Res(per=ok), Res(per=ok),
                                         Res(per=dict(ok, **{"M.Given": "failed"})))),
                         (False, "a helper outside every block at line 2 is failed under seed 3"))
        self.assertIsNone(self.judge(rows(Res(per=ok), Res("killed(memory)"), Res(per=ok))))
        self.assertEqual(self.judge(rows(*[Res(per={"M.Given": "verified"})] * 3)),
                         (False, "no verification task ran for the block"))
        two = rows(*[Res(per=ok)] * 6, solvers=("4.12.1", "4.14.1"))
        self.assertEqual(self.judge(two), (True, ""))
        two[4] = core.Row("4.14.1", 2, Res(per=dict(ok, **{"M.Item": "failed"})), {})
        self.assertEqual(self.judge(two), (False, "its declaration at line 8 is failed under "
                                                  "4.14.1 seed 2"))
        diag = common.Diag("/nonexistent/x.dfy", 10, 1, "error", "x", "")
        self.assertEqual(self.judge(rows(Res(per=ok), Res("failed", ok, [diag]), Res(per=ok))),
                         (False, "an error at line 10 under seed 2"))

    def test_code_t_verdict(self):
        f = "/nonexistent/x.dfy"
        inside = common.Diag(f, 9, 1, "error", "Verification out of resource (M.Item)", "")
        outside = common.Diag(f, 3, 1, "error", "Verification out of resource (M.Given)", "")
        self.assertEqual(firsttry._code_t_verdict(Res("inconclusive", {}, [inside]), f, 7, 12),
                         ("fail", None))
        v, why = firsttry._code_t_verdict(Res("inconclusive", {}, [outside]), f, 7, 12)
        self.assertIsNone(v)
        self.assertIn("inconclusive outside the block", why)
        self.assertIsNone(firsttry._code_t_verdict(Res("killed(memory)"), f, 7, 12)[0])
        self.assertEqual(firsttry._code_t_verdict(Res(), f, 7, 12), ("pass", None))


# =====================================================================================
# vcheck: the sweep and the solver options (no verifier runs)
# =====================================================================================

class Sweep(unittest.TestCase):
    def test_summary(self):
        a = Res(per={"M.A": "verified", "M.B": "verified"})
        b = Res(per={"M.A": "verified", "M.B": "failed"}, verdict="failed")
        rs = rows(a, a, b)
        rs[0].counts, rs[1].counts, rs[2].counts = ({"M.A": 100, "M.B": 50}, {"M.A": 100,
                                                    "M.B": 150}, {"M.A": 101, "M.B": 100})
        s = core.sweep_summary(rs, "d")
        self.assertFalse(s["stable"])
        self.assertEqual(s["verdicts"], {"seed 1": "verified", "seed 2": "verified",
                                         "seed 3": "failed"})
        self.assertEqual(s["differs"], [("M.B", {"seed 1": "verified", "seed 2": "verified",
                                                 "seed 3": "failed"})])
        self.assertEqual([x[1] for x in s["flagged"]], ["M.B"])
        self.assertEqual(s["flag_cv"], 0.2)
        self.assertEqual(s["spread"][0][1], "M.B")
        # per solver: two solvers' counts never mix in one spread
        rs = rows(*[a] * 6, solvers=("4.12.1", "4.14.1"))
        for r in rs:
            r.counts = {"M.A": 100 if r.solver == "4.12.1" else 400}
        s = core.sweep_summary(rs, "d")
        self.assertTrue(s["stable"])
        self.assertEqual(s["flagged"], [])
        self.assertEqual({x[4] for x in s["spread"]}, {"4.12.1", "4.14.1"})

    def run_brittleness(self, rs, **kw):
        t = core.Target("d", C.ROOT / "tests/wrappers/fixtures/dafny/ok.dfy", C.ROOT)
        buf = io.StringIO()
        with unittest.mock.patch.object(core, "brittleness_rows", lambda *a, **k: rs), \
                contextlib.redirect_stdout(buf):
            code = core.brittleness(t, C.ROOT, **kw)
        return code, buf.getvalue()

    def test_output(self):
        a = Res(per={"M.A": "verified"})
        rs = rows(a, a, a)
        for r, c in zip(rs, (100, 150, 60)):
            r.counts = {"M.A": c}
        code, out = self.run_brittleness(rs)
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "vcheck --brittleness: tests/wrappers/fixtures/dafny/ok.dfy "
                                   "[dafny]: seed 1: verified · seed 2: verified · seed 3: "
                                   "verified — stable")
        self.assertIn("  spread above 20%: 1 symbol(s), flagged, never gating: M.A (CV 35.6%)",
                      lines)
        code, out = self.run_brittleness(rs, as_json=True)
        d = json.loads(out)
        self.assertEqual(d["verdicts"], {"1": "verified", "2": "verified", "3": "verified"})
        self.assertEqual(d["flagged"], [{"cv": 0.3563, "solver": None, "symbol": "M.A"}])
        self.assertIsNone(d["solvers"])
        self.assertTrue(d["stable"])
        rs = rows(*[a] * 5, Res("failed", {"M.A": "failed"}), solvers=("4.12.1", "4.14.1"))
        code, out = self.run_brittleness(rs, solvers=("4.12.1", "4.14.1"))
        self.assertEqual(code, 1)
        self.assertTrue(out.splitlines()[0].endswith(
            "4.12.1 seed 1: verified · 4.12.1 seed 2: verified · 4.12.1 seed 3: verified · "
            "4.14.1 seed 1: verified · 4.14.1 seed 2: verified · 4.14.1 seed 3: failed "
            "— NOT stable"), out)
        self.assertIn("  differs: M.A: 4.12.1 seed 1 verified, 4.12.1 seed 2 verified, 4.12.1 "
                      "seed 3 verified, 4.14.1 seed 1 verified, 4.14.1 seed 2 verified, 4.14.1 "
                      "seed 3 failed", out)
        code, out = self.run_brittleness(rs, as_json=True, solvers=("4.12.1", "4.14.1"))
        d = json.loads(out)
        self.assertEqual(d["solvers"], ["4.12.1", "4.14.1"])
        self.assertEqual(d["verdicts"]["4.14.1 seed 3"], "failed")
        self.assertNotIn("by_seed", d["differs"][0])

    # An invented standalone Verus file: a free fn, an inherent impl, a generic
    # impl, two trait impls and a nested module (neutral test material).
    VTOY = """use vstd::prelude::*;

verus! {

pub struct S { pub x: u64 }

impl S {
    pub fn get(&self) -> u64 { self.x }
}

pub struct G<A> { pub a: A }

impl<A> G<A> {
    pub fn g(&self) -> u64 { 0 }
}

pub trait T { fn t(&self) -> u64; }

impl T for S {
    fn t(&self) -> u64 { 0 }
}

impl<A> T for G<A> {
    fn t(&self) -> u64 { 1 }
}

mod inner {
    pub proof fn lemma_a() {}
}

proof fn lemma_b() {}

} // verus!
"""

    def test_verus_symbols_attributed_to_their_sites(self):
        """DV5d: a Verus run names a fn `<crate>::<path>` in its resource counts
        and a trait impl's method under its type (probed on the pinned Verus:
        `probe::S::t`, `probe::G::g`), so `--ref --brittleness` located no
        spread entry; site_of maps every form onto symbol_sites' keys."""
        d = Path(tempfile.mkdtemp(prefix="dvl-sites-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, d, True)
        f = d / "toy.rs"
        f.write_text(self.VTOY)
        t = core.Target("v", f, C.ROOT)
        sites = core.symbol_sites(t)
        self.assertEqual(set(sites), {"S::get", "G<A>::g", "T::t", "<S as T>::t",
                                      "<G<A> as T>::t", "inner::lemma_a", "lemma_b"})
        want = {"toy::S::get": "pub fn get(", "toy::G::g": "pub fn g(",
                "toy::S::t": "fn t(&self) -> u64 { 0 }", "toy::G::t": "fn t(&self) -> u64 { 1 }",
                "toy::inner::lemma_a": "pub proof fn lemma_a", "toy::lemma_b": "proof fn lemma_b",
                "S::get": "pub fn get(", "inner::lemma_a": "pub proof fn lemma_a"}
        for sym, text in want.items():
            self.assertEqual(core.site_of(sites, sym, "v"),
                             (str(f.resolve()), line_of(self.VTOY, text)), sym)
        self.assertIsNone(core.site_of(sites, "toy::missing", "v"))
        self.assertIsNone(core.site_of({"M.A": ("x", 1)}, "toy::M.A", "d"))
        # DV5e review fix: a run name two sites share is ambiguous (None, not the first
        # site), and a module of the target's own is never taken for the crate prefix
        self.assertIsNone(core.site_of({"<S as T>::t": ("lib.rs", 10),
                                        "<S as U>::t": ("lib.rs", 20)}, "mycrate::S::t", "v"))
        self.assertIsNone(core.site_of({"G<A>::g": ("lib.rs", 5), "G<B>::g": ("lib.rs", 9)},
                                       "mycrate::G::g", "v"))
        self.assertIsNone(core.site_of({"f": ("lib.rs", 3), "m::g": ("lib.rs", 7)}, "m::f", "v"))
        self.assertEqual(core.site_of({"f": ("lib.rs", 3), "m::g": ("lib.rs", 7)},
                                      "mycrate::m::g", "v", "mycrate"), ("lib.rs", 7))
        self.assertIsNone(core.site_of({"f": ("lib.rs", 3)}, "other::f", "v", "mycrate"))
        self.assertEqual(core.verus_crate_name(f), "toy")
        self.assertEqual(core.verus_run_name("m::<G<A> as n::T<B>>::t"), "m::G::t")
        # the reference sweep's text names the location, never the symbol
        rs = rows(*[Res(per={"S::t": "verified"})] * 3)
        for r, c in zip(rs, (100, 150, 60)):
            r.counts = {"toy::S::t": c}
        buf = io.StringIO()
        with unittest.mock.patch.object(core, "brittleness_rows", lambda *a, **k: rs), \
                unittest.mock.patch.object(core, "run_context", lambda *a: (None, t, None, None)), \
                contextlib.redirect_stdout(buf):
            core.brittleness(t, C.ROOT, reference=True)
        out = buf.getvalue()
        self.assertNotIn("(a declaration outside the target's files)", out)
        ln = line_of(self.VTOY, "fn t(&self) -> u64 { 0 }")
        self.assertIn(f"toy.rs:{ln}", out)
        self.assertNotIn("S::t", out)


def line_of(text, start):
    return next(i for i, x in enumerate(text.split("\n"), 1) if x.strip().startswith(start))


class SolverOptions(unittest.TestCase):
    OK = "tests/wrappers/fixtures/dafny/ok.dfy"
    V = "tests/wrappers/fixtures/verus/clean.rs"

    def test_pins(self):
        p = common.load_pins()["dafny"]
        self.assertEqual(core.D.solver_names(), ["4.12.1", "4.14.1"])
        self.assertEqual(p["solvers"]["4.12.1"]["path"], p["solver"])
        versions = (C.ROOT / "VERSIONS.md").read_text(encoding="utf-8")
        for name, e in p["solvers"].items():
            with self.subTest(solver=name):
                self.assertIn(f"`{e['path']}` → `{e['version']}` (sha256 "
                              f"`{e['sha256']['linux-x86_64']}`)", versions)
                self.assertIn(f"`{e['sha256']['macos-arm64']}`", versions)
        self.assertEqual(p["spread_flag_cv"], 0.2)
        self.assertEqual(common.load_pins()["verus"]["spread_flag_cv"], 0.2)

    def test_refusals_before_any_run(self):
        for args, rc, want in (
                (("--solvers", self.OK), 2, "--solvers goes with --brittleness"),
                (("--brittleness", "--solvers", "--solver", "4.14.1", self.OK), 2,
                 "--solvers and --solver are alternatives"),
                (("--gate", "--solver", "4.14.1", self.OK), 3, "keep the pinned solver (Δ10)"),
                (("--ref", "--solver", "4.14.1", self.OK), 3, "keep the pinned solver (Δ10)"),
                (("--solver", "4.14.1", self.V), 3, "Verus has one solver"),
                (("--brittleness", "--solvers", self.V), 3, "Verus has one solver"),
                (("--solver", "9.9.9", self.OK), 3, "--solver 9.9.9: not a solver bundled"),
                (("--test", "--solver", "4.14.1", self.OK), 2, "usage: vcheck --test"),
                (("--selftest", "--solvers"), 2, "--selftest takes no other argument"),
                (("--shipped", "--solver", "4.14.1", "Q04"), 2, "usage: vcheck --shipped")):
            with self.subTest(args=args):
                got, out, err = C.tool("vcheck", *args)
                self.assertEqual(got, rc, out + err)
                self.assertIn(want, err)
        # the library refuses the gate too
        res = core.D.verify(self.OK, gate=True, solver="4.14.1")
        self.assertEqual(res.verdict, "refused")

    def test_ref_brittleness_is_author_only(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        shutil.copytree(REFERENCE, root / "Solutions")
        rc, out, err = C.tool("vcheck", "--ref", "--brittleness",
                              root / "Solutions" / "dafny/Q/Q04_ProofCraft/core", root=root)
        self.assertEqual(rc, 3, out + err)
        self.assertIn("author-only", err)


# =====================================================================================
# specfreeze open_specs and the reference lint (QPLAN §6 Q44)
# =====================================================================================

TRAIT = ("\n// item: Q04.W2v S2\npub trait Lamp {\n    spec fn lit(&self) -> bool;\n\n"
         "    fn press(&mut self);\n}\n\n"
         "pub fn bump(a: u64) -> (r: u64)\n    requires\n        a < 100,\n{\n    a + 1\n}\n")
TRAIT_TWIN = ("\n// item: Q04.W2v S2\npub trait Lamp {\n    spec fn lit(&self) -> bool;\n\n"
              "    fn press(&mut self)\n        ensures\n            self.lit() == !old(self).lit(),"
              "\n    ;\n}\n\n"
              "pub fn bump(a: u64) -> (r: u64)\n    requires\n        a < 100,\n"
              "        a > 0,\n    ensures\n        r == a + 1,\n        forall|i: int, j: int| "
              "i < j ==> i <= j,\n{\n    a + 1\n}\n")
METHOD = ("\n  // item: Q04.W2d S2\n  method Reset(a: array<int>) returns (r: int)\n"
          "    requires a.Length > 0\n    modifies a\n  {\n    a[0] := 0;\n    r := 0;\n  }\n")
METHOD_TWIN = ("\n  // item: Q04.W2d S2\n  method Reset(a: array<int>) returns (r: int)\n"
               "    requires a.Length > 0\n    modifies a\n    ensures a[0] == 0\n"
               "    ensures r == 0\n  {\n    a[0] := 0;\n    r := 0;\n  }\n")


class OpenSpecs(unittest.TestCase):
    """A statement hole completed by adding requires/ensures clauses (QPLAN §6
    Q44): pinned under open_specs from the twins; added clauses are no freeze
    change, a dropped or changed shipped clause or a changed core still is."""

    def setUp(self):
        self.root = C.build_root()
        shutil.copytree(REFERENCE, self.root / "Solutions")
        anchor_v = "pub open spec fn double(n: nat) -> nat {"
        C.replace_in(self.root / LIB_RS, anchor_v, TRAIT + "\n" + anchor_v)
        C.replace_in(self.root / "Solutions" / LIB_RS, anchor_v, TRAIT_TWIN + "\n" + anchor_v)
        anchor_d = "  // item: Q04.C1dv S3 write:calc"
        C.replace_in(self.root / CORE, anchor_d, METHOD.lstrip("\n") + "\n" + anchor_d)
        C.replace_in(self.root / "Solutions" / CORE, anchor_d,
                     METHOD_TWIN.lstrip("\n") + "\n" + anchor_d)

    def tearDown(self):
        C.remove_root(self.root)

    def check(self):
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        return rc, out + err

    def test_pin_check_and_changes(self):
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn(f"open specs (QPLAN §6 Q44): {CORE}: Q04_ProofCraft.Reset, {LIB_RS}: "
                      f"Lamp::press, {LIB_RS}: bump", out)
        freeze = tomllib.loads((self.root / "expected" / "Q04.freeze").read_text())
        files = {f["path"]: f for f in freeze["file"]}
        self.assertEqual(files[LIB_RS]["open_specs"], ["Lamp::press", "bump"])
        self.assertEqual(files[LIB_RS]["spec_clauses"]["Lamp::press"],
                         {"requires": [], "ensures": []})
        self.assertEqual(len(files[LIB_RS]["spec_clauses"]["bump"]["requires"]), 1)
        self.assertEqual(files[CORE]["open_specs"], ["Q04_ProofCraft.Reset"])
        self.assertNotIn("open_specs", files[EXIT_RS])
        self.assertEqual(self.check()[0], 0)
        # the learner's answer: the twin's clauses added
        lib, core_ = self.root / LIB_RS, self.root / CORE
        lib.write_text(lib.read_text().replace(TRAIT, TRAIT_TWIN))
        core_.write_text(core_.read_text().replace(METHOD, METHOD_TWIN))
        rc, out = self.check()
        self.assertEqual(rc, 0, out)
        self.assertIn("specfreeze: Q04: 0 finding(s)", out)
        bump = self.line_of(LIB_RS, "pub fn bump")
        reset = self.line_of(CORE, "method Reset")
        for rel, old, new, line, sym in (
                (LIB_RS, "        a < 100,\n        a > 0,", "        a > 0,", bump, "bump"),
                (LIB_RS, "        a < 100,\n        a > 0,", "        a < 99,\n        a > 0,",
                 bump, "bump"),
                (LIB_RS, "pub fn bump(a: u64)", "pub fn bump(a: u32)", bump, "bump"),
                (LIB_RS, "        a > 0,\n    ensures", "        a > 0,\n    recommends\n"
                 "        a > 1,\n    ensures", bump, "bump"),
                (LIB_RS, "    fn press(&mut self)\n", "    fn press(&self)\n",
                 self.line_of(LIB_RS, "fn press"), "Lamp::press"),
                (CORE, "    requires a.Length > 0\n    modifies a\n    ensures a[0] == 0",
                 "    modifies a\n    ensures a[0] == 0", reset, "Q04_ProofCraft.Reset"),
                (CORE, "    modifies a\n    ensures a[0] == 0", "    ensures a[0] == 0", reset,
                 "Q04_ProofCraft.Reset")):
            with self.subTest(old=old, new=new):
                text = (self.root / rel).read_text()
                C.replace_in(self.root / rel, old, new)
                rc, out = self.check()
                self.assertEqual(rc, 1, out)
                self.assertIn(f"{rel}:{line}: freeze-changed — {sym}", out)
                (self.root / rel).write_text(text)
        # added clauses beyond the twin's, or one added clause dropped again: accepted
        C.replace_in(lib, "        r == a + 1,\n", "        r == a + 1,\n        r > 0,\n")
        C.replace_in(core_, "    ensures r == 0\n", "")
        self.assertEqual(self.check()[0], 0)

    def line_of(self, rel, needle):
        return next(i for i, x in enumerate((self.root / rel).read_text().split("\n"), 1)
                    if needle in x)

    def test_reference_lint(self):
        rc, out, err = C.tool("reference_lint.py", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("statement-differs", out, out + err)
        # a twin that drops a shipped clause is not an open spec: it differs
        tw = self.root / "Solutions" / LIB_RS
        C.replace_in(tw, "        a < 100,\n        a > 0,", "        a > 0,")
        rc, out, err = C.tool("reference_lint.py", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        line = next(i for i, x in enumerate(tw.read_text().split("\n"), 1) if "pub fn bump" in x)
        self.assertIn(f"Solutions/{LIB_RS}:{line}: statement-differs", out)

    def test_helpers(self):
        lib = (self.root / LIB_RS).read_text()
        twin = lib.replace(TRAIT, TRAIT_TWIN)
        got = core.open_spec_symbols(self.root / LIB_RS, "v", ltext=lib, ttext=twin,
                                     tpath=self.root / LIB_RS)
        self.assertEqual(got, ["Lamp::press", "bump"])
        self.assertEqual(core.open_spec_symbols(self.root / LIB_RS, "v", ltext=lib, ttext=twin,
                                                tpath=self.root / LIB_RS, exclude={"bump"}),
                         ["Lamp::press"])
        src = core.V.vs.parse(twin)
        it = next(x for x in src.walk() if x.kind == "fn" and x.name == "bump")
        text, cl = core.verus_spec_parts(src, it)
        self.assertEqual(text, "pub fn bump ( a : u64 ) -> ( r : u64 )")
        self.assertEqual(cl, {"requires": ["a < 100", "a > 0"],
                              "ensures": ["r == a + 1", "forall | i : int , j : int | i < j ==> "
                                                        "i <= j"]})
        self.assertTrue(core.spec_clauses_kept({"requires": ["a"], "ensures": []},
                                               {"requires": ["b", "a"], "ensures": ["c"]}))
        self.assertFalse(core.spec_clauses_kept({"requires": ["a", "b"]},
                                                {"requires": ["b", "a"]}))



# =====================================================================================
# Added measures: a `decreases` added to a declaration that shipped without one is
# no statement change (DV3b kits; Δ160's first Open item)
# =====================================================================================

MEASURE_D = ("  lemma Tally(n: nat)\n    ensures n >= 0\n  {\n  }\n\n"
             "  lemma Steady(n: nat)\n    ensures n >= 0\n    decreases n\n  {\n  }\n\n"
             "  method Idle(n: nat)\n  {\n  }\n\n")
MEASURE_D_TWIN = MEASURE_D.replace("  lemma Tally(n: nat)\n    ensures n >= 0\n",
                                   "  lemma Tally(n: nat)\n    ensures n >= 0\n    decreases n\n")
MEASURE_V = ("pub proof fn tally(n: nat)\n    ensures\n        n >= 0,\n{\n}\n\n"
             "pub open spec fn level(n: nat) -> nat {\n    0\n}\n\n")


class AddedMeasures(unittest.TestCase):
    """specfreeze --check, --against and the reference lint accept a `decreases`
    added to a declaration that shipped without one; a shipped measure stays
    frozen, and Dafny's `decreases *` and a Verus `when` are changes."""

    def setUp(self):
        self.root = C.build_root()
        shutil.copytree(REFERENCE, self.root / "Solutions")
        anchor_v = "pub open spec fn double(n: nat) -> nat {"
        for base in (self.root, self.root / "Solutions"):
            C.replace_in(base / LIB_RS, anchor_v, MEASURE_V + anchor_v)
        anchor_d = "  // item: Q04.C1dv S3 write:calc"
        C.replace_in(self.root / CORE, anchor_d, MEASURE_D + anchor_d)
        C.replace_in(self.root / "Solutions" / CORE, anchor_d, MEASURE_D_TWIN + anchor_d)

    def tearDown(self):
        C.remove_root(self.root)

    def check(self):
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        return rc, out + err

    def line_of(self, rel, needle):
        return next(i for i, x in enumerate((self.root / rel).read_text().split("\n"), 1)
                    if needle in x)

    def test_check(self):
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        # a twin that only adds a measure poses no open spec
        self.assertNotIn("open specs", out)
        freeze = tomllib.loads((self.root / "expected" / "Q04.freeze").read_text())
        self.assertFalse(any(f.get("open_specs") for f in freeze["file"]))
        self.assertEqual(self.check()[0], 0)
        accepted = (
            (CORE, "  lemma Tally(n: nat)\n    ensures n >= 0\n",
             "  lemma Tally(n: nat)\n    ensures n >= 0\n    decreases n, 0\n"),
            (CORE, "  method Idle(n: nat)\n", "  method Idle(n: nat)\n    decreases n\n"),
            (LIB_RS, "        n >= 0,\n{\n}", "        n >= 0,\n    decreases n,\n{\n}"),
            (LIB_RS, "pub open spec fn level(n: nat) -> nat {",
             "pub open spec fn level(n: nat) -> nat\n    decreases n,\n{"))
        for rel, old, new in accepted:
            with self.subTest(accepted=new):
                text = (self.root / rel).read_text()
                C.replace_in(self.root / rel, old, new)
                rc, out = self.check()
                self.assertEqual(rc, 0, out)
                (self.root / rel).write_text(text)
        # all four at once
        for rel, old, new in accepted:
            C.replace_in(self.root / rel, old, new)
        self.assertEqual(self.check()[0], 0)
        for rel, old, new in accepted:
            C.replace_in(self.root / rel, new, old)
        changed = (
            (CORE, "Steady(n: nat)\n    ensures n >= 0\n    decreases n\n",
             "Steady(n: nat)\n    ensures n >= 0\n    decreases n + 1\n", "lemma Steady",
             "Q04_ProofCraft.Steady"),
            (CORE, "Steady(n: nat)\n    ensures n >= 0\n    decreases n\n",
             "Steady(n: nat)\n    ensures n >= 0\n", "lemma Steady", "Q04_ProofCraft.Steady"),
            (CORE, "  method Idle(n: nat)\n", "  method Idle(n: nat)\n    decreases *\n",
             "method Idle", "Q04_ProofCraft.Idle"),
            (CORE, "  lemma Tally(n: nat)\n    ensures n >= 0\n",
             "  lemma Tally(n: nat)\n    ensures n >= 1\n    decreases n\n", "lemma Tally",
             "Q04_ProofCraft.Tally"),
            (LIB_RS, "pub open spec fn level(n: nat) -> nat {",
             "pub open spec fn level(n: nat) -> nat\n    decreases n when n > 0\n{",
             "spec fn level", "level"))
        for rel, old, new, needle, sym in changed:
            with self.subTest(changed=new):
                text = (self.root / rel).read_text()
                C.replace_in(self.root / rel, old, new)
                rc, out = self.check()
                self.assertEqual(rc, 1, out)
                self.assertIn(f"{rel}:{self.line_of(rel, needle)}: freeze-changed — {sym}", out)
                (self.root / rel).write_text(text)

    def test_reference_lint(self):
        rc, out, err = C.tool("reference_lint.py", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("statement-differs", out + err)
        # a twin that changes a shipped measure still differs
        tw = self.root / "Solutions" / CORE
        C.replace_in(tw, "Steady(n: nat)\n    ensures n >= 0\n    decreases n\n",
                     "Steady(n: nat)\n    ensures n >= 0\n    decreases n + 1\n")
        rc, out, err = C.tool("reference_lint.py", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        line = next(i for i, x in enumerate(tw.read_text().split("\n"), 1)
                    if "lemma Steady" in x)
        self.assertIn(f"Solutions/{CORE}:{line}: statement-differs", out)

    def test_against(self):
        from dvl import dafny as D, verus as V
        frozen, cand = self.root / "frozen.dfy", self.root / "cand.dfy"
        frozen.write_text("module M {\n" + MEASURE_D + "}\n")
        cand.write_text("module M {\n" + MEASURE_D_TWIN + "}\n")
        kinds = lambda fs: [(f.kind, f.message.split(":")[0]) for f in fs  # noqa: E731
                            if f.kind.startswith("freeze")]
        self.assertEqual(kinds(D.freeze_check(str(frozen), str(cand))), [])
        cand.write_text("module M {\n" + MEASURE_D.replace(
            "    decreases n\n", "    decreases n + 1\n") + "}\n")
        self.assertEqual(kinds(D.freeze_check(str(frozen), str(cand))),
                         [("freeze-changed", "M.Steady")])
        vfrozen = {s: h for s, h, *_ in V._spec_records(self._rs(MEASURE_V))}
        added = MEASURE_V.replace("        n >= 0,\n{", "        n >= 0,\n    decreases n,\n{")
        self.assertEqual(V.freeze_check(vfrozen, str(self._rs(added))), [])
        self.assertEqual(V.freeze_check(vfrozen, str(self._rs(added.replace(
            "        n >= 0,\n    decreases", "        n >= 1,\n    decreases"))))[0].kind,
            "freeze-changed")

    def _rs(self, body):
        p = self.root / "cand.rs"
        p.write_text("use vstd::prelude::*;\n\nverus! {\n\n" + body + "} // verus!\n")
        return p

    def test_measure_free_text(self):
        from dvl import dafny as D
        t = MEASURE_D_TWIN + "  method Spin()\n    decreases *\n  {\n  }\n"
        got = D.measure_free_text("module M {\n" + t + "}\n")
        self.assertEqual(got.count("\n"), t.count("\n") + 2)
        self.assertEqual(got.count("decreases"), 1)
        self.assertIn("decreases *", got)
        v = ("verus! {\nproof fn a(n: nat)\n    decreases n,\n{\n}\nspec fn b(n: nat) -> nat\n"
             "    decreases n when n > 0 via c\n{\n    0\n}\n}\n")
        got = core.V.vs.measure_free_text(v)
        self.assertEqual(got.count("\n"), v.count("\n"))
        self.assertEqual(got.count("decreases"), 1)
        self.assertIn("decreases n when n > 0 via c", got)
        self.assertEqual(core.measure_free_text("x = 1\n", "py"), "x = 1\n")


# =====================================================================================
# The empty-body gate's statement, spec-definition and open-statement holes, and
# its whole-goal NL/BV variants judged by the forms (DV3b integration)
# =====================================================================================

EB_VERUS = """use vstd::prelude::*;

verus! {

// item: Q99.H1v S6
/// A statement hole: a trait method ships with no specification.
pub trait Knob {
    spec fn level(&self) -> int;

    fn turn(&mut self);
}

pub fn turn_twice<T: Knob>(k: &mut T) {
    proof {
        #[verifier::proof_note("Q99.H1v")] assume(false);
    }
    k.turn();
    k.turn();
}

// item: Q99.H2v S2
/// A spec-definition hole.
pub uninterp spec fn depth(n: nat) -> nat
    decreases n,
;

// item: Q99.H3v S1
/// An open statement: the learner writes the ensures and the body.
#[verifier::external_body]
pub fn halve(x: u32) -> (r: u32)
{
    unimplemented!()
}

// item: Q99.H4v S11
// form: nl-steps:2
/// A proof hole whose whole-goal NL variant is a construct-free answer.
pub proof fn grow(a: nat, b: nat)
    requires
        a <= b,
    ensures
        a * a <= b * b,
{
    assume(false);
}

} // verus!
"""

EB_TWIN = EB_VERUS.replace("pub fn halve(x: u32) -> (r: u32)\n{",
                           "pub fn halve(x: u32) -> (r: u32)\n    ensures\n        r == x / 2,\n{")


class EmptyBodyHoleKinds(unittest.TestCase):
    def item(self, text, iid):
        items, errs = firsttry.ci.parse_items("verus/q/x/src/lib.rs", text)
        self.assertEqual(errs, [])
        return next(it for it in items if it["id"] == iid)

    def test_skip_reasons(self):
        rel = "verus/q/x/src/lib.rs"
        why = firsttry.eb_skip_reason(EB_VERUS, rel, self.item(EB_VERUS, "Q99.H1v"))
        self.assertIn("a statement hole", why)
        why = firsttry.eb_skip_reason(EB_VERUS, rel, self.item(EB_VERUS, "Q99.H2v"))
        self.assertIn("a spec-definition hole", why)
        for iid in ("Q99.H3v", "Q99.H4v"):
            self.assertIsNone(firsttry.eb_skip_reason(EB_VERUS, rel, self.item(EB_VERUS, iid)))
        # without the item's own labelled assume the block is no statement hole
        other = EB_VERUS.replace('proof_note("Q99.H1v")', 'proof_note("Q99.H9v")')
        self.assertIsNone(firsttry.eb_skip_reason(other, rel, self.item(other, "Q99.H1v")))
        self.assertIsNone(firsttry.eb_skip_reason("", "x.dfy", {"line_start": 1, "line_end": 1}))

    def test_open_statement(self):
        it = self.item(EB_VERUS, "Q99.H3v")
        got = firsttry.open_spec_statement(EB_VERUS, EB_TWIN, it, ["halve"])
        self.assertEqual(got, EB_TWIN)
        self.assertIsNone(firsttry.open_spec_statement(EB_VERUS, EB_TWIN, it, []))
        self.assertIsNone(firsttry.open_spec_statement(EB_VERUS, EB_TWIN,
                                                       self.item(EB_VERUS, "Q99.H4v"),
                                                       ["halve"]))

    def test_nl_variant_judged_by_the_forms(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(EB_VERUS, "Q99.H4v")
        rules = ["nl-steps:2"]
        res = Res("verified", {"E0 seed=1": "fails(error)", "NL seed=1": "verifies"})
        got = firsttry.eb_form_killed(EB_VERUS, rel, it, res, rules, set())
        self.assertEqual([m for m, _ in got], ["NL"])
        self.assertIn("form nl-steps:2 not met", got[0][1])
        # another mode closing the item, or no form, leaves the gate's verdict alone
        res2 = Res("verified", {"E0 seed=1": "verifies", "NL seed=1": "verifies"})
        self.assertIsNone(firsttry.eb_form_killed(EB_VERUS, rel, it, res2, rules, set()))
        self.assertIsNone(firsttry.eb_form_killed(EB_VERUS, rel, it, res, [], set()))
        # a form the whole-goal variant meets leaves it automation
        self.assertIsNone(firsttry.eb_form_killed(EB_VERUS, rel, it, res, ["nl-steps:1"],
                                                  set()))

    # reviewed by the tools lane (DV3b kits)
    def test_skip_needs_only_the_skipped_kind(self):
        rel = "verus/q/x/src/lib.rs"
        # the trait's first method may be of any mode
        exec_first = EB_VERUS.replace(
            "    spec fn level(&self) -> int;\n\n    fn turn(&mut self);\n",
            "    fn turn(&mut self);\n\n    spec fn level(&self) -> int;\n")
        self.assertNotEqual(exec_first, EB_VERUS)
        why = firsttry.eb_skip_reason(exec_first, rel, self.item(exec_first, "Q99.H1v"))
        self.assertIn("a statement hole", why)
        # a block that also holds another hole form is not skipped (the gate's
        # refusal stays loud)
        extra = EB_VERUS.replace(
            "    k.turn();\n    k.turn();\n}\n",
            "    k.turn();\n    k.turn();\n}\n\n#[verifier::external_body]\n"
            "pub fn helper() {\n}\n")
        self.assertNotEqual(extra, EB_VERUS)
        self.assertIsNone(firsttry.eb_skip_reason(extra, rel, self.item(extra, "Q99.H1v")))
        extra = EB_VERUS.replace(
            "    decreases n,\n;\n",
            "    decreases n,\n;\n\npub proof fn depth_zero()\n    ensures depth(0) == 0,\n"
            "{\n    admit();\n}\n")
        self.assertNotEqual(extra, EB_VERUS)
        self.assertIsNone(firsttry.eb_skip_reason(extra, rel, self.item(extra, "Q99.H2v")))

    def test_open_statement_variants_judged_on_the_twins_clauses(self):
        rel = "verus/q/x/src/lib.rs"
        learner = EB_VERUS.replace(
            "        a <= b,\n    ensures\n        a * a <= b * b,\n{",
            "        a <= b,\n{")
        twin = EB_VERUS.replace("a * a <= b * b", "a * 3 <= b * 3")
        self.assertNotEqual(learner, EB_VERUS)
        it = self.item(learner, "Q99.H4v")
        stext = firsttry.open_spec_statement(learner, twin, it, ["grow"])
        self.assertIn("a * 3 <= b * 3", stext)
        res = Res("verified", {"E0 seed=1": "fails(error)", "NL seed=1": "verifies"})
        # the learner text has no ensures, so no whole-goal variant: the gate fails
        self.assertIsNone(firsttry.eb_form_killed(learner, rel, it, res, ["nl-steps:2"], set()))
        got = firsttry.eb_form_killed(stext, rel, it, res, ["nl-steps:2"], set())
        self.assertEqual([m for m, _ in got], ["NL"])


# DV5a integration: a statement hole after an open statement (both languages),
# a bodyless Dafny function hole, and the not-admitted rule
EB_DAFNY = """module M {
  // item: Q99.H1d S2
  method Twice(x: int) returns (r: int)
  {
    r := 2 * x;
  }

  method Client(x: int) returns (r: int)
    ensures r == 4 * x
  {
    assume false;  // HOLE: delete this line once `Twice` is specified
    var y := Twice(x);
    r := Twice(y);
  }

  // item: Q99.H2d S5
  function Pick(a: nat): (r: nat)
    ensures r >= a

  // item: Q99.H3d S1
  method Run(x: int) returns (r: int)
    ensures r == x
  {
    assume false;
  }
}
"""

EB_VERUS_OPEN = """use vstd::prelude::*;

verus! {

// item: Q99.H5v S2
pub fn double(x: u8) -> (r: u16)
{
    2 * (x as u16)
}

pub fn client(x: u8) {
    proof {
        #[verifier::proof_note("Q99.H5v")] assume(false);
    }
    let r = double(x);
    assert(r == 2 * x);
}

} // verus!
"""


class EmptyBodyStatementAndFunctionHoles(unittest.TestCase):
    def item(self, rel, text, iid):
        items, errs = firsttry.ci.parse_items(rel, text)
        self.assertEqual(errs, [])
        return next(it for it in items if it["id"] == iid)

    def test_dafny_statement_hole_needs_its_open_statement(self):
        rel = "dafny/Q/Q99_X/std/Q99_X.dfy"
        it = self.item(rel, EB_DAFNY, "Q99.H1d")
        why = firsttry.eb_skip_reason(EB_DAFNY, rel, it, ["M.Twice"])
        self.assertTrue(why.startswith(firsttry.STATEMENT_SKIP), why)
        # without the open-statement pin the block is gated as shipped
        self.assertIsNone(firsttry.eb_skip_reason(EB_DAFNY, rel, it, []))
        self.assertIsNone(firsttry.eb_skip_reason(EB_DAFNY, rel, it))
        # a hole in the first declaration is never a statement hole
        it3 = self.item(rel, EB_DAFNY, "Q99.H3d")
        self.assertIsNone(firsttry.eb_skip_reason(EB_DAFNY, rel, it3, ["M.Run"]))

    def test_dafny_function_hole(self):
        rel = "dafny/Q/Q99_X/std/Q99_X.dfy"
        why = firsttry.eb_skip_reason(EB_DAFNY, rel, self.item(rel, EB_DAFNY, "Q99.H2d"))
        self.assertTrue(why.startswith(firsttry.FUNCTION_SKIP), why)
        method = EB_DAFNY.replace("function Pick(a: nat): (r: nat)", "lemma Pick(a: nat)")
        method = method.replace("ensures r >= a", "ensures a >= 0")
        self.assertIsNone(firsttry.eb_skip_reason(method, rel, self.item(rel, method, "Q99.H2d")))

    def test_verus_statement_hole_after_an_open_statement(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(rel, EB_VERUS_OPEN, "Q99.H5v")
        why = firsttry.eb_skip_reason(EB_VERUS_OPEN, rel, it, ["double"])
        self.assertTrue(why.startswith(firsttry.STATEMENT_SKIP), why)
        self.assertIsNone(firsttry.eb_skip_reason(EB_VERUS_OPEN, rel, it, []))
        # the labelled assume inside the open statement itself is no client's
        inside = EB_VERUS_OPEN.replace(
            "{\n    2 * (x as u16)\n}",
            "{\n    proof {\n        #[verifier::proof_note(\"Q99.H5v\")] assume(false);\n    }\n"
            "    2 * (x as u16)\n}")
        self.assertNotEqual(inside, EB_VERUS_OPEN)
        self.assertIsNone(firsttry.eb_skip_reason(inside, rel, self.item(rel, inside, "Q99.H5v"),
                                                  ["double"]))

    def test_admitted_false(self):
        ctx = unittest.mock.Mock()
        ctx.rec = {"admissible": {"Q99.H1d": {"admitted": False, "minutes": 0, "fallback": ""},
                                  "Q99.H2d": {"admitted": True, "minutes": 5, "fallback": ""}}}
        self.assertTrue(firsttry.admitted_false(ctx, "Q99.H1d"))
        self.assertFalse(firsttry.admitted_false(ctx, "Q99.H2d"))
        self.assertFalse(firsttry.admitted_false(ctx, "Q99.H3d"))
        ctx.rec = {"admissible": {}}
        self.assertFalse(firsttry.admitted_false(ctx, "Q99.H1d"))


EB_VERUS_PROSE = """use vstd::prelude::*;

verus! {

// item: Q99.H6v S2
// prose: lemma_toy_bound
/// Prose: state and prove `lemma_toy_bound`.
pub proof fn toy_client() {
    #[verifier::proof_note("Q99.H6v")] assume(false);  // HOLE: delete once stated
    // Uncomment as you go:
    // lemma_toy_bound(3);
    // assert(3 < 4);
}

} // verus!
"""

EB_VERUS_PROSE_TWIN = EB_VERUS_PROSE.replace(
    "pub proof fn toy_client() {\n"
    "    #[verifier::proof_note(\"Q99.H6v\")] assume(false);  // HOLE: delete once stated\n"
    "    // Uncomment as you go:\n"
    "    // lemma_toy_bound(3);\n"
    "    // assert(3 < 4);\n",
    "// reference-only: the prose item's statement\n"
    "pub proof fn lemma_toy_bound(x: int) requires x < 4 ensures x < 5 {}\n\n"
    "pub proof fn toy_client() {\n"
    "    lemma_toy_bound(3);\n"
    "    assert(3 < 4);\n")

EB_DAFNY_PROSE = """module M {
  // item: Q99.H7d S2
  // prose: ToyBound
  method ToyClient() {
    assume false;  // HOLE: delete once stated
    // Uncomment as you go:
    // ToyBound(3);
  }
}
"""


class EmptyBodyProseItems(unittest.TestCase):
    """A prose item (`// prose: <name>`, QPLAN §19.0): its shipped gate is skipped
    as a statement hole; the client gate uncomments its use-site check, which
    must call <name>; the proof gate empties the twin's <name>."""

    def item(self, rel, text, iid):
        items, errs = firsttry.ci.parse_items(rel, text)
        self.assertEqual(errs, [])
        return next(it for it in items if it["id"] == iid)

    def test_prose_name_and_skip(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(rel, EB_VERUS_PROSE, "Q99.H6v")
        self.assertEqual(firsttry.prose_name(EB_VERUS_PROSE, it), "lemma_toy_bound")
        why = firsttry.eb_skip_reason(EB_VERUS_PROSE, rel, it)
        self.assertTrue(why.startswith(firsttry.STATEMENT_SKIP), why)
        self.assertIn("prose item", why)
        plain = EB_VERUS_PROSE.replace("// prose: lemma_toy_bound\n", "")
        pit = self.item(rel, plain, "Q99.H6v")
        self.assertIsNone(firsttry.prose_name(plain, pit))
        drel = "dafny/Q/Q99_X/std/Q99_X.dfy"
        dit = self.item(drel, EB_DAFNY_PROSE, "Q99.H7d")
        dwhy = firsttry.eb_skip_reason(EB_DAFNY_PROSE, drel, dit)
        self.assertTrue(dwhy.startswith(firsttry.STATEMENT_SKIP), dwhy)

    def test_use_sites_and_uncomment(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(rel, EB_VERUS_PROSE, "Q99.H6v")
        lines = EB_VERUS_PROSE.split("\n")
        uses = firsttry.prose_use_sites(EB_VERUS_PROSE, rel, it, "lemma_toy_bound")
        self.assertEqual([lines[ln - 1].strip() for ln in uses], ["// lemma_toy_bound(3);"])
        self.assertEqual(firsttry.prose_use_sites(EB_VERUS_PROSE, rel, it, "other"), [])
        out = firsttry.uncomment_checks(list(lines), rel, it)
        self.assertIn("    lemma_toy_bound(3);", out)
        self.assertIn("    assert(3 < 4);", out)
        self.assertIn("    // Uncomment as you go:", out)

    def test_client_gate_needs_a_use_site_calling_the_name(self):
        rel = "verus/q/x/src/lib.rs"
        text = EB_VERUS_PROSE.replace("    // lemma_toy_bound(3);\n", "")
        ctx = unittest.mock.Mock()
        ctx.text.return_value = text
        ctx.root = Path(C.tempfile.mkdtemp(prefix="dvl-prose-", dir=C.TMP_BASE))
        try:
            ok, lines = firsttry.client_gate(ctx, self.item(rel, text, "Q99.H6v"), rel)
        finally:
            shutil.rmtree(ctx.root, ignore_errors=True)
        self.assertFalse(ok)
        self.assertIn("needs a commented use-site check", lines[0])

    def test_decl_line(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(rel, EB_VERUS_PROSE_TWIN, "Q99.H6v")
        ln = firsttry.prose_decl_line(EB_VERUS_PROSE_TWIN, rel, it, "lemma_toy_bound")
        self.assertIsNotNone(ln)
        self.assertIn("fn lemma_toy_bound", EB_VERUS_PROSE_TWIN.split("\n")[ln - 1])
        lit = self.item(rel, EB_VERUS_PROSE, "Q99.H6v")
        self.assertIsNone(firsttry.prose_decl_line(EB_VERUS_PROSE, rel, lit, "lemma_toy_bound"))
        drel = "dafny/Q/Q99_X/std/Q99_X.dfy"
        dtwin = EB_DAFNY_PROSE.replace("  method ToyClient()",
                                       "  lemma ToyBound(x: int) requires x < 4 ensures x < 5 {}\n"
                                       "  method ToyClient()")
        self.assertIsNotNone(firsttry.prose_decl_line(dtwin, drel, self.item(drel, dtwin,
                                                                            "Q99.H7d"),
                                                      "ToyBound"))

    def test_proof_gate_refuses_without_the_twin_declaration(self):
        rel = "verus/q/x/src/lib.rs"
        it = self.item(rel, EB_VERUS_PROSE, "Q99.H6v")
        ctx = unittest.mock.Mock()
        ctx.root = Path(C.tempfile.mkdtemp(prefix="dvl-prose-", dir=C.TMP_BASE))
        try:
            ok, lines = firsttry.prose_proof_gate(ctx, it, rel, "lemma_toy_bound", None, None)
            self.assertFalse(ok)
            self.assertIn("no reference twin", lines[0])
            twin = ctx.root / firsttry.core.REF_DIR / rel
            twin.parent.mkdir(parents=True)
            twin.write_text(EB_VERUS_PROSE, encoding="utf-8")
            ok, lines = firsttry.prose_proof_gate(ctx, it, rel, "lemma_toy_bound", None, None)
            self.assertFalse(ok)
            self.assertIn("declares no `lemma_toy_bound`", lines[0])
        finally:
            shutil.rmtree(ctx.root, ignore_errors=True)


EB_VERUS_EXEC_PROSE_TWIN = """use vstd::prelude::*;

verus! {

// item: Q99.H8v S13
// prose: toy_larger
// triv: { a }
pub fn toy_larger(a: u64, b: u64) -> (r: u64)
    ensures
        r == if a < b { b } else { a },
{
    if a < b { b } else { a }
}

fn toy_larger_use() {
    let r = toy_larger(1, 2);
    assert(r == 2);
}

} // verus!
"""


class ExecProseTriv(unittest.TestCase):
    """DV5c (Δ197's open item): an exec prose item's proof gate runs TRIV with its
    twin's `triv:` body; when the twin's code holds no proof text, TRIV alone is
    the gate (the light modes strip proof only)."""

    def setUp(self):
        self.root = Path(C.tempfile.mkdtemp(prefix="dvl-prose-triv-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.rel = "verus/q/x/src/lib.rs"

    def gate(self, twin_text, verdict="failed"):
        twin = self.root / firsttry.core.REF_DIR / self.rel
        twin.parent.mkdir(parents=True, exist_ok=True)
        twin.write_text(twin_text, encoding="utf-8")
        items, _ = firsttry.ci.parse_items(self.rel, twin_text)
        it = next(x for x in items if x["id"] == "Q99.H8v")
        ctx = unittest.mock.Mock()
        ctx.root = self.root
        calls = []

        def fake(target, sym, **kw):
            calls.append((sym, kw.get("modes"), kw.get("triv_body")))
            return common.Result("verus", target, 1, verdict, "verify", 0, [], [], [],
                                 {"TRIV seed=1": "fails(error)"})
        with unittest.mock.patch.object(firsttry.V, "empty_body", fake):
            ok, lines = firsttry.prose_proof_gate(ctx, it, self.rel, "toy_larger", None, None)
        return ok, lines, calls

    def test_exec_prose_fn(self):
        items, _ = firsttry.ci.parse_items(self.rel, EB_VERUS_EXEC_PROSE_TWIN)
        it = next(x for x in items if x["id"] == "Q99.H8v")
        fn, needs = firsttry.exec_prose_fn(EB_VERUS_EXEC_PROSE_TWIN, it, "toy_larger")
        self.assertEqual((fn.name, needs), ("toy_larger", False))
        proved = EB_VERUS_EXEC_PROSE_TWIN.replace("    if a < b { b } else { a }\n",
                                                  "    proof { assert(true); }\n"
                                                  "    if a < b { b } else { a }\n")
        self.assertTrue(firsttry.exec_prose_fn(proved, it, "toy_larger")[1])
        self.assertEqual(firsttry.exec_prose_fn(EB_VERUS_EXEC_PROSE_TWIN, it, "toy_absent"),
                         (None, None))
        spec = EB_VERUS_EXEC_PROSE_TWIN.replace("pub fn toy_larger(a: u64, b: u64) -> (r: u64)",
                                                "pub open spec fn toy_larger(a: u64, b: u64) "
                                                "-> (r: u64)")
        self.assertEqual(firsttry.exec_prose_fn(spec, it, "toy_larger"), (None, None))

    def test_code_without_proof_is_gated_by_triv_alone(self):
        ok, lines, calls = self.gate(EB_VERUS_EXEC_PROSE_TWIN)
        self.assertTrue(ok, lines)
        self.assertEqual(calls, [("toy_larger", ["TRIV"], "{ a }")])
        self.assertIn("with the declared trivial body (TRIV) fails in every run", lines[0])
        self.assertIn("the light modes, which strip proof only, are not run", lines[1])
        ok, lines, _ = self.gate(EB_VERUS_EXEC_PROSE_TWIN, verdict="verified")
        self.assertFalse(ok)
        self.assertIn("FALLS TO AUTOMATION", lines[0])

    def test_code_with_proof_runs_every_mode_and_triv(self):
        proved = EB_VERUS_EXEC_PROSE_TWIN.replace("    if a < b { b } else { a }\n",
                                                  "    proof { assert(true); }\n"
                                                  "    if a < b { b } else { a }\n")
        ok, lines, calls = self.gate(proved)
        self.assertTrue(ok, lines)
        self.assertEqual(calls, [("toy_larger", None, "{ a }")])

    def test_no_triv_line_keeps_the_light_modes_and_advises(self):
        ok, lines, calls = self.gate(EB_VERUS_EXEC_PROSE_TWIN.replace("// triv: { a }\n", ""),
                                     verdict="verified")
        self.assertFalse(ok)
        self.assertEqual(calls, [("toy_larger", None, None)])
        self.assertIn("declare its trivial body", lines[-1])


class PythonOverlay(unittest.TestCase):
    """dvl.python's scratch overlay (the reference gate and the TRIV mode) also
    carries tests/corpus/, so a frozen test that reads the corpus through
    fvh.corpus's default root runs there instead of skipping (Δ167)."""

    def test_overlay_carries_the_corpus(self):
        from dvl import python as PY
        root = Path(C.tempfile.mkdtemp(prefix="dvl-overlay-", dir=C.TMP_BASE))
        try:
            (root / "harness" / "q").mkdir(parents=True)
            (root / "harness" / "q" / "a.py").write_text("x = 1\n")
            s = PY._overlay(root, "harness/q/a.py", "x = 2\n")
            try:
                self.assertEqual((s / "harness" / "q" / "a.py").read_text(), "x = 2\n")
                self.assertFalse((s / "tests").exists())
            finally:
                shutil.rmtree(s, ignore_errors=True)
            (root / "tests" / "corpus" / "dafny" / "D-1").mkdir(parents=True)
            (root / "tests" / "corpus" / "dafny" / "D-1" / "manifest.toml").write_text("k = 1\n")
            s = PY._overlay(root, "harness/q/a.py", "x = 3\n")
            try:
                got = s / "tests" / "corpus" / "dafny" / "D-1" / "manifest.toml"
                self.assertEqual(got.read_text(), "k = 1\n")
                self.assertFalse(got.is_symlink())
            finally:
                shutil.rmtree(s, ignore_errors=True)
        finally:
            shutil.rmtree(root, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
