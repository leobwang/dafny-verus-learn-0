"""scripts/avoid.sh: the disjointness gate between the Q and R tracks (spec §2.7,
design §9, PLAN.md §5.5). No test here starts a solver or reads a reference
tree. The fixture roots are throwaway copies of the committed registry with
every module set to planned (so no item home of an armed module is required)
and a few invented exercise files at the paths the registry gives; the gate's
inputs (waivers, curated list, owners) are written per test and passed with
the hidden --inputs option. Every expected line was captured from a real run.

Run: python3 -B -m unittest discover -s tests/ci -p 'test_avoid*.py'
"""

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_common as C  # noqa: E402

AVOID = C.ROOT / "scripts" / "avoid.sh"
sys.path.insert(0, str(C.ROOT / "scripts" / "avoid"))
sys.path.insert(0, str(C.ROOT / "scripts"))
import avoid as A  # noqa: E402

WAIVER_HEAD = "id\tstate\tkey\tsource\tdirection\treason\tcost\n"
CURATED_HEAD = "name\tkind\tapplies\torigin\n"
OWNERS = """schema = 1
[conventions]
keys = ["wf"]
[[artifact]]
owner = "Q"
name = "BigNat"
words = ["big nat", "limb"]
[[artifact]]
owner = "R"
name = "regex"
words = ["deriv"]
[[tag]]
owner = "R"
tag = "midpoint-overflow"
homes = ["R01.P1dv"]
tokens = ["midpoint"]
"""

Q_EX = "dafny/Q/Q01_Hello/core/Q01_Hello.dfy"
R_EX = "dafny/R/R01_Hello/core/R01_Hello.dfy"
R_V = "verus/r/r01_hello/src/lib.rs"

Q_FILE = """module Q01_Hello {
  // item: Q01.H1d S1
  lemma ShiftTwice(x: nat)
    ensures x + 0 == x

  // item: Q01.X1d S1
  // need: function PadTo(s: seq<nat>, k: nat): seq<nat>
  // Uncomment as you go:
  // lemma PadToCheck() ensures |PadTo([], 2)| == 2 {}
}
"""


def run(root, inputs, *args):
    p = subprocess.run(["bash", str(AVOID), "--root", str(root), "--inputs", str(inputs), *args],
                       capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout, p.stderr


class Fixture(unittest.TestCase):
    """A planned-only root with one Q exercise file; tests add R files."""

    def setUp(self):
        self.base = C.tmpdir("avoid-")
        self.root = self.base / "root"
        self.root.mkdir()
        text = (C.ROOT / "MODULES.toml").read_text(encoding="utf-8")
        text = re.sub(r'(?m)^status = "(authoring|shipped)"$', 'status = "planned"', text)
        (self.root / "MODULES.toml").write_text(text, encoding="utf-8")
        self.inputs = self.base / "inputs"
        (self.inputs / "avoid").mkdir(parents=True)
        self.waivers()
        self.curated()
        (self.inputs / "avoid" / "owners.toml").write_text(OWNERS, encoding="utf-8")
        self.put(Q_EX, Q_FILE)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def put(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def waivers(self, *rows):
        (self.inputs / "avoid.waivers.tsv").write_text(
            "# test\n" + WAIVER_HEAD + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")

    def curated(self, *rows):
        (self.inputs / "avoid.curated").write_text(
            CURATED_HEAD + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")

    def avoid(self, *args):
        return run(self.root, self.inputs, *args)


class Names(Fixture):
    def test_no_r_material_passes(self):
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("avoid.sh: OK: tracks Q+R; Q: 1 declarations, 2 sources (2 hole-bodied)", out)
        self.assertIn("R: 0 declarations", out)

    def test_an_r_name_equal_to_a_q_hole_is_a_hit(self):
        self.put(R_EX, "module R01_Hello {\n  lemma lemma_shift_twice(y: nat) ensures y == y {}\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"shift_twice R:{R_EX}:2 ↔ hole:Q01.H1d (Q:{Q_EX}:3)   [name]", out)

    def test_a_posed_need_line_is_a_source(self):
        self.put(R_V, "verus! {\npub open spec fn pad_to(n: nat) -> nat { n }\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"pad_to R:{R_V}:2 ↔ hole:Q01.X1d (Q:{Q_EX}:7)   [name]", out)

    def test_a_commented_check_is_not_a_source(self):
        self.put(R_EX, "module R01_Hello {\n  lemma PadToCheck() {}\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))

    def test_a_convention_key_is_never_compared(self):
        self.put("docs/Q01_Hello.md", "# Q01\n\n```rust\npub open spec fn wf(&self) -> bool\n```\n")
        self.put(R_V, "verus! {\npub open spec fn wf(x: nat) -> bool { true }\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))

    def test_a_chapter_fence_is_a_source(self):
        self.put("docs/Q01_Hello.md", "# Q01\n\n```dafny\nfunction Weight(n: nat): nat\n```\n")
        self.put(R_EX, "module R01_Hello {\n  function Weight(n: nat): nat { n }\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"weight R:{R_EX}:2 ↔ chapter:Q01 (Q:docs/Q01_Hello.md:4)   [name]", out)

    def test_a_written_problem_is_a_source(self):
        self.put("paper/Q01_problems.tex",
                 "\\begin{problem}\n\\begin{veruscode}\nproof fn carry_out(a: u64)\n"
                 "\\end{veruscode}\n\\end{problem}\n")
        self.put(R_EX, "module R01_Hello {\n  lemma CarryOut() {}\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("carry_out R:", out)
        self.assertIn("↔ paper:Q01 (Q:paper/Q01_problems.tex:3)", out)

    def test_track_q_alone_skips_the_r_check(self):
        self.put(R_EX, "module R01_Hello {\n  lemma ShiftTwice(y: nat) {}\n}\n")
        rc, out, err = self.avoid("--track", "Q")
        self.assertEqual(rc, 0, (out, err))


class Items(Fixture):
    def test_a_planned_modules_partial_items_are_tolerated(self):
        self.put("slots/Q01.slots", "P10dv = ???\n")      # a slot whose item is not there yet
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))

    def test_an_armed_modules_broken_items_exit_2(self):
        text = (self.root / "MODULES.toml").read_text(encoding="utf-8")
        text = text.replace('id = "Q01"\nlegacy_id = ""\ntrack = "Q"\nstatus = "planned"',
                            'id = "Q01"\nlegacy_id = ""\ntrack = "Q"\nstatus = "authoring"', 1)
        (self.root / "MODULES.toml").write_text(text, encoding="utf-8")
        self.put("slots/Q01.slots", "P10dv = ???\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 2, (out, err))
        self.assertIn("Q01: its item blocks do not parse (slots/Q01.slots:1: slot P10dv names no "
                      "verdict item of Q01", err)


class Waivers(Fixture):
    HIT = "module R01_Hello {\n  lemma ShiftTwice(y: nat) ensures y == y {}\n}\n"

    def test_a_name_row_waives_its_hit(self):
        self.put(R_EX, self.HIT)
        self.waivers(("N1", "adopted", "shift_twice", "hole:Q01.*", "Q→R", "why", "none"))
        rc, out, err = self.avoid("--json")
        self.assertEqual(rc, 0, (out, err))
        d = json.loads(out)
        self.assertEqual([(h["key"], h["waiver"]) for h in d["hits"]], [("shift_twice", "N1")])

    def test_a_row_in_the_wrong_direction_waives_nothing(self):
        self.put(R_EX, self.HIT)
        self.waivers(("N1", "adopted", "shift_twice", "hole:Q01.*", "R→Q", "why", "none"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("shift_twice R:", out)

    def test_a_row_that_waives_no_hit_is_stale(self):
        self.put(R_EX, "module R01_Hello {\n  lemma Other() {}\n}\n")
        self.waivers(("N1", "adopted", "shift_twice", "hole:Q01.*", "Q→R", "why", "none"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("shift_twice scripts/avoid.waivers.tsv:3 ↔ hole:Q01.*   "
                      "[stale waiver N1: it waives no hit]", out)

    def test_a_row_whose_target_track_has_no_declarations_is_idle(self):
        self.waivers(("N1", "adopted", "shift_twice", "hole:Q01.*", "Q→R", "why", "none"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("1 name waiver(s) idle (no declarations on their target track: N1)", out)

    def test_genre_rows_are_listed_and_a_provisional_one_is_named(self):
        self.waivers(("W7", "adopted", "-", "Q13, Q16 → R06", "Q→R", "genre", "cost"),
                     ("W19", "provisional", "-", "Q17.H2v → R11", "Q→R", "genre", "cost"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("2 genre waivers listed (shape overlaps, not name-checked)", out)
        self.assertIn("provisional: W19", out)

    def test_malformed_rows_exit_2(self):
        for rows, msg in (
                ([("N1", "adopted", "x", "y", "Q→R", "why")], "6 tab-separated fields, 7 expected"),
                ([("N1", "maybe", "x", "y", "Q→R", "why", "c")], "state must be one of"),
                ([("N1", "adopted", "NotAKey", "y", "Q→R", "why", "c")], "is not a normalized key"),
                ([("N1", "adopted", "x", "y", "Q=>R", "why", "c")], "direction must be one of"),
                ([("N1", "adopted", "-", "y", "Q→R", "why", "c")], "an N<n> id names a name-only"),
                ([("W1", "adopted", "-", "y", "Q→R", "g", "c"), ("W1", "adopted", "-", "z", "Q→R",
                                                                 "g", "c")], "a second genre row")):
            with self.subTest(msg=msg):
                self.waivers(*rows)
                rc, out, err = self.avoid()
                self.assertEqual(rc, 2, (out, err))
                self.assertIn(msg, err)

    def test_a_missing_header_is_malformed(self):
        (self.inputs / "avoid.waivers.tsv").write_text("N1\tadopted\tx\ty\tQ→R\tw\tc\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 2, (out, err))
        self.assertIn("the header must be the tab-separated columns", err)


class Curated(Fixture):
    def test_a_curated_name_and_type(self):
        self.curated(("Tree", "type", "R", "Lean R"), ("eval", "name", "R", "Lean R"))
        self.put(R_EX, "module R01_Hello {\n  function TreeSize(): nat { 0 }\n"
                       "  function Eval(): nat { 0 }\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"tree_size R:{R_EX}:2 ↔ curated:Tree (scripts/avoid.curated:2, Lean R)",
                      out)
        self.assertIn(f"eval R:{R_EX}:3 ↔ curated:eval", out)

    def test_a_curated_name_applies_only_to_its_track(self):
        self.curated(("ShiftTwice", "name", "R", "Lean R"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))

    def test_a_never_token_anywhere_in_a_file(self):
        self.curated(("LeanLearn0", "never", "QR", "the Lean namespace"))
        self.put(R_EX, "module R01_Hello {\n  import LeanLearn0\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"lean_learn_0 R:{R_EX}:2 ↔ curated:LeanLearn0", out)

    def test_a_bad_kind_exits_2(self):
        self.curated(("Tree", "shape", "R", "x"))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 2, (out, err))
        self.assertIn("kind must be one of name, type, never", err)


class Owners(Fixture):
    def test_an_owned_artifact_word_in_the_other_track(self):
        self.put(R_EX, "module R01_Hello {\n  function LimbCount(): nat { 0 }\n}\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"limb_count R:{R_EX}:2 ↔ artifact:Q:limb", out)

    def test_an_owner_tag_token_in_the_other_tracks_prediction(self):
        self.put(Q_EX, Q_FILE.replace("}\n", "  // item: Q01.P1dv S1 verdict\n"
                                            "  method Midpoint(a: nat) returns (m: nat) { m := a; }\n}\n"))
        self.put("slots/Q01.slots", "P1dv = ???\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"midpoint Q:{Q_EX}:13 ↔ owner:R:midpoint-overflow", out)

    def test_the_other_half_of_the_corpus(self):
        self.put("harness/q/fvh_q/q06_stats.py",
                 'from fvh import corpus\n\ndef go():\n    return corpus.load_half("dafny", "R")\n')
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("half_r Q:harness/q/fvh_q/q06_stats.py:4 ↔ corpus:R", out)

    def test_a_tag_home_that_is_not_the_owners_item_is_malformed(self):
        (self.inputs / "avoid" / "owners.toml").write_text(OWNERS.replace('"R01.P1dv"', '"Q01.P1dv"'))
        rc, out, err = self.avoid()
        self.assertEqual(rc, 2, (out, err))
        self.assertIn("is not an item id of the owner track R", err)


class SelfCheck(Fixture):
    BANK = ".claude/skills/instructor/banks/Q01.md"

    def test_a_parallel_problem_reposing_an_exercise_hole(self):
        self.put(self.BANK, "# Q01 bank\n\n## Parallel problems\n\n### PP1\n\n```dafny\n"
                            "lemma ShiftTwice(n: nat)\n```\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 1, (out, err))
        self.assertIn(f"shift_twice Q:{self.BANK}:8 ↔ self:Q01 (Q:{Q_EX}:3)   [self]", out)

    def test_questions_outside_the_parallel_problems_are_not_read(self):
        self.put(self.BANK, "# Q01 bank\n\n## Questions\n\n```dafny\nlemma ShiftTwice(n: nat)\n```\n")
        rc, out, err = self.avoid()
        self.assertEqual(rc, 0, (out, err))


class ExtraR(Fixture):
    def test_extra_r_files_are_r_declarations(self):
        spike = self.base / "spike"
        spike.mkdir()
        (spike / "RG_A1_Re.dfy").write_text("module RG_A1_Re {\n  datatype Re = Shift_Twice | Eps\n}\n")
        (spike / "tools").mkdir()
        (spike / "tools" / "x.dfy").write_text("lemma PadTo() {}\n")
        rc, out, err = self.avoid("--extra-r", str(spike))
        self.assertEqual(rc, 1, (out, err))
        self.assertIn("shift_twice R:", out)
        self.assertIn("↔ hole:Q01.H1d", out)
        self.assertNotIn("pad_to", out)
        self.assertIn("--extra-r: 1 path(s)", out)

    def test_a_missing_extra_path_is_a_usage_error(self):
        rc, out, err = self.avoid("--extra-r", str(self.base / "nope"))
        self.assertEqual(rc, 3, (out, err))


class Units(unittest.TestCase):
    def test_keys(self):
        for name, key in (("NodeCount", "node_count"), ("node_count", "node_count"),
                          ("lemma_node_count", "node_count"), ("LemmaNodeCount", "node_count"),
                          ("proof_sum", "sum"), ("NodeCountLemma", "node_count"),
                          ("RG_A1b_Facts", "facts"), ("QG_L4_BigNat", "big_nat"),
                          ("Q05_Frames", "frames"), ("Seq.ToNat", "to_nat"), ("vstd::seq::len", "len"),
                          ("from_u64", "from_u_64"), ("FromU64", "from_u_64"),
                          ("XMLParser", "xml_parser"), ("Valid?", "valid"), ("lemma", "lemma")):
            with self.subTest(name=name):
                self.assertEqual(A.key_of(name), key)

    def test_declaration_extractors(self):
        d = A.dafny_names("module M {\n  datatype T<X> = A(x: X) | B {\n  predicate P() { true } }\n"
                          "  ghost function {:opaque} F(): nat\n  // lemma Hidden()\n"
                          "  method M2() { var s := \"lemma Str()\"; }\n}\n")
        self.assertEqual([n for n, _ in d], ["T", "A", "B", "P", "F", "M2"])
        v = A.verus_names("verus! {\npub enum E { A, B(u8), C { x: u8 } }\n"
                          "pub open spec fn f(g: spec_fn(int) -> int) -> int { 0 }\n"
                          "struct S;\ntrait Tr { fn m(&self); }\n}\n")
        self.assertEqual([n for n, _ in v], ["E", "A", "B", "C", "f", "S", "Tr", "m"])
        self.assertEqual([n for n, _ in A.python_names("class K:\n    def m(self): pass\n")],
                         ["K", "m"])

    def test_fences_banks_and_tex(self):
        md = "x\n```dafny\nlemma L()\n```\n```mermaid\nfn no()\n```\n```rust\nfn r()\n```\n"
        self.assertEqual([(lang, ln) for lang, ln, _ in A.fences(md)], [("d", 3), ("v", 9)])
        bank = "# b\n## Questions\nq\n## Parallel problems\n### PP1\n## Notes\n"
        self.assertEqual(A.bank_pp_range(bank), (4, 5))
        tex = "\\begin{verbatim}\nlemma V()\n\\end{verbatim}"
        self.assertEqual([lang for lang, _, _ in A.tex_code(tex)], ["d", "v"])

    def test_reference_paths_are_never_read(self):
        for rel in ("Solutions/plans/x.md", "paper/solutions/Q01.tex",
                    "tests/instructor/leak_patterns/Q01.txt", "Challenges/Q19/Hidden/x"):
            with self.subTest(rel=rel), self.assertRaises(A.Malformed):
                A.read(C.ROOT, rel)


class Committed(unittest.TestCase):
    def test_the_committed_tree_passes_with_its_inputs(self):
        p = subprocess.run(["bash", str(AVOID)], capture_output=True, text=True, timeout=300)
        self.assertEqual(p.returncode, 0, (p.stdout, p.stderr))
        self.assertTrue(p.stdout.startswith("avoid.sh: OK: tracks Q+R;"), p.stdout)

    def test_usage_errors_exit_3(self):
        for args in (["--track", "S"], ["--bogus"]):
            with self.subTest(args=args):
                p = subprocess.run(["bash", str(AVOID), *args], capture_output=True, text=True)
                self.assertEqual(p.returncode, 3, (p.stdout, p.stderr))

    def test_ci_static_runs_it_on_the_course_root(self):
        text = (C.ROOT / "scripts" / "ci.sh").read_text(encoding="utf-8")
        self.assertIn('step "avoid.sh" bash "$SCRIPTS/avoid.sh" --root "$ROOT"', text)
        self.assertNotIn("avoid.sh is not built yet", text)


if __name__ == "__main__":
    unittest.main()
