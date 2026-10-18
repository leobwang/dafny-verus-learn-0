"""Lab 2's public task forms (QPLAN §25.6): scripts/dvl/benchstrip.py's second transform
(verus-lab2-form, dafny-lab2-form: the specification removed, the prose and the code kept, an
empty witness) on invented text; the check, independent of the transform, that no shipped
form under bench/local/q/lab2pub/ keeps its specification or a proof body; the stratum file
and bench/public/POOLS.toml's [[draw]] records against each other and against the seeded
order; the pool file keeping its draws when a pool is re-pinned; and, when the sets are
installed, the forms re-derived from them byte for byte. The user's decisions of 2026-10-14:
D28 (the non-recursive definitions only the specification uses leave the form and travel
with the sealed reference; no shipped form keeps one), D29 (NOTICE names each set's
repository, commit and licence as fetched) and D30 (Lab 1's draw excludes the tasks Lab 2's
public strata drew)."""

import hashlib
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import bench  # noqa: E402
from dvl import benchstrip as B  # noqa: E402
from dvl import judge as J  # noqa: E402
from dvl import lab2pub as L  # noqa: E402

VERUS = '''/*
### ID
HumanEval/900
*/
use vstd::prelude::*;

verus! {

// Part of the specification.
spec fn total(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { s[0] + total(s.drop_first()) }
}

// Used by the proof only.
spec fn total_rev(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { s.last() + total_rev(s.drop_last()) }
}

proof fn lemma_same(s: Seq<int>)
    ensures total(s) == total_rev(s),
    decreases s.len(),
{
    assume(false);
}

fn add_up(v: &Vec<u8>) -> (r: u64)
    requires
        v.len() < 100,
    ensures
        r == total(v@.map(|_i, x: u8| x as int)),
{
    let mut acc: u64 = 0;
    let mut i: usize = 0;
    while i < v.len()
        invariant
            i <= v.len(),
            acc <= 255 * i,
        decreases v.len() - i,
    {
        proof {
            lemma_same(v@.map(|_i, x: u8| x as int));
        }
        assert(acc <= 255 * i);
        acc = acc + v[i] as u64;
        i = i + 1;
    }
    acc
}

} // verus!

/*
### PROMPT
def add_up(v):
    """The sum of v."""
*/
'''

DAFNY = '''// <vc-preamble>
function Sum(s: seq<int>): int
{
  if |s| == 0 then 0 else s[0] + Sum(s[1..])
}
// </vc-preamble>

// <vc-helpers>
lemma SumAppend(s: seq<int>, x: int)
  ensures Sum(s + [x]) == Sum(s) + x
{
  assert (s + [x])[1..] == s[1..] + [x];
}

function Unused(x: int): int { x }

function Twice(x: int): int { x + x }
// </vc-helpers>

// <vc-spec>
method AddUp(s: seq<int>) returns (r: int)
  requires |s| < 100
  ensures r == Sum(s)
// </vc-spec>
// <vc-code>
{
  r := 0;
  var i := 0;
  ghost var seen := [];
  while i < |s|
    invariant 0 <= i <= |s|
    invariant r == Sum(s[..i])
    decreases |s| - i
  {
    SumAppend(s[..i], s[i]);
    assert s[..i + 1] == s[..i] + [s[i]];
    calc {
      r + s[i];
    }
    r := r + s[i];
    i := i + 1;
  }
  assert s[..i] == s by { }
  r := Twice(r) - r;
}
// </vc-code>
'''


class VerusForm(unittest.TestCase):
    def setUp(self):
        self.f = B.lab2_form_verus(VERUS)
        self.t = self.f.text

    def test_the_specification_and_the_proofs_go(self):
        self.assertEqual(self.f.name, "add_up")
        for gone in ("invariant", "proof {", "assert(", "lemma_same", "total_rev",
                     "Used by the proof only", "v.len() < 100", "r == total("):
            self.assertNotIn(gone, self.t, gone)
        self.assertFalse([x for x in self.t.splitlines()
                          if x.strip().startswith(("requires", "ensures"))])
        self.assertEqual(B.spec_residue(self.t, "verus", "add_up"), [])
        self.assertNotEqual(B.spec_residue(VERUS, "verus", "add_up"), [])

    def test_the_code_the_measure_the_vocabulary_and_the_prompt_stay(self):
        for kept in ("decreases v.len() - i,", "acc = acc + v[i] as u64;", "acc\n}",
                     "// Part of the specification.", "### PROMPT", "HumanEval/900"):
            self.assertIn(kept, self.t, kept)
        # the spec fn the ensures named is kept, and public, so the grader's lemmas can name it
        self.assertIn("pub open spec fn total(", self.t)

    def test_an_empty_witness_is_added(self):
        self.assertEqual(self.f.witness, "add_up_witness")
        self.assertIn("fn add_up_witness() {\n}\n", self.t)
        c = J.candidate(self.t, "verus", "add_up")
        self.assertEqual((c["requires"], c["ensures"]), ([], []))
        self.assertEqual(c["results"], [["r", "u64"]])

    def test_idempotent_on_its_own_output_but_for_the_witness(self):
        with self.assertRaises(B.StripError):         # no ensures left to remove
            B.lab2_form_verus(self.t)

    def test_files_that_pose_no_single_task_are_refused(self):
        two = VERUS.replace("} // verus!", "fn other() {\n}\n\n} // verus!")
        with self.assertRaisesRegex(B.StripError, "2 exec fns"):
            B.lab2_form_verus(two)
        named = VERUS.replace("    acc\n}", "    lemma_same(seq![]);\n    acc\n}")
        with self.assertRaises(B.StripError):
            B.lab2_form_verus(named)

    def test_publish_leaves_a_public_spec_fn_alone(self):
        src = "use vstd::prelude::*;\nverus! {\npub open spec fn a() -> int { 1 }\n" \
              "pub(crate) spec fn b() -> int { 2 }\nspec fn c() -> int { 3 }\n" \
              "pub closed spec fn d() -> int { 4 }\n} // verus!\n"
        out = B.lab2_publish_verus(src)
        for line in ("pub open spec fn a()", "pub open spec fn b()", "pub open spec fn c()",
                     "pub closed spec fn d()"):
            self.assertIn(line, out)


class DafnyForm(unittest.TestCase):
    def setUp(self):
        self.f = B.lab2_form_dafny(DAFNY, prose="def add_up(v):\n    The sum of v. */")
        self.t = self.f.text

    def test_the_specification_and_the_proofs_go(self):
        self.assertEqual(self.f.name, "AddUp")
        for gone in ("invariant", "lemma", "SumAppend", "assert", "calc", "ghost var",
                     "Unused", "|s| < 100", "r == Sum(s)"):
            self.assertNotIn(gone, self.t, gone)
        self.assertFalse([x for x in self.t.splitlines()
                          if x.strip().startswith(("requires", "ensures"))])
        self.assertEqual(B.spec_residue(self.t, "dafny", "AddUp"), [])
        self.assertNotEqual(B.spec_residue(DAFNY, "dafny", "AddUp"), [])

    def test_the_code_the_measure_and_the_definitions_stay(self):
        for kept in ("decreases |s| - i", "r := r + s[i];", "function Sum(",
                     "function Twice(", "r := Twice(r) - r;", "// <vc-code>"):
            self.assertIn(kept, self.t, kept)

    def test_the_prose_goes_above_the_method_and_cannot_close_its_comment(self):
        i, j = self.t.index("/* The task's prose:"), self.t.index("method AddUp(")
        self.assertLess(i, j)
        self.assertIn("The sum of v. * /", self.t)

    def test_an_empty_witness_is_added(self):
        self.assertEqual(self.f.witness, "AddUpWitness")
        self.assertIn("method AddUpWitness()\n{\n}\n", self.t)
        c = J.candidate(self.t, "dafny", "AddUp")
        self.assertEqual((c["requires"], c["ensures"]), ([], []))

    def test_files_that_pose_no_single_task_are_refused(self):
        with self.assertRaisesRegex(B.StripError, "2 methods"):
            B.lab2_form_dafny(DAFNY + "\nmethod Other() {}\n")
        with self.assertRaisesRegex(B.StripError, "assume"):
            B.lab2_form_dafny(DAFNY.replace("r := 0;", "r := 0;\n  assume r == 0;"))
        with self.assertRaisesRegex(B.StripError, "forall"):
            B.lab2_form_dafny(DAFNY.replace("r := 0;", "r := 0;\n  forall k | 0 <= k < 0 { }"))
        with self.assertRaisesRegex(B.StripError, "no ensures"):
            B.lab2_form_dafny(DAFNY.replace("  ensures r == Sum(s)\n", ""))

    def test_registered_beside_the_other_transforms(self):
        for name, ext in (("verus-lab2-form", ".rs"), ("dafny-lab2-form", ".dfy")):
            self.assertIn(name, B.TRANSFORMS)
            self.assertIn(name, B.TRANSFORM_NOTES)
            self.assertEqual(B.apply(name, "x.txt", b"x"), (b"x", False))
        out, changed = B.apply("dafny-lab2-form", "t.dfy", DAFNY.encode())
        self.assertTrue(changed)
        self.assertNotIn(b"ensures", out)


VERUS_D28 = """use vstd::prelude::*;

verus! {

spec fn total(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 { 0 } else { s[0] + total(s.drop_first()) }
}

spec fn sums_to(s: Seq<int>, r: int) -> bool {
    r == total(s)
}

spec fn small(r: int) -> bool {
    0 <= r < 1000
}

spec fn fine(s: Seq<int>, r: int) -> bool {
    sums_to(s, r) && small(r)
}

spec fn steps(n: nat) -> nat
    decreases n,
{
    if n == 0 { unit() } else { 1 + steps((n - 1) as nat) }
}

spec fn unit() -> nat {
    0
}

spec fn spare(n: nat) -> bool {
    n < 100
}

fn add_up(v: Vec<i64>) -> (r: i64)
    ensures
        fine(v@.map(|_i, x: i64| x as int), r as int) && steps(3) >= 0,
{
    let mut acc: i64 = 0;
    let mut i: usize = 0;
    while i < v.len()
        decreases v.len() - i,
    {
        // keep the sum in range
        // across the loop

        assert(i < v.len());
        acc = acc;
        i = i + 1;
    }
    acc
}

} // verus!
"""

DAFNY_D28 = """function Sum(s: seq<int>): int
{
  if |s| == 0 then 0 else s[0] + Sum(s[1..])
}

function Clamp(x: int): int
{
  if x < 0 then 0 else x
}

predicate SumsTo(s: seq<int>, r: int)
{
  r == Sum(s)
}

predicate Small(r: int)
{
  0 <= r < 1000
}

method AddUp(s: seq<int>) returns (r: int)
  ensures SumsTo(s, r) && Small(r)
{
  r := 0;
  var i := 0;
  while i < |s|
    invariant 0 <= i <= |s|
  {
    r := r + Clamp(s[i]);
    i := i + 1;
  }
}
"""


class Decision28(unittest.TestCase):
    """The non-recursive definitions only the specification uses leave the form (D28)."""

    def test_d37_retains_only_the_definition_used_under_a_quantifier(self):
        verus = '''use vstd::prelude::*;
verus! {
spec fn parcel(x: int) -> int { x * 31 + 17 }
spec fn plain(x: int) -> bool { x != 19 }
fn stamp(x: u32) -> (r: u32)
    ensures exists|j: int, k: int| parcel(j) == r && k == j,
            plain(r as int),
{ x }
}
'''
        f = B.lab2_form_verus(verus)
        self.assertIn("pub open spec fn parcel", f.text)
        self.assertNotIn("spec fn plain", f.text)
        self.assertEqual(f.definition_names, ["plain"])
        # the kept definition travels beside the form, never named in it
        self.assertEqual(f.quantified, ["parcel"])
        self.assertNotIn("quantified", f.text)
        self.assertEqual(B.definition_residue(f.text, "verus", kept=f.quantified), [])
        self.assertEqual([n for _, n in B.definition_residue(f.text, "verus")], ["parcel"])
        dafny = '''function Parcel(x: int): int { x * 31 + 17 }
predicate Plain(x: int) { x != 19 }
method Stamp(x: int) returns (r: int)
  ensures (exists j: int :: Parcel(j) == r) && Plain(r)
{ r := x; }
'''
        f = B.lab2_form_dafny(dafny)
        self.assertIn("function Parcel", f.text)
        self.assertNotIn("predicate Plain", f.text)
        self.assertEqual(f.definition_names, ["Plain"])
        self.assertEqual(f.quantified, ["Parcel"])
        self.assertNotIn("quantified", f.text)
        self.assertEqual(B.definition_residue(f.text, "dafny", kept=f.quantified), [])
        self.assertEqual([n for _, n in B.definition_residue(f.text, "dafny")], ["Parcel"])

    def test_verus_seals_the_non_recursive_specification_only_spec_fns(self):
        f = B.lab2_form_verus(VERUS_D28)
        self.assertEqual(f.definition_names, ["sums_to", "small", "fine"])
        for gone in ("fn sums_to(", "fn small(", "fn fine("):
            self.assertNotIn(gone, f.text)
        # recursive ones stay, published; so does what a kept recursive one names
        self.assertIn("pub open spec fn total(", f.text)
        self.assertIn("pub open spec fn steps(", f.text)
        self.assertIn("pub open spec fn unit(", f.text)
        # `spare` is named by nothing: proof-only, removed and not sealed
        self.assertNotIn("fn spare(", f.text)
        self.assertEqual(len(f.definitions), 3)
        self.assertTrue(all(d.startswith("pub open spec fn ") for d in f.definitions))
        self.assertIn("r == total(s)", f.definitions[0])
        self.assertEqual(B.definition_residue(f.text, "verus"), [])
        self.assertEqual(B.spec_residue(f.text, "verus", "add_up"), [])

    def test_dafny_seals_the_non_recursive_specification_only_definitions(self):
        f = B.lab2_form_dafny(DAFNY_D28, prose="add up")
        self.assertEqual(f.definition_names, ["SumsTo", "Small"])
        self.assertNotIn("predicate SumsTo", f.text)
        self.assertNotIn("predicate Small", f.text)
        self.assertIn("function Sum(", f.text)          # recursive: stays
        self.assertIn("function Clamp(", f.text)        # the code calls it: stays
        self.assertEqual(f.definitions[1], "predicate Small(r: int)\n{\n  0 <= r < 1000\n}")
        self.assertEqual(B.definition_residue(f.text, "dafny"), [])

    def test_the_independent_check_sees_a_kept_specification_only_definition(self):
        plain = DAFNY_D28.replace("ensures SumsTo(s, r) && Small(r)", "ensures r == Sum(s)")
        plain = plain[:plain.index("predicate SumsTo")] + plain[plain.index("method AddUp"):]
        kept = B.lab2_form_dafny(plain).text
        self.assertEqual(B.definition_residue(kept, "dafny"), [])
        planted = kept.replace("method AddUp(", "predicate Spare(r: int)\n{\n  r > 0\n}\n\n"
                                                "method AddUp(", 1)
        self.assertEqual([n for _, n in B.definition_residue(planted, "dafny")], ["Spare"])
        v = B.lab2_form_verus(VERUS_D28).text.replace(
            "fn add_up(", "pub open spec fn spare(r: int) -> bool {\n    r > 0\n}\n\nfn add_up(",
            1)
        self.assertEqual([n for _, n in B.definition_residue(v, "verus")], ["spare"])

    def test_a_comment_above_a_removed_proof_step_goes_with_it(self):
        f = B.lab2_form_verus(VERUS_D28)
        self.assertNotIn("keep the sum in range", f.text)
        self.assertNotIn("assert(", f.text)
        self.assertIn("acc = acc;", f.text)

    def test_the_split_rule(self):
        g = {"a": {"b"}, "b": set(), "r": {"r", "c"}, "c": set(), "s": {"a"}, "k": set()}
        keep, sealed = B.split_definitions(g, code_named={"k"}, spec_named={"s", "r"})
        self.assertEqual(sealed, {"s", "a", "b"})
        self.assertEqual(keep, {"k", "r", "c"})

    def test_the_grader_renames_the_sealed_definitions(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "truthcheck_d28", ROOT / "sandbox" / "image" / "truthcheck.py")
        T = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(T)
        f = B.lab2_form_dafny(DAFNY_D28)
        ref = {"definitions": f.definitions, "requires": [], "ensures": ["SumsTo(s, r) && Small(r)"]}
        # a delivery that states its own SumsTo word for word keeps it; Small is the grader's
        mine = f.text + "\npredicate SumsTo(s: seq<int>, r: int)\n{\n  r == Sum(s)\n}\n"
        defs, req, ens = T._renamed(ref, mine)
        self.assertEqual(ens, ("SumsTo(s, r) && dvl_ref_Small(r)",))
        self.assertEqual(len(defs), 1)
        self.assertIn("predicate dvl_ref_Small(", defs[0])
        defs, req, ens = T._renamed(ref, f.text)
        self.assertEqual(ens, ("dvl_ref_SumsTo(s, r) && dvl_ref_Small(r)",))


def _stratum():
    return tomllib.loads((ROOT / "bench/local/q/lab2pub/STRATUM.toml").read_text(encoding="utf-8"))


class ShippedForms(unittest.TestCase):
    """bench/local/q/lab2pub/ as shipped (tracked: no set needs to be installed)."""

    def setUp(self):
        self.st = _stratum()
        self.cards = self.st["card"]

    def test_the_stratum_is_lab_2s_five_and_five(self):
        self.assertEqual(self.st["lab"], "Q15")
        self.assertEqual(self.st["stratum"], "public")
        by = {}
        for c in self.cards:
            by.setdefault(c["lang"], []).append(c["id"])
            self.assertRegex(c["id"], r"^(vp|dp)[1-5]-he\d{3}$")
            self.assertEqual(c["id"].startswith("vp"), c["lang"] == "verus")
            self.assertEqual(c["id"][-3:], f"{c['humaneval']:03d}")
        self.assertEqual({k: len(v) for k, v in by.items()}, {"verus": 5, "dafny": 5})
        self.assertEqual(len({c["humaneval"] for c in self.cards}), 10)

    def test_no_form_keeps_its_specification_or_a_proof_body(self):
        for c in self.cards:
            with self.subTest(card=c["id"]):
                p = L.form_path(ROOT, c["id"], c["lang"])
                text = p.read_text(encoding="utf-8")
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), c["form_sha256"])
                self.assertEqual(B.spec_residue(text, c["lang"], c["name"]), [])
                got = J.candidate(text, c["lang"], c["name"])
                self.assertEqual((got["requires"], got["ensures"]), ([], []))
                w = f"{c['name']}_witness" if (c["lang"] == "verus" or "_" in c["name"]
                                               or c["name"][:1].islower()) \
                    else f"{c['name']}Witness"
                if c["lang"] == "verus":
                    self.assertIn(f"fn {w}() {{\n}}\n", text)
                else:
                    self.assertIn(f"method {w}()\n{{\n}}\n", text)
                self.assertIn(f"Lab 2 public task {c['id']} (Q15", text)

    def test_no_form_keeps_a_non_recursive_specification_only_definition(self):
        """Every definition a form ships that no code needs is one D37 keeps: the set the
        form shows equals the one its card's kept_definitions_sha256 records (the names are
        author-side), and the form names none of them as kept."""
        kept = 0
        for c in self.cards:
            with self.subTest(card=c["id"]):
                text = L.form_path(ROOT, c["id"], c["lang"]).read_text(encoding="utf-8")
                names = [n for _, n in B.definition_residue(text, c["lang"])]
                self.assertEqual(L.kept_digest(names), c.get("kept_definitions_sha256"))
                self.assertEqual(B.definition_residue(text, c["lang"], kept=names), [])
                self.assertNotRegex(text, r"(?i)quantified|D37")
                kept += len(names)
        self.assertEqual(kept, 1)

    def test_the_header_says_what_a_delivery_adds(self):
        self.assertEqual(self.st.get("forms_date"), "2026-10-16")
        for c in self.cards:
            with self.subTest(card=c["id"]):
                text = L.form_path(ROOT, c["id"], c["lang"]).read_text(encoding="utf-8")
                head = " ".join(x[2:].strip() for x in text.splitlines()[:10]
                                if x.startswith("//"))
                for want in ("with any definition they need", "You may add proof annotations",
                             "never change its executable code",
                             "the definitions only its specification used removed"):
                    self.assertIn(want, head)
                if c["lang"] == "verus":
                    self.assertIn("`pub open`", head)

    def test_the_grader_reads_the_cards(self):
        cards = J.lab_cards(ROOT, "Q15")
        for c in self.cards:
            self.assertEqual(cards[c["id"]][:2], (c["lang"], c["name"]))

    def test_no_reference_is_learner_visible(self):
        d = ROOT / "bench/local/q/lab2pub"
        names = {p.name for p in d.rglob("*") if p.is_file()}
        self.assertEqual(names - {f"{c['id']}{'.rs' if c['lang'] == 'verus' else '.dfy'}"
                                  for c in self.cards}, {"STRATUM.toml", "NOTICE"})


class Notice(unittest.TestCase):
    """NOTICE (the user's decision D29): each upstream set's name, repository, commit and
    licence as bench/manifest.toml pins and checks them, and both LICENSE files."""

    def test_the_notice_names_each_sets_pins_and_licence(self):
        text = (ROOT / "bench/local/q/lab2pub/NOTICE").read_text(encoding="utf-8")
        sets = bench.load_manifest(ROOT)[1]
        for key, cards, label, _ in L.NOTICE_SETS:
            meta = sets[L.STRATA[key]["set"]]
            with self.subTest(set=meta["name"]):
                for want in (cards, label, meta["repo"], meta["commit"],
                             f"licence     {meta['licence']['spdx']}, as fetched",
                             f"checked     {meta['licence']['checked']}",
                             f"{label} LICENSE (bench/public/{meta['name']}/LICENSE)"):
                    self.assertIn(want, text)
        self.assertIn("decision D28", text)
        self.assertIn("decision D29", text)
        self.assertEqual(text.count("Permission is hereby granted"), 2)

    def test_the_notice_is_the_generated_one(self):
        need = [bench.set_dir(ROOT, n) / "LICENSE" for n in ("humaneval-verus", "vericoding")]
        if not all(f.is_file() for f in need):
            self.skipTest("humaneval-verus and vericoding are not both installed")
        self.assertEqual((ROOT / "bench/local/q/lab2pub/NOTICE").read_text(encoding="utf-8"),
                         L.notice_text(ROOT))


class Lab1Draw(unittest.TestCase):
    """Lab 1's draw excludes the tasks Lab 2's public strata drew (the user's decision D30)."""

    def test_lab_1_excludes_lab_2s_problems_across_languages(self):
        lab2 = next(d for d in bench.load_draws(ROOT) if d.get("lab") == "Q15"
                    and d.get("stratum") == "verus")
        pool = bench.load_pools(ROOT)["humaneval-verus"]["tasks"]
        got = bench.lab_members(ROOT, "humaneval-verus", "Q12")
        self.assertEqual(len(lab2["drawn"]), 5)
        self.assertFalse(set(got) & set(lab2["drawn"]))
        drawn_ids = {int(c.split("-he")[1]) for d in bench.load_draws(ROOT)
                     if d.get("lab") == "Q15" for c in d.get("cards", [])}
        for task in got:
            self.assertNotIn(int(re.search(r"human_eval_(\d+)", task).group(1)), drawn_ids)
        excluded = [task for task in pool
                    if int(re.search(r"human_eval_(\d+)", task).group(1)) in drawn_ids]
        self.assertEqual(sorted(set(got) | set(excluded)), sorted(pool))
        self.assertEqual(len(got), 74)
        # Lab 2 itself, and a set no other lab drew from, keep their whole pools
        self.assertEqual(len(bench.lab_members(ROOT, "humaneval-verus", "Q15")), len(pool))
        self.assertEqual(bench.lab_members(ROOT, "dafnybench", "Q12"),
                         sorted(bench.load_pools(ROOT)["dafnybench"]["tasks"]))

    def test_get_bench_lists_the_members_lab_1_may_draw(self):
        import subprocess
        def run(*args):
            return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/dvl/bench.py"),
                                   *args], capture_output=True, text=True)
        p = run("--members", "humaneval-verus", "--lab", "Q12")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.split(), bench.lab_members(ROOT, "humaneval-verus", "Q12"))
        self.assertIn("74 of the pool's 83", p.stderr)
        p2 = run("--members", "humaneval-verus", "--lab", "Q12", "--seed", "s")
        self.assertEqual(p2.stdout.split(), L.draw_order(p.stdout.split(), "s"))
        self.assertNotEqual(run("--members", "humaneval-verus").returncode, 0)

    def test_the_rule_is_written_where_lab_1_is_pre_registered(self):
        st = (ROOT / "bench/local/q/lab1/STRATUM.toml").read_text(encoding="utf-8")
        self.assertIn("decision D30", st)
        ch = " ".join((ROOT / "docs/Q12_PracticeIC.md").read_text(encoding="utf-8").split())
        self.assertIn("across both languages", ch)
        tex = " ".join((ROOT / "paper/Q12_answers.tex").read_text(encoding="utf-8").split())
        self.assertIn("across both languages", tex)


class DrawRecords(unittest.TestCase):
    def setUp(self):
        self.st = _stratum()
        self.draws = {d["stratum"]: d for d in bench.load_draws(ROOT) if d.get("lab") == "Q15"}
        self.pools = bench.load_pools(ROOT)

    def test_each_stratum_has_its_draw_and_the_stratum_file_is_its_result(self):
        self.assertEqual(sorted(self.draws), ["dafny", "verus"])
        for key, d in self.draws.items():
            st = L.STRATA[key]
            mine = [c for c in self.st["card"] if c["set"] == st["set"]]
            self.assertEqual(d["drawn"], [c["task"] for c in mine])
            self.assertEqual(d["cards"], [c["id"] for c in mine])
            pool = self.pools[st["set"]]
            self.assertEqual(d["pool_sha256"], pool["pool_sha256"])
            self.assertEqual(d["set_sha256"], pool["set_sha256"])
            self.assertTrue(set(d["drawn"]) <= set(pool["tasks"]))
            self.assertFalse(set(d["drawn"]) & set(d["skipped"]))
            self.assertEqual(len(d["drawn"]) + len(d["skipped"]), d["walked"])
            self.assertRegex(d["prereg_sha256"], r"^[0-9a-f]{64}$")

    def test_the_verus_order_is_the_seeded_one(self):
        d = self.draws["verus"]
        tasks, _ = L.members(ROOT, "verus")       # the whole pool: POOLS.toml alone
        order = L.draw_order(tasks, d["seed"])
        self.assertEqual(L.order_digest(order), d["order_sha256"])
        self.assertEqual(set(order[:d["walked"]]), set(d["drawn"]) | set(d["skipped"]))
        self.assertEqual(order[d["walked"] - 1], d["drawn"][-1])

    def test_the_dafny_order_is_the_seeded_one(self):
        if not (bench.set_dir(ROOT, "vericoding") / "tasks" / "vericoding_benchmark_v1.csv").is_file():
            self.skipTest("vericoding is not installed (its subset index gives the stratum)")
        d = self.draws["dafny"]
        tasks, _ = L.members(ROOT, "dafny")
        self.assertEqual(len(tasks), d["members"])
        order = L.draw_order(tasks, d["seed"])
        self.assertEqual(L.order_digest(order), d["order_sha256"])
        self.assertEqual(set(order[:d["walked"]]), set(d["drawn"]) | set(d["skipped"]))

    def test_the_draw_order_is_a_pure_function_of_the_members_and_the_seed(self):
        a = L.draw_order(["c", "a", "b", "d"], "s")
        self.assertEqual(a, L.draw_order(["d", "b", "a", "c"], "s"))
        self.assertEqual(sorted(a), ["a", "b", "c", "d"])


class PoolFileKeepsDraws(unittest.TestCase):
    def test_re_pinning_a_pool_keeps_the_draws_and_a_draw_replaces_its_own(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-lab2pub-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "bench" / "public").mkdir(parents=True)
        pools = {"s": {"set": "s", "set_sha256": "0" * 64, "pins_sha256": "1" * 64,
                       "validated": "2026-10-13", "selection": "{}", "rows": 2, "pool": 1,
                       "pool_sha256": bench.pool_digest(["a.rs"]), "by_reason": {"pool": 1},
                       "by_stratum": {"verus": [2, 1]}, "wall_s": 1.0, "segments": 1,
                       "tasks": ["a.rs"]}}
        bench.write_pools(tmp, pools)
        draw = {"lab": "Q15", "stratum": "verus", "set": "s", "seed": "x", "drawn": ["a.rs"],
                "cards": ["vp1-he000"], "skipped": {"b.rs": "C1: why"}, "walked": 2}
        bench.write_draws(tmp, [draw, dict(draw, stratum="dafny")])
        bench.write_pools(tmp, bench.load_pools(tmp))          # what --pin-pool does
        got = bench.load_draws(tmp)
        self.assertEqual([d["stratum"] for d in got], ["verus", "dafny"])
        self.assertEqual(got[0]["skipped"], {"b.rs": "C1: why"})
        bench.write_draws(tmp, [dict(draw, seed="y")])
        got = bench.load_draws(tmp)
        self.assertEqual(sorted((d["stratum"], d["seed"]) for d in got),
                         [("dafny", "x"), ("verus", "y")])
        self.assertEqual(bench.load_pools(tmp)["s"]["tasks"], ["a.rs"])


class InstalledSets(unittest.TestCase):
    def test_every_form_re_derives_from_the_installed_sets(self):
        need = [bench.set_dir(ROOT, n) / "answers" for n in ("humaneval-verus", "vericoding")]
        if not all(d.is_dir() for d in need):
            self.skipTest("humaneval-verus and vericoding are not both installed")
        self.assertEqual(L.build(ROOT, check=True), [])

    def test_the_sealed_definitions_travel_with_the_reference(self):
        need = [bench.set_dir(ROOT, n) / "answers" for n in ("humaneval-verus", "vericoding")]
        if not all(d.is_dir() for d in need):
            self.skipTest("humaneval-verus and vericoding are not both installed")
        keys = {v["set"]: k for k, v in L.STRATA.items()}
        rows = L._vericoding_rows(ROOT)
        sealed = 0
        for c in _stratum()["card"]:
            with self.subTest(card=c["id"]):
                key = keys[c["set"]]
                text, f, _ = L.make_form(ROOT, key, c["task"], c["id"], rows)
                ref = L.reference(ROOT, key, c["task"], c["name"])
                self.assertEqual(ref["definitions"], f.definitions)
                self.assertEqual(ref["definition_names"], f.definition_names)
                rec = tomllib.loads(L.reference_toml(ROOT, key, c["id"], c["task"], c["name"]))
                self.assertEqual(rec["definitions"], f.definitions)
                self.assertEqual(rec["definition_names"], f.definition_names)
                self.assertEqual((rec["requires"], rec["ensures"]),
                                 (ref["requires"], ref["ensures"]))
                answer = L.base_answer(ROOT, key, c["task"])
                for n, d in zip(f.definition_names, f.definitions):
                    self.assertIn(d, answer)              # word for word, as the answer has it
                    self.assertNotRegex(text, rf"\b(fn|function|predicate)\s+{n}\b")
                    self.assertRegex(" ".join(ref["requires"] + ref["ensures"]) + " ".join(
                        f.definitions), rf"\b{n}\b")
                sealed += len(f.definitions)
        self.assertGreater(sealed, 0)

    def test_each_drawn_answer_keeps_the_forms_code(self):
        """D27's code check: each drawn answer (its proof annotations kept) is a delivery of
        its form, once the form's witness is there."""
        from dvl import labcode as LC
        need = [bench.set_dir(ROOT, n) / "answers" for n in ("humaneval-verus", "vericoding")]
        if not all(d.is_dir() for d in need):
            self.skipTest("humaneval-verus and vericoding are not both installed")
        keys = {v["set"]: k for k, v in L.STRATA.items()}
        for c in _stratum()["card"]:
            with self.subTest(card=c["id"]):
                key = keys[c["set"]]
                form = L.form_path(ROOT, c["id"], c["lang"])
                ftext = form.read_text(encoding="utf-8")
                answer = L.base_answer(ROOT, key, c["task"])
                i = ftext.index("A non-vacuity witness for `")
                i = ftext.rindex("\n", 0, i) + 1
                j = ftext.index("{\n}\n", i) + 4
                witness = ftext[i:j]
                if c["lang"] == "verus":
                    k = answer.rindex("} // verus!")
                    delivery = answer[:k] + witness + "\n" + answer[k:]
                else:
                    delivery = answer.rstrip("\n") + "\n\n" + witness
                rel = form.relative_to(ROOT)
                self.assertEqual(LC.code_findings(rel, rel, ttext=ftext, dtext=delivery), [])

    def test_each_drawn_task_passes_the_static_checks(self):
        need = [bench.set_dir(ROOT, n) / "answers" for n in ("humaneval-verus", "vericoding")]
        if not all(d.is_dir() for d in need):
            self.skipTest("humaneval-verus and vericoding are not both installed")
        keys = {v["set"]: k for k, v in L.STRATA.items()}
        for c in _stratum()["card"]:
            with self.subTest(card=c["id"]):
                _, f, number, ref = L.static_check(ROOT, keys[c["set"]], c["task"])
                self.assertEqual((f.name, number), (c["name"], c["humaneval"]))
                self.assertTrue(ref["ensures"])


if __name__ == "__main__":
    unittest.main()
