"""Tool-free tests for the practice tiers' tool requests (QPLAN §30 Q52, Q62,
Q63, Q65, Q66; PLAN §8 R11, R15; R05.P3dv):

  * Q52  a Dafny function or predicate shipped with a placeholder body is an
         open body of the freeze pin, taken from its twin (specfreeze --pin,
         --check; reference_lint compares it by its header);
  * Q62  a Dafny module marked `// specfreeze: frozen-imports` keeps its
         import list (specfreeze --pin/--check/--against, reference_lint);
  * Q63  the lab gate's lever check (dvl.levers, specfreeze --lab);
  * Q65  dvl.verus.empty_body's qualified symbols for impl methods, the
         `{ arbitrary() }` body of a value-returning proof fn and the E0
         variants that keep `let tracked`; firsttry's per-method gate of a
         trait-impl item and its named `triv:` bodies;
  * Q66  a Dafny empty-body run that ends out of resources counts as failing;
  * R05.P3dv  vcheck --json --measures: `resource_count` and `wall_s` (learner
         loop only).

Nothing here runs Dafny or Verus: the verifier calls are mocked or never
reached. The real runs are in test_practice_tools_tool.py.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_practice_tools_static.py'
"""

import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
firsttry = C.load_script("firsttry")
specfreeze = C.load_script("specfreeze")
D, V, vs, common = core.D, core.V, core.V.vs, core.common
from dvl import levers as LEV  # noqa: E402

FX = C.ROOT / "tests" / "wrappers" / "fixtures"
REFERENCE = FX / "tools" / "reference"
CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"

ANSWER = ("\nmodule Q04_Answer {\n"
          "  // specfreeze: frozen-imports\n"
          "  ghost predicate Pre(x: int)\n"
          "    requires x >= 0\n"
          "  {\n"
          "    true\n"
          "  }\n"
          "}\n")
TWIN_ANSWER = ANSWER.replace("    true\n", "    x > 0 && x < 10\n")


class RootCase(unittest.TestCase):
    def setUp(self):
        self.root = C.build_root()

    def tearDown(self):
        C.remove_root(self.root)

    def rep(self, rel, old, new):
        C.replace_in(self.root / rel, old, new)

    def tool(self, *args, env=None):
        return C.tool(*args, root=self.root, env=env)


# =====================================================================================
# Q52 and Q62: the freeze pin's placeholder bodies and frozen import lists
# =====================================================================================

class DafnyImports(unittest.TestCase):
    TEXT = ("module A { const x := 1 }\n"
            "module B {\n  import opened A\n  import Z = A\n}\n"
            "module F {\n  // specfreeze: frozen-imports\n  const y := 2\n"
            "  module Inner {\n    import A\n  }\n}\n"
            "module G {\n  module H {\n    // specfreeze: frozen-imports\n  }\n}\n")

    def test_imports_by_module(self):
        src = D.parse_source(self.TEXT)
        self.assertEqual(D.module_imports(src)["B"], ["import opened A", "import Z = A"])
        self.assertEqual(D.module_imports(src)["A"], [])
        self.assertEqual(D.subtree_imports(src, "F"), ["Inner: import A"])
        self.assertEqual(D.subtree_imports(src, "B"), [": import Z = A", ": import opened A"])
        self.assertIsNone(D.subtree_imports(src, "Nope"))
        # the innermost module holding the marker line is the frozen one
        self.assertEqual(sorted(D.frozen_import_modules(src)), ["F", "G.H"])
        # the parser's older import table is unchanged
        self.assertEqual([n for _, n in src.imports], ["A", "A", "A"])


class FreezePin(RootCase):
    def twin(self, text):
        t = self.root / "Solutions" / CORE
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(text)

    def pin(self):
        rc, out, err = self.tool("specfreeze", "--pin", "Q04", env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        data = tomllib.loads((self.root / "expected" / "Q04.freeze").read_text())
        return out, {f["path"]: f for f in data["file"]}

    def check(self):
        rc, out, err = self.tool("specfreeze", "--check", "Q04")
        return rc, out + err

    def test_placeholder_body_is_open_from_its_twin(self):
        """Q52: a placeholder body the twin replaces is pinned without it; its
        header stays frozen; a body the twin does not change stays frozen."""
        with open(self.root / CORE, "a") as f:
            f.write(ANSWER)
        self.twin((self.root / CORE).read_text().replace(ANSWER, TWIN_ANSWER))
        _, files = self.pin()
        self.assertIn("Q04_Answer.Pre", files[CORE]["open_bodies"])
        self.assertNotIn("Q04_ProofCraft.Sum", files[CORE]["open_bodies"])
        self.assertEqual(self.check()[0], 0)
        self.rep(CORE, "    true\n", "    x > 0 && x < 10\n")        # the answer
        rc, out = self.check()
        self.assertEqual(rc, 0, out)
        self.rep(CORE, "    requires x >= 0\n", "    requires x >= 1\n")  # the header is frozen
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("freeze-changed — Q04_Answer.Pre", out)
        self.rep(CORE, "    requires x >= 1\n", "    requires x >= 0\n")
        # a given function's body (the twin keeps it) is still part of its statement
        self.rep(CORE, "if n == 0 then 0 else n + Sum(n - 1)", "if n == 0 then 0 else Sum(n - 1)")
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("freeze-changed — Q04_ProofCraft.Sum", out)

    def test_no_twin_no_placeholder(self):
        with open(self.root / CORE, "a") as f:
            f.write(ANSWER)
        _, files = self.pin()
        self.assertNotIn("Q04_Answer.Pre", files[CORE]["open_bodies"])
        self.rep(CORE, "    true\n", "    x > 0\n")
        self.assertEqual(self.check()[0], 1)

    def test_frozen_imports(self):
        """Q62: the marked module's import list (its nested modules included)
        is part of the pin; other modules import freely."""
        with open(self.root / CORE, "a") as f:
            f.write(ANSWER)
        out, files = self.pin()
        self.assertIn("frozen import lists (QPLAN §30 Q62)", out)
        self.assertEqual(files[CORE]["frozen_imports"], {"Q04_Answer": []})
        others = [r for r, f in files.items() if "frozen_imports" in f]
        self.assertEqual(others, [CORE])
        self.assertEqual(self.check()[0], 0)
        text = (self.root / CORE).read_text()
        line = text.split("\n").index("module Q04_Answer {") + 1
        for old, new in (("  // specfreeze: frozen-imports\n",
                          "  // specfreeze: frozen-imports\n  import opened Q04_ProofCraft\n"),
                         ("  ghost predicate Pre",
                          "  module Side {\n    import opened Q04_ProofCraft\n  }\n"
                          "  ghost predicate Pre")):
            self.rep(CORE, old, new)
            rc, out = self.check()
            self.assertEqual(rc, 1, (new, out))
            self.assertIn(f"Q04_ProofCraft.dfy:{line}: freeze-imports-changed — module Q04_Answer",
                          out)
            (self.root / CORE).write_text(text)
        # the marker line itself is not what is frozen: deleting it changes nothing
        self.rep(CORE, "  // specfreeze: frozen-imports\n", "")
        self.assertEqual(self.check()[0], 0)
        # an import added to an unmarked module is no finding
        self.rep(CORE, "  import opened QG_L2_BigNat\n",
                 "  import opened QG_L2_BigNat\n  import L1 = QG_L1_BigNat\n")
        self.assertEqual(self.check()[0], 0)
        # the module gone
        (self.root / CORE).write_text(text.replace(ANSWER, ""))
        rc, out = self.check()
        self.assertEqual(rc, 1)
        self.assertIn("freeze-missing — module Q04_Answer", out)

    def test_pins_without_markers_or_placeholders_are_unchanged(self):
        self.pin()
        before = (self.root / "expected" / "Q04.freeze").read_text()
        self.assertNotIn("frozen_imports", before)
        self.pin()
        self.assertEqual((self.root / "expected" / "Q04.freeze").read_text(), before)

    def test_against_applies_the_frozen_files_markers(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q62-"))
        try:
            frozen = tmp / "frozen.dfy"
            frozen.write_text("module P { function F(x: int): int { x } }" + ANSWER)
            ok = tmp / "ok.dfy"
            ok.write_text(frozen.read_text())
            bad = tmp / "bad.dfy"
            bad.write_text(frozen.read_text().replace(
                "  // specfreeze: frozen-imports\n", "  import opened P\n"))
            rc, out, err = C.tool("specfreeze", "--against", frozen, ok)
            self.assertEqual(rc, 0, out + err)
            rc, out, err = C.tool("specfreeze", "--against", frozen, bad)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("freeze-imports-changed — module Q04_Answer", out)
        finally:
            shutil.rmtree(tmp)


class ReferenceLintPlaceholders(RootCase):
    def setUp(self):
        super().setUp()
        shutil.copytree(REFERENCE, self.root / "Solutions")

    def lint(self):
        return self.tool("reference_lint.py", env={"CI": "true"})

    def test_placeholder_body_and_frozen_imports(self):
        with open(self.root / CORE, "a") as f:
            f.write(ANSWER)
        twin = self.root / "Solutions" / CORE
        with open(twin, "a") as f:
            f.write(TWIN_ANSWER)
        rc, out, err = self.lint()
        self.assertEqual(rc, 0, out + err)                 # Q52: no statement-differs
        text = twin.read_text()
        twin.write_text(text.replace("    requires x >= 0\n", "    requires x >= 1\n"))
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("statement-differs", out)
        twin.write_text(text.replace("  // specfreeze: frozen-imports\n",
                                     "  // specfreeze: frozen-imports\n"
                                     "  import opened Q04_ProofCraft\n"))
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        line = twin.read_text().split("\n").index("module Q04_Answer {") + 1
        self.assertIn(f"Solutions/{CORE}:{line}: imports-differ", out)


class PlaceholderLint(unittest.TestCase):
    def test_a_placeholder_bodied_predicate_is_no_learner_finding(self):
        """Q52's lint note: a placeholder body is a body; a bodyless predicate
        without an `ensures` stays an uncounted hole (bodyless-silent)."""
        found = D.lint_source("module M {\n  ghost predicate P(x: int) { true }\n}\n", "m.dfy",
                              "learner")
        self.assertEqual(found, [])
        found = D.lint_source("module M {\n  ghost predicate P(x: int)\n}\n", "m.dfy", "learner")
        self.assertEqual([f.kind for f in found], ["bodyless-silent"])


# =====================================================================================
# Q63: the lab gate's lever check
# =====================================================================================

LAB_D, LAB_V = FX / "dafny" / "lab", FX / "verus" / "lab"


class Levers(unittest.TestCase):
    def test_dafny_table(self):
        got = LEV.levers(LAB_D / "task.dfy")
        self.assertEqual([(s, lv) for s, lv, _ in got],
                         [("module LabTask", "{:disableNonlinearArithmetic}"),
                          ("LabTask.CountIsN", "{:induction false}")])

    def test_dafny_pairs(self):
        self.assertEqual(LEV.lever_findings(LAB_D / "task.dfy", LAB_D / "kept.dfy"), [])
        found = LEV.lever_findings(LAB_D / "task.dfy", LAB_D / "levered.dfy")
        self.assertEqual(sorted((f.kind, f.line) for f in found),
                         [("lab-lever-added", 7), ("lab-lever-removed", 0)])
        self.assertTrue(any("{:vcs_split_on_every_assert} on LabTask.CountIsN" in f.message
                            for f in found))
        self.assertTrue(any("{:induction false} on LabTask.CountIsN" in f.message
                            for f in found))

    def test_dafny_kinds_and_scopes(self):
        task = "module M {\n  lemma L(n: nat) ensures n >= 0 {}\n}\n"
        cases = {
            "module M {\n  lemma {:induction} L(n: nat) ensures n >= 0 {}\n}\n":
                "{:induction}",
            "module M {\n  @Induction(n) lemma L(n: nat) ensures n >= 0 {}\n}\n":
                "@Induction(n)",
            "module M {\n  lemma L(n: nat) ensures n >= 0 { assert {:split_here} true; }\n}\n":
                "{:split_here}",
            "module M {\n  lemma {:fuel F, 2} L(n: nat) ensures n >= 0 {}\n}\n":
                "{:fuel F , 2}",
            "module M {\n  lemma {:isolate_assertions} L(n: nat) ensures n >= 0 {}\n}\n":
                "{:isolate_assertions}",
            "module {:disableNonlinearArithmetic} M {\n  lemma L(n: nat) ensures n >= 0 {}\n}\n":
                "{:disableNonlinearArithmetic}",
            "module M {\n  lemma {:resource_limit 9} L(n: nat) ensures n >= 0 {}\n}\n":
                "{:resource_limit 9}",
            "module M {\n  lemma {:options \"--x\"} L(n: nat) ensures n >= 0 {}\n}\n":
                "{:options \"--x\"}",
            "module M {\n  lemma L(n: nat) ensures n >= 0 {}\n"
            "  lemma {:vcs_split_on_every_assert} Helper() {}\n}\n":
                "{:vcs_split_on_every_assert}",
        }
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q63-"))
        try:
            (tmp / "t.dfy").write_text(task)
            for text, lever in cases.items():
                (tmp / "d.dfy").write_text(text)
                found = LEV.lever_findings(tmp / "t.dfy", tmp / "d.dfy")
                self.assertEqual([f.kind for f in found], ["lab-lever-added"], text)
                self.assertTrue(found[0].message.startswith(lever + " on "), found[0].message)
            # triggers, opacity and plain proof text are no levers
            (tmp / "d.dfy").write_text("module M {\n  opaque function F(): int { 1 }\n"
                                       "  lemma L(n: nat) ensures n >= 0 {\n"
                                       "    assert forall k: nat {:trigger k + 1} :: k + 1 > 0;\n"
                                       "    reveal F();\n  }\n}\n")
            self.assertEqual(LEV.lever_findings(tmp / "t.dfy", tmp / "d.dfy"), [])
            # a lever moved to another declaration is one removed and one added
            (tmp / "t2.dfy").write_text("module M {\n  lemma {:induction false} A() {}\n"
                                        "  lemma B() {}\n}\n")
            (tmp / "d2.dfy").write_text("module M {\n  lemma A() {}\n"
                                        "  lemma {:induction false} B() {}\n}\n")
            self.assertEqual(sorted(f.kind for f in LEV.lever_findings(tmp / "t2.dfy",
                                                                       tmp / "d2.dfy")),
                             ["lab-lever-added", "lab-lever-removed"])
            # a removed trust escape strengthens the delivery: no finding
            (tmp / "t3.dfy").write_text("module M {\n  lemma {:axiom} A() ensures true\n}\n")
            (tmp / "d3.dfy").write_text("module M {\n  lemma A() ensures true {}\n}\n")
            self.assertEqual(LEV.lever_findings(tmp / "t3.dfy", tmp / "d3.dfy"), [])
        finally:
            shutil.rmtree(tmp)

    def test_verus(self):
        found = LEV.lever_findings(LAB_V / "task.rs", LAB_V / "levered.rs")
        self.assertEqual([(f.kind, f.line) for f in found], [("lab-lever-added", 13)])
        self.assertIn("#[verifier::spinoff_prover] on fn count_is_n", found[0].message)
        # the labelled assume's proof_note leaving is no finding (task.rs ships one)
        self.assertEqual(LEV.lever_findings(LAB_V / "task.rs", LAB_V / "task.rs"), [])
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q63v-"))
        try:
            base = ("use vstd::prelude::*;\nverus! {\n"
                    "#[verifier::external_body]\npub fn f(x: u64) -> (r: u64) ensures r == x "
                    "{ unimplemented!() }\n}\n")
            (tmp / "t.rs").write_text(base)
            (tmp / "ok.rs").write_text(base.replace("#[verifier::external_body]\n", "").replace(
                "{ unimplemented!() }", "{ x }"))
            self.assertEqual(LEV.lever_findings(tmp / "t.rs", tmp / "ok.rs"), [])
            (tmp / "crate.rs").write_text("#![verifier::loop_isolation(false)]\n"
                                          + (tmp / "ok.rs").read_text().replace(
                                              "{ x }", "{ assert(forall|i: u64| #[trigger] "
                                                       "(i + 0) == i); x }"))
            found = LEV.lever_findings(tmp / "t.rs", tmp / "crate.rs")
            self.assertEqual([(f.kind, f.line) for f in found], [("lab-lever-added", 1)])
            self.assertIn("#![verifier::loop_isolation(false)] on (file)", found[0].message)
        finally:
            shutil.rmtree(tmp)

    def test_directories(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q63d-"))
        try:
            for side in ("task", "del"):
                (tmp / side / "src").mkdir(parents=True)
                (tmp / side / "Cargo.toml").write_text("[package]\nname = \"x\"\n")
                shutil.copy(LAB_V / "task.rs", tmp / side / "src" / "lib.rs")
            self.assertEqual(LEV.lever_findings(tmp / "task", tmp / "del"), [])
            shutil.copy(LAB_V / "levered.rs", tmp / "del" / "src" / "lib.rs")
            (tmp / "del" / "src" / "extra.rs").write_text(
                "verus! {\n#[verifier::spinoff_prover]\nproof fn p() {}\n}\n")
            (tmp / "del" / "Cargo.toml").write_text("[package]\nname = \"y\"\n")
            kinds = sorted(f.kind for f in LEV.lever_findings(tmp / "task", tmp / "del"))
            self.assertEqual(kinds, ["lab-file-added", "lab-lever-added", "lab-project-changed"])
        finally:
            shutil.rmtree(tmp)

    def test_refusals(self):
        with self.assertRaises(LEV.LeverError):
            LEV.lever_findings(LAB_D / "task.dfy", LAB_V / "task.rs")
        with self.assertRaises(LEV.LeverError):
            LEV.lever_findings(LAB_D / "task.dfy", LAB_D)
        with self.assertRaises(LEV.LeverError):
            LEV.lever_findings(LAB_D / "nope.dfy", LAB_D / "kept.dfy")

    def test_specfreeze_lab(self):
        rc, out, err = C.tool("specfreeze", "--lab", LAB_D / "task.dfy", LAB_D / "kept.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("0 finding(s) (lab: statements and levers against the task form)", out)
        rc, out, err = C.tool("specfreeze", "--lab", LAB_D / "task.dfy", LAB_D / "levered.dfy",
                              "--json")
        self.assertEqual(rc, 1, out + err)
        doc = json.loads(out)
        self.assertEqual(doc["exit_code"], 1)
        self.assertEqual(sorted(f["kind"] for f in doc["findings"]),
                         ["lab-lever-added", "lab-lever-removed"])
        # the statement freeze runs too: a weakened ensures is freeze-changed
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q63s-"))
        try:
            weak = tmp / "weak.dfy"
            weak.write_text((LAB_D / "kept.dfy").read_text().replace(
                "ensures Count(n) == n", "ensures Count(n) >= 0"))
            rc, out, err = C.tool("specfreeze", "--lab", LAB_D / "task.dfy", weak)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("freeze-changed", out)
        finally:
            shutil.rmtree(tmp)
        rc, out, err = C.tool("specfreeze", "--lab", LAB_D / "task.dfy", LAB_V / "task.rs")
        self.assertEqual(rc, 2, out + err)

    def test_vcheck_lab_task_usage(self):
        rc, out, err = C.tool("vcheck", "--lab-task", LAB_D / "task.dfy", LAB_D / "kept.dfy")
        self.assertEqual(rc, 2, out + err)                  # the lab gate goes with --gate
        self.assertIn("vcheck --gate --lab-task", err)
        rc, out, err = C.tool("vcheck", "--gate", "--lab-task", LAB_D / "missing.dfy",
                              LAB_D / "kept.dfy")
        self.assertEqual(rc, 3, out + err)

    def test_lab_gate_on_a_result(self):
        res = common.Result("dafny", str(LAB_D / "levered.dfy"), 0, "verified", "verify", 2)
        core.lab_gate(res, LAB_D / "task.dfy", LAB_D / "levered.dfy")
        self.assertEqual((res.verdict, res.exit_code), ("failed", 0))
        self.assertEqual(len(res.findings), 2)
        res = common.Result("dafny", str(LAB_D / "kept.dfy"), 0, "verified", "verify", 2)
        core.lab_gate(res, LAB_D / "task.dfy", LAB_D / "kept.dfy")
        self.assertEqual((res.verdict, res.findings), ("verified", []))
        res = common.Result("dafny", "x", 0, "verified", "verify", 2)
        core.lab_gate(res, LAB_D / "task.dfy", LAB_V / "task.rs")
        self.assertEqual((res.verdict, [f.kind for f in res.findings]),
                         ("failed", ["lab-levers-unchecked"]))

    # The user's decision D24: the lab gate also applies vaudit's assumption rules to a
    # delivery still verified after the lever check (`audit`, which the CLI always passes).
    def _gate(self, lang, task, delivery, audit):
        res = common.Result(lang, str(delivery), 0, "verified", "verify", 2)
        return core.lab_gate(res, task, delivery, audit=audit)

    def test_lab_gate_audit_clean_passes(self):
        for lang, lab, ext in (("dafny", LAB_D, "dfy"), ("verus", LAB_V, "rs")):
            res = self._gate(lang, lab / f"task.{ext}", lab / f"kept.{ext}", lambda: [])
            self.assertEqual((res.verdict, res.findings, res.exit_code), ("verified", [], 0),
                             lang)

    def test_lab_gate_audit_finding_fails(self):
        for lang, lab, ext, kind in (("dafny", LAB_D, "dfy", "audit-assume-axiom"),
                                     ("verus", LAB_V, "rs", "hole-external-body")):
            d = lab / f"kept.{ext}"
            res = self._gate(lang, lab / f"task.{ext}", d,
                             lambda: [common.Finding(str(d), 7, kind, "an assumption")])
            self.assertEqual((res.verdict, res.exit_code), ("failed", 0), lang)
            self.assertEqual([(f.kind, f.line) for f in res.findings], [("lab-audit", 7)])
            self.assertIn(f"reports {kind}: an assumption", res.findings[0].message)

    def test_lab_gate_audit_after_the_lever_check(self):
        called = []
        res = self._gate("dafny", LAB_D / "task.dfy", LAB_D / "levered.dfy",
                         lambda: called.append(1) or [])
        self.assertEqual(res.verdict, "failed")
        self.assertEqual(called, [])            # a lever failure is final: no audit run
        res = common.Result("dafny", "x", 0, "failed", "verify", 1)
        core.lab_gate(res, LAB_D / "task.dfy", LAB_D / "kept.dfy",
                      audit=lambda: called.append(1) or [])
        self.assertEqual((res.verdict, called), ("failed", []))

    def test_lab_gate_audit_that_cannot_run_fails(self):
        def boom():
            raise common.ToolchainError("the pinned install is missing")
        res = self._gate("dafny", LAB_D / "task.dfy", LAB_D / "kept.dfy", boom)
        self.assertEqual(res.verdict, "failed")
        self.assertEqual([f.kind for f in res.findings], ["lab-audit"])
        self.assertIn("audit-incomplete", res.findings[0].message)

    def test_lab_gate_audit_killed_is_no_verdict(self):
        d = LAB_V / "kept.rs"
        res = self._gate("verus", LAB_V / "task.rs", d, lambda: [common.Finding(
            str(d), 0, "audit-incomplete", "the --no-cheating run of k did not complete "
            "(killed(memory), stage verify); raw output in /x")])
        self.assertEqual((res.verdict, res.exit_code), ("killed(memory)", 137))
        d = LAB_D / "kept.dfy"
        res = self._gate("dafny", LAB_D / "task.dfy", d, lambda: [common.Finding(
            str(d), 0, "audit-error", "the audit did not run to completion (inconclusive); "
            "raw output: /x")])
        self.assertEqual((res.verdict, res.exit_code), ("inconclusive", 124))
        res = self._gate("dafny", LAB_D / "task.dfy", d, lambda: [common.Finding(
            str(d), 0, "audit-error", "the audit did not run to completion (exit 4); raw "
            "output: /x")])
        self.assertEqual((res.verdict, res.exit_code), ("failed", 0))

    def test_shipped_assumption_forms_pass_the_lever_check(self):
        # D24's fixtures: delivered unchanged, each keeps every shipped lever, so only the
        # assumption audit can refuse it (the tool tests run it)
        for task, lever in ((LAB_D / "axiom_task.dfy", "{:axiom}"),
                            (LAB_D / "axiom_lemma_task.dfy", "{:axiom}"),
                            (LAB_V / "external_task.rs", "#[verifier::external_body]")):
            self.assertIn(lever, [lv for _, lv, _ in LEV.levers(task)], task.name)
            self.assertEqual(LEV.lever_findings(task, task), [], task.name)

    def test_lab_audit_is_vaudits_audit(self):
        t = SimpleNamespace(lang="d", path=LAB_D / "kept.dfy")
        with mock.patch.object(core._vaudit(), "audit", return_value=["x"]) as au:
            self.assertEqual(core.lab_audit(t), ["x"])
        au.assert_called_once_with(t, "learner", None)


# =====================================================================================
# Q65: the Verus empty-body variants
# =====================================================================================

VFX = FX / "verus"


def fn_named(src, name):
    return next(it for it in src.walk() if it.kind == "fn" and it.name == name)


class VerusVariants(unittest.TestCase):
    def test_named_return_proof_fn_gets_arbitrary(self):
        text = (VFX / "eb_named.rs").read_text()
        src = vs.parse(text)
        it = fn_named(src, "witness_three")
        for mode in ("E0", "E0H", "E1", "E2", "EM"):
            v = V.eb_variant(text, src, it, mode)
            self.assertIn("{\n    arbitrary()\n}", v, mode)
            self.assertNotIn("reveal_with_fuel", v)
        self.assertIsNone(V.eb_variant(text, src, it, "NL"))     # a named return: no NL/BV

    def test_unit_and_tracked_returns_keep_the_empty_body(self):
        for ret, want in (("", "{\n}"), (" -> ()", "{\n}"), (" -> (tracked r: nat)", "{\n}"),
                          (" -> nat", "{\n    arbitrary()\n}")):
            text = ("use vstd::prelude::*;\nverus! {\nproof fn p()" + ret
                    + " {\n    assume(false);\n    arbitrary()\n}\n}\n")
            src = vs.parse(text)
            self.assertEqual(V._empty_proof_body(src, fn_named(src, "p")), want, ret)

    def test_e0_keeps_let_tracked(self):
        text = (VFX / "eb_tracked.rs").read_text()
        src = vs.parse(text)
        it = fn_named(src, "read_slot")
        for mode in ("E0", "E0H", "E1"):
            v = V.eb_variant(text, src, it, mode)
            self.assertIn("let tracked perm = perms.tracked_borrow(0);", v, mode)
            self.assertNotIn("reveal_with_fuel", v, mode)
            self.assertIn("*p.borrow(Tracked(perm))", v, mode)
        # ghost lets still go (QPLAN §6 Q9's fixture)
        gtext = (VFX / "eb_ghost.rs").read_text()
        gsrc = vs.parse(gtext)
        g = next(x for x in gsrc.walk() if x.kind == "fn" and x.mode == "exec" and x.body)
        self.assertNotIn("let ghost", V.eb_variant(gtext, gsrc, g, "E0"))

    def test_proof_spans_keep_tracked_only_on_request(self):
        text = ("verus! {\nfn f() {\n    let tracked t = x;\n    let ghost g = 1;\n"
                "    proof { let tracked u = y; }\n    g(Tracked(t));\n}\n}\n")
        src = vs.parse(text)
        it = fn_named(src, "f")
        cut = lambda keep: vs.apply_spans(text, vs.proof_spans(  # noqa: E731
            src, it.body[0] + 1, it.body[1], keep_tracked=keep))
        self.assertNotIn("let tracked t", cut(False))
        kept = cut(True)
        self.assertIn("let tracked t = x;", kept)
        self.assertNotIn("let ghost", kept)
        self.assertNotIn("let tracked u", kept)        # inside a stripped proof block

    def plan(self, rel):
        return SimpleNamespace(files=[(str(VFX / rel), "", None)])

    def test_qualified_symbols(self):
        plan = self.plan("eb_trait.rs")
        for sym, owner in (("A::three", "<A as Probe>"), ("<B as Probe>::three", "<B as Probe>"),
                           ("three_plain", "A")):
            found = V._find_item(None, plan, sym)
            self.assertIsNotNone(found, sym)
            self.assertEqual(found[3].owner, owner, sym)
        self.assertIsNone(V._find_item(None, plan, "three"))     # the trait and two impls
        self.assertIsNone(V._find_item(None, plan, "C::three"))
        self.assertEqual(V.owner_type("<A as Probe>"), "A")
        self.assertEqual(V.owner_type("Wrap<T>"), "Wrap")
        self.assertIsNone(V.owner_type(None))

    def test_verify_function_patterns(self):
        plan = self.plan("eb_trait.rs")
        src = vs.parse((VFX / "eb_trait.rs").read_text())
        a3 = next(it for it in src.walk() if it.kind == "fn" and it.owner == "<A as Probe>")
        plain = fn_named(src, "three_plain")
        self.assertEqual(V._verify_function_arg(plan, a3), "A::three")
        self.assertEqual(V._verify_function_arg(plan, plain), "*::three_plain")
        free = SimpleNamespace(owner=None, name="count3")
        self.assertEqual(V._verify_function_arg(plan, free), "count3")


TRAIT_ITEM = """use vstd::prelude::*;
verus! {
pub trait Acc: Sized {
    spec fn total(&self) -> nat;
    fn add(&mut self, x: u64);
    fn read(&self) -> (r: u64);
}
pub struct P { pub lo: u64 }
// item: Q98.H2v S9
impl Acc for P {
    open spec fn total(&self) -> nat {
        self.lo as nat
    }

    #[verifier::external_body]
    fn add(&mut self, x: u64) {
        unimplemented!()
    }

    #[verifier::external_body]
    fn read(&self) -> (r: u64) {
        unimplemented!()
    }

    fn given(&self) -> (r: u64) {
        0
    }
}
}
"""


DAFNY_CLASS_ITEM = """module M {
  // item: Q98.H1d S6
  class C {
    var v: nat
    ghost var G: nat

    ghost predicate Valid()
      reads this
    {
      true
    }

    constructor ()
      ensures Valid() && G == 0
    {
      assume false;  // HOLE: delete this line and implement
    }

    method Put(x: nat)
      requires Valid()
      modifies this
      ensures Valid() && G == x
    {
      assume false;  // HOLE: delete this line and implement
    }
  }
}
"""


class TraitImplItems(unittest.TestCase):
    def item(self, text):
        items, _ = firsttry.ci.parse_items("verus/q/x/src/lib.rs", text)
        return next(x for x in items if x["id"] == "Q98.H2v")

    def test_hole_methods(self):
        it = self.item(TRAIT_ITEM)
        self.assertEqual(firsttry.impl_hole_methods(TRAIT_ITEM, "verus/q/x/src/lib.rs", it),
                         [("<P as Acc>::add", "add"), ("<P as Acc>::read", "read")])
        # an inherent impl with two hole methods is gated per method too (Q14.H5v)
        inherent = TRAIT_ITEM.replace("impl Acc for P {", "impl P {")
        self.assertEqual(firsttry.impl_hole_methods(inherent, "verus/q/x/src/lib.rs",
                                                    self.item(inherent)),
                         [("P::add", "add"), ("P::read", "read")])
        # with one hole method its first fn's gate stands
        single = inherent.replace("    #[verifier::external_body]\n    fn read(&self) -> (r: u64) {\n"
                                  "        unimplemented!()\n", "    fn read(&self) -> (r: u64) {\n"
                                  "        0\n")
        self.assertEqual(firsttry.impl_hole_methods(single, "verus/q/x/src/lib.rs",
                                                    self.item(single)), [])

    def test_dafny_class_hole_methods(self):
        # DV5c (Q17.H1d): a Dafny block with several hole methods is gated per method;
        # its placeholder-bodied predicate is never one of them, and one hole method
        # keeps the first declaration's gate
        rel = "dafny/Q/Q98_X/std/Q98_X.dfy"
        text = DAFNY_CLASS_ITEM
        items, _ = firsttry.ci.parse_items(rel, text)
        it = next(x for x in items if x["id"] == "Q98.H1d")
        self.assertEqual(firsttry.dafny_hole_methods(text, rel, it),
                         [("M.C._ctor", "_ctor"), ("M.C.Put", "Put")])
        single = text.replace("      assume false;  // HOLE: delete this line and implement\n"
                              "    }\n  }", "      v := 0;\n    }\n  }")
        items, _ = firsttry.ci.parse_items(rel, single)
        it = next(x for x in items if x["id"] == "Q98.H1d")
        self.assertEqual(firsttry.dafny_hole_methods(single, rel, it), [])
        self.assertEqual(firsttry.dafny_hole_methods(text, "verus/q/x/src/lib.rs", it), [])

    def test_named_triv_bodies(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q65-"))
        try:
            rel = "verus/q/x/src/lib.rs"
            twin = tmp / "Solutions" / rel
            twin.parent.mkdir(parents=True)
            ctx = SimpleNamespace(root=tmp)
            twin.write_text(TRAIT_ITEM.replace(
                "impl Acc for P {",
                "// triv: read: { 0 }\n// triv: add: {\n// triv: }\nimpl Acc for P {"))
            it = self.item(twin.read_text())
            bodies, problem = firsttry.declared_triv_bodies(ctx, it, rel)
            self.assertIsNone(problem)
            self.assertEqual(bodies, {"read": "{ 0 }", "add": "{\n}"})
            self.assertIsNotNone(firsttry.declared_triv_body(ctx, it, rel)[1])
            twin.write_text(TRAIT_ITEM.replace("impl Acc for P {",
                                               "// triv: { BigNat { limbs: Vec::new() } }\n"
                                               "impl Acc for P {"))
            it = self.item(twin.read_text())
            self.assertEqual(firsttry.declared_triv_body(ctx, it, rel),
                             ("{ BigNat { limbs: Vec::new() } }", None))
            twin.write_text(TRAIT_ITEM.replace("impl Acc for P {",
                                               "// triv: read: 0\nimpl Acc for P {"))
            it = self.item(twin.read_text())
            self.assertIn("one `{ … }` block", firsttry.declared_triv_bodies(ctx, it, rel)[1])
        finally:
            shutil.rmtree(tmp)


# =====================================================================================
# Q66: an empty-body run that ends out of resources
# =====================================================================================

class DafnyOutOfResources(unittest.TestCase):
    def test_inconclusive_maxauto_counts_as_failing(self):
        def fake(cp, gate=False, symbol=None, seed=None, extra_flags=(), target=None, raw=None,
                 **kw):
            st = "inconclusive" if extra_flags else "failed"
            return common.Result("dafny", target, 4, "failed", "verify", None, [], [], [],
                                 {symbol: st}, str(raw), ["dafny"])
        with mock.patch.object(D.common, "toolchain"), \
                mock.patch.object(D, "_verify_program", side_effect=fake):
            res = D.empty_body(str(FX / "dafny" / "eb.dfy"), "Q09.H2d")
        self.assertEqual(res.verdict, "failed")
        self.assertEqual(res.per_symbol["maxauto"], "inconclusive")
        kinds = [f.kind for f in res.findings]
        self.assertNotIn("lever-needed", kinds)
        self.assertEqual(kinds, ["empty-body-inconclusive"])
        self.assertIn("counted as failing (QPLAN §30 Q66)", res.findings[0].message)

    def test_inconclusive_shipped_runs_count_as_failing(self):
        def fake(cp, gate=False, symbol=None, seed=None, extra_flags=(), target=None, raw=None,
                 **kw):
            st = "verified" if extra_flags else "inconclusive"
            return common.Result("dafny", target, 4, "failed", "verify", None, [], [], [],
                                 {symbol: st}, str(raw), ["dafny"])
        with mock.patch.object(D.common, "toolchain"), \
                mock.patch.object(D, "_verify_program", side_effect=fake):
            res = D.empty_body(str(FX / "dafny" / "eb.dfy"), "Q09.H1d")
        self.assertEqual(res.verdict, "failed")
        self.assertIn("lever-needed", [f.kind for f in res.findings])


# =====================================================================================
# R05.P3dv: vcheck --json's measurements
# =====================================================================================

class JsonMeasures(unittest.TestCase):
    def test_resource_total(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-r05-"))
        try:
            (tmp / "tasks.csv").write_text(
                "TestResult.DisplayName,TestResult.Outcome,TestResult.ResourceCount\n"
                "M.A (well-formedness),Passed,100\nM.A (correctness),Passed,250\n"
                "M.B (correctness),Passed,7\n")
            res = common.Result("dafny", "x", 0, "verified", "verify", 3, raw_dir=str(tmp))
            self.assertEqual(core.resource_total(res), 357)
            (tmp / "tasks.csv").unlink()
            self.assertIsNone(core.resource_total(res))
            job = tmp / "01-target"
            job.mkdir()
            doc = {"verification-results": {"verified": 2},
                   "times-ms": {"smt": {"smt-run-module-times": [
                       {"function-breakdown": [{"function": "c::f", "rlimit": 40},
                                               {"function": "c::g", "rlimit": 2}]}]}}}
            (job / "stdout.txt").write_text(json.dumps(doc))
            res = common.Result("verus", "x", 0, "verified", "verify", 2, raw_dir=str(tmp))
            self.assertEqual(core.resource_total(res), 42)
            (job / "stdout.txt").write_text(json.dumps({"verification-results": {}}))
            self.assertIsNone(core.resource_total(res))
            self.assertIsNone(core.resource_total(
                common.Result(core.PY.LANG, "x", 0, "verified", "verify", 1)))
        finally:
            shutil.rmtree(tmp)

    def test_result_json(self):
        res = common.Result("dafny", "x", 0, "verified", "verify", 3)
        plain = core.result_json(res)
        self.assertNotIn("resource_count", plain)
        self.assertNotIn("wall_s", plain)
        loop = core.result_json(res, measures={"resource_count": 9, "wall_s": 0.5})
        self.assertEqual((loop["resource_count"], loop["wall_s"]), (9, 0.5))
        self.assertEqual(set(loop) - set(plain), {"resource_count", "wall_s"})



class A1bLayerNames(unittest.TestCase):
    """Layer A1b (R06's band-1 facts, DELTAS Δ174): the wrappers' given-layer
    patterns accept its Dafny file and module and its Verus crate, as
    gen_units and check_course_map do."""

    def test_dafny_given_patterns(self):
        m = D.GIVEN_PATH.fullmatch("dafny/given/R/RG_A1b_Facts.dfy")
        self.assertEqual(m.groups(), ("R", "A1b"))
        self.assertEqual(D.GIVEN_PATH.fullmatch("dafny/given/R/RG_A1_Re.dfy").group(2), "A1")
        self.assertEqual(D.GIVEN_MODULE.fullmatch("RG_A1b_Facts").group(1), "A1b")
        self.assertIsNone(D.GIVEN_PATH.fullmatch("dafny/given/R/RG_A2b_X.dfy"))

    def test_verus_given_patterns(self):
        self.assertEqual(V.GIVEN_DIR.search("verus/given/rg_re_a1b/src/lib.rs").group(1),
                         "rg_re_a1b")
        self.assertIsNotNone(V.GIVEN_CRATE.fullmatch("rg_re_a1b"))
        self.assertIsNotNone(V.GIVEN_CRATE.fullmatch("rg_re_a1"))
        self.assertIsNone(V.GIVEN_CRATE.fullmatch("rg_re_a2b"))


if __name__ == "__main__":
    unittest.main()
