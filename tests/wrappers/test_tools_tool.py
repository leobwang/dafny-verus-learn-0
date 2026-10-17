"""Tool tests for the DV1b tools against the real pinned Dafny 4.11.0 and Verus
0.2026.09.27.3cf1832 (scripts/get_toolchain.sh): scripts/vcheck, scripts/vaudit,
scripts/specfreeze --against, scripts/firsttry.py (--check, --report, --exit,
--empty-body) and scripts/pins.py (learner mode, --update, --ci, --ref).

Every job runs through the dvl libraries, so it runs under the CLAUDE.md
§Resources memory cap (Dafny 8G, Verus 16G) one at a time unless
DVL_DAFNY_JOBS / DVL_VERUS_JOBS say otherwise. The suite fails, never skips,
without the pinned toolchains. Every expectation below was observed on a real
run of these fixtures (invented programs: the wrapper fixtures of the library
lanes, the synthetic armed Q04, and tests/wrappers/fixtures/tools/).

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_tools_tool.py'
"""

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

FX = "tests/wrappers/fixtures"
REFERENCE = C.ROOT / "tests" / "wrappers" / "fixtures" / "tools" / "reference"


class RootCase(unittest.TestCase):
    git = False

    def setUp(self):
        self.root = C.build_root(git=self.git)

    def tearDown(self):
        C.remove_root(self.root)

    def rep(self, rel, old, new):
        C.replace_in(self.root / rel, old, new)

    def run_(self, script, *args, env=None):
        return C.tool(script, *args, root=self.root, env=env)


# =====================================================================================
# vcheck
# =====================================================================================

class Vcheck(unittest.TestCase):
    def test_learner_loop_counts_holes(self):
        rc, out, err = C.tool("vcheck", f"{FX}/dafny/holes.dfy")
        self.assertEqual(rc, 0, out + err)
        lines = out.splitlines()
        self.assertEqual(lines[0], "vcheck: tests/wrappers/fixtures/dafny/holes.dfy [dafny, learner "
                                   "loop]: verified — 4 verified, 5 holes, 0 errors")
        self.assertIn("tests/wrappers/fixtures/dafny/holes.dfy:19:20: hole bodyless-method Q04.H1d",
                      lines)
        rc, out, err = C.tool("vcheck", f"{FX}/verus/holes.rs")
        self.assertEqual(rc, 1, out + err)                 # a real failure beside the holes
        self.assertIn("tests/wrappers/fixtures/verus/holes.rs:30:40: hole assume Q04.H1v", out)
        self.assertIn("tests/wrappers/fixtures/verus/holes.rs:22:12: error: assertion failed", out)

    def test_dafny_tests_that_print(self):
        """vcheck --test: a printing pass is a pass, not "no test ran", and a
        printing failure keeps its FAILED line (DV2b-2)."""
        target = f"{FX}/dafny/tests_print.dfy"
        rc, out, err = C.tool("vcheck", "--test", "--name", "PrintsThenPasses", target)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, f"vcheck: {target} [dafny, test]: verified — 1 passed, 0 failed\n"
                              "PASSED Fx_PrintTests.PrintsThenPasses\n")
        rc, out, err = C.tool("vcheck", "--test", "--name", "PrintsThenFails", target)
        self.assertEqual(rc, 1, out + err)
        lines = out.splitlines()
        self.assertEqual(lines[:2], [f"vcheck: {target} [dafny, test]: failed — 0 passed, 1 failed",
                                     "FAILED Fx_PrintTests.PrintsThenFails"])
        self.assertIn(f"{target}:14:5: error: two doubled", lines)
        self.assertNotIn("test-not-run", out)

    def test_clean_gate_prints_only_the_summary(self):
        for target in (f"{FX}/dafny/ok.dfy", f"{FX}/verus/clean.rs"):
            rc, out, err = C.tool("vcheck", "--gate", target)
            self.assertEqual(rc, 0, out + err)
            self.assertEqual(len(out.splitlines()), 1, out)
            self.assertRegex(out, r"gate\]: verified — [1-9]\d* verified, 0 holes, 0 errors\n$")

    def test_gate_fails_holes_and_silent_kinds(self):
        rc, out, err = C.tool("vcheck", "--gate", f"{FX}/dafny/holes.dfy")
        self.assertEqual(rc, 1, out + err)
        # silent hole kinds verify (Δ3): the Dafny gate passes them, and vaudit, the
        # other half of "done" (Δ4), fails them
        rc, out, err = C.tool("vcheck", "--gate", f"{FX}/dafny/silent.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("[dafny, gate]: verified — 2 verified, 0 holes, 0 errors", out)
        rc, out, err = C.tool("vaudit", f"{FX}/dafny/silent.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("silent.dfy:11: axiom-attribute", out)
        rc, out, err = C.tool("vcheck", "--gate", f"{FX}/verus/holes.rs")
        self.assertEqual(rc, 1, out + err)

    def test_json(self):
        import json
        rc, out, err = C.tool("vcheck", "--json", f"{FX}/verus/holes.rs")
        self.assertEqual(rc, 1, err)
        doc = json.loads(out)
        self.assertEqual(set(doc) >= {"exit_code", "verdict", "stage", "verified_count", "holes",
                                      "findings", "per_symbol"}, True)
        self.assertEqual((doc["verdict"], doc["stage"], doc["exit_code"]), ("failed", "verify", 1))
        self.assertEqual(sorted(h["label"] for h in doc["holes"]),
                         ["Q04.H1v", "Q04.H2v", "exec_hole"])

    def test_fast_channel(self):
        rc, out, err = C.tool("vcheck", "--symbol", "Fx_Holes.IncGrows", f"{FX}/dafny/holes.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("symbol Fx_Holes.IncGrows: verified", out)
        rc, out, err = C.tool("vcheck", "--symbol", "labelled", f"{FX}/verus/holes.rs")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("symbol labelled: hole", out)

    def test_allowed_passthrough(self):
        rc, out, err = C.tool("vcheck", f"{FX}/dafny/ok.dfy", "--", "--isolate-assertions")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("[dafny, learner loop]: verified — ", out)
        rc, out, err = C.tool("vcheck", f"{FX}/verus/clean.rs", "--", "--expand-errors")
        self.assertEqual(rc, 0, out + err)

    def test_filter_position_counts_assertions(self):
        """Δ39, W-D08: under --filter-position the count is of assertions, and
        the summary (and --json's count_unit) says so; observed on the pin."""
        import json
        rc, out, err = C.tool("vcheck", f"{FX}/dafny/sym.dfy", "--", "--filter-position",
                              "sym.dfy:5")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, f"vcheck: {FX}/dafny/sym.dfy [dafny, learner loop]: verified — "
                              "1 assertions verified, 0 holes, 0 errors\n")
        rc, out, err = C.tool("vcheck", "--json", f"{FX}/dafny/sym.dfy", "--",
                              "--filter-position", "sym.dfy:5")
        doc = json.loads(out)
        self.assertEqual((doc["verified_count"], doc["count_unit"]), (1, "assertions"))
        rc, out, err = C.tool("vcheck", "--json", f"{FX}/dafny/ok.dfy")
        self.assertEqual(json.loads(out)["count_unit"], "tasks")
        rc, out, err = C.tool("vcheck", "--json", f"{FX}/verus/clean.rs")
        self.assertEqual(json.loads(out)["count_unit"], "verified")

    def test_brittleness(self):
        rc, out, err = C.tool("vcheck", "--brittleness", f"{FX}/dafny/ok.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("seed 1: verified · seed 2: verified · seed 3: verified — stable", out)
        rc, out, err = C.tool("vcheck", "--brittleness", f"{FX}/verus/clean.rs")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("— stable", out)

    def test_selftest(self):
        rc, out, err = C.tool("vcheck", "--selftest")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("selftest: Dafny: gate OK", out)
        self.assertIn("selftest: Verus: gate OK", out)
        self.assertTrue(out.rstrip().endswith("selftest: PASS"), out)


class VcheckModule(RootCase):
    def test_units(self):
        rc, out, err = self.run_("vcheck", "Q04")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("vcheck: dafny/Q/Q04_ProofCraft/core [dafny, learner loop]: verified — "
                      "3 verified, 2 holes, 0 errors", out)
        self.assertIn("vcheck: 3 unit(s): 3 verified, 0 not; 5 hole(s) in all", out)
        rc, out, err = self.run_("vcheck", "Q04", "v")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out.count("vcheck: verus/q/q04_proof_craft [verus"), 1)
        rc, out, err = self.run_("vcheck", "--gate", "--module", "Q04", "--lang", "d")
        self.assertEqual(rc, 1, out + err)                 # the shipped holes fail the gate

    def test_probe_gets_the_module_context(self):
        probe = self.root / "instructor" / "scratch" / "probe.dfy"
        probe.parent.mkdir(parents=True)
        probe.write_text("module Probe {\n  import opened QG_L1_BigNat\n  import opened QG_L2_BigNat\n\n"
                         "  lemma TwiceIsDouble()\n    ensures TWICE == BASE + BASE\n  {\n  }\n}\n")
        rc, out, err = self.run_("vcheck", probe)
        self.assertEqual(rc, 1, out + err)                 # alone, the given layer is unknown
        self.assertIn("stage resolve", out)
        rc, out, err = self.run_("vcheck", "--module", "Q04", probe)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("verified — ", out)

    def test_verus_probe_gets_this_roots_layer_chain(self):
        """The chain comes from the course root (here the throwaway root's
        verus/given/ L1-L3), not from the scripts' checkout, which has no
        given crate; a probe outside the tree takes --root's. Observed on the pin."""
        import tempfile
        probe = self.root / "instructor" / "scratch" / "probe.rs"
        probe.parent.mkdir(parents=True)
        probe.write_text("use vstd::prelude::*;\nuse qg_bignat_l2::*;\n\nverus! {\n\n"
                         "proof fn probe_ok()\n    ensures\n        1int + 1 == 2,\n{\n}\n\n"
                         "} // verus!\n")
        rel = "instructor/scratch/probe.rs"
        rc, out, err = self.run_("vcheck", probe)
        self.assertEqual(rc, 1, out + err)                 # alone, the layer crate is unknown
        self.assertIn(f"{rel}:2:5: error: unresolved import `qg_bignat_l2`", out)
        rc, out, err = self.run_("vcheck", "--module", "Q04", probe)
        self.assertEqual((rc, out), (0, f"vcheck: {rel} [verus, learner loop]: verified — "
                                        "1 verified, 0 holes, 0 errors\n"), err)
        outside = Path(tempfile.mkdtemp(prefix="dvl-tools-outside-", dir=C.TMP_BASE))
        try:
            shutil.copyfile(probe, outside / "probe.rs")
            rc, out, err = self.run_("vcheck", "--module", "Q04", outside / "probe.rs")
            self.assertEqual(rc, 0, out + err)
            self.assertIn("[verus, learner loop]: verified — 1 verified, 0 holes, 0 errors", out)
        finally:
            shutil.rmtree(outside, ignore_errors=True)


PIN_COUNTS_OUT = (  # observed on the pin: `vcheck --ref --pin-counts Q04` over the fixture twins
    "vcheck --pin-counts: Solutions/dafny/Q/Q04_ProofCraft/core [dafny]: reference 7 verified; "
    "3 of 3 contract declaration(s) pinned (gate floor 3)",
    "vcheck --pin-counts: Solutions/dafny/Q/Q04_ProofCraft/std [dafny]: reference 3 verified; "
    "1 of 1 contract declaration(s) pinned (gate floor 1)",
    "vcheck --pin-counts: Solutions/verus/q/q04_proof_craft [verus]: reference 6 verified; "
    "4 of 4 contract declaration(s) pinned (gate floor 4)",
    "vcheck --pin-counts: dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy [exercise]: shipped "
    "verified, 2 hole(s), 0 error(s)",
    "vcheck --pin-counts: dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy [exercise]: shipped "
    "verified, 1 hole(s), 0 error(s)",
    "vcheck --pin-counts: verus/q/q04_proof_craft/src/lib.rs [exercise]: shipped verified, "
    "2 hole(s), 0 error(s)",
    "vcheck --pin-counts: verus/q/q04_proof_craft/src/tests.rs [exercise]: shipped verified, "
    "0 hole(s), 0 error(s)",
    "vcheck --pin-counts: dafny/checks/Q04_checks.dfy [check]: shipped verified, 0 hole(s), "
    "0 error(s)",
    "vcheck --pin-counts: dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy [exit]: shipped verified, "
    "2 hole(s), 0 error(s)",
    "vcheck --pin-counts: verus/q/q04_proof_craft/src/exit.rs [exit]: shipped verified, "
    "2 hole(s), 0 error(s)",
    "vcheck --pin-counts: dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy [agent]: shipped "
    "verified, 0 hole(s), 0 error(s)",
    "vcheck --pin-counts: verus/q/q04_proof_craft/src/agent.rs [agent]: shipped verified, "
    "0 hole(s), 0 error(s)",
    "vcheck --pin-counts: wrote expected/Q04.counts (3 unit(s), 9 file(s))")


def pin_counts(case):
    """Copy the fixture twins into the root and write expected/Q04.counts."""
    if not (case.root / "Solutions").exists():
        shutil.copytree(REFERENCE, case.root / "Solutions")
    rc, out, err = case.run_("vcheck", "--ref", "--pin-counts", "Q04", env={"CI": "true"})
    case.assertEqual(rc, 0, out + err)
    return out


class VcheckRef(RootCase):
    def test_twin_mode(self):
        shutil.copytree(REFERENCE, self.root / "Solutions")
        targets = ["Solutions/dafny/Q/Q04_ProofCraft/core", "Solutions/dafny/Q/Q04_ProofCraft/std",
                   "Solutions/dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy",
                   "Solutions/dafny/checks/Q04_checks.dfy", "Solutions/verus/q/q04_proof_craft",
                   "Solutions/verus/q/q04_proof_craft/src/exit.rs"]
        rc, out, err = self.run_("vcheck", "--ref", targets[1], env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)                  # a unit twin with no count pin
        self.assertIn("Solutions/dafny/Q/Q04_ProofCraft/std: count-pin-missing", out)
        self.assertEqual(pin_counts(self).splitlines(), list(PIN_COUNTS_OUT))
        pinned = (self.root / "expected" / "Q04.counts").read_text()
        self.assertIn('symbols = ["Q04_ProofCraft.H1", "Q04_ProofCraft.Sum", '
                      '"Q04_ProofCraft.SumFormula"]', pinned)
        self.assertIn('symbols = ["h1", "sum", "sum_formula", "twice"]', pinned)
        self.assertNotIn("CheckSumZero", pinned)            # a twin-only test is never pinned
        rc, out, err = self.run_("vcheck", "--ref", *targets, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("vcheck: 6 unit(s): 6 verified, 0 not; 0 hole(s) in all", out)
        # a twin that drifts from its count pin fails the reference gate (stale pin)
        std = "Solutions/dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"
        shipped = (self.root / std).read_text()
        self.rep(std, "  // item: Q04.T1dv", "  // reference-only: a helper\n  lemma Extra(x: nat)\n"
                 "    ensures x + 1 > x\n  {\n  }\n\n  // item: Q04.T1dv")
        rc, out, err = self.run_("vcheck", "--ref", targets[1], env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("[dafny, reference gate]: failed — 4 verified, 0 holes, 0 errors, 1 finding",
                      out)
        self.assertIn("Solutions/dafny/Q/Q04_ProofCraft/std: count-pin-stale", out)
        (self.root / std).write_text(shipped)
        self.rep("Solutions/dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy",
                 "    DoubleIsTwice(a);\n", "    assert Double(a) == 3;\n")
        rc, out, err = self.run_("vcheck", "--ref", targets[2], env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Solutions/dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy:", out)
        self.assertNotIn("assertion might not hold", out)    # locations only
        self.assertNotIn("/tmp", out.split("raw output:")[0])
        import json
        rc, out, err = self.run_("vcheck", "--ref", "--json", targets[2], env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        doc = json.loads(out)
        self.assertEqual(doc["verdict"], "failed")
        self.assertTrue(doc["diagnostics"])
        self.assertEqual({d["message"] for d in doc["diagnostics"]}, {""})   # --json too
        rc, out, err = self.run_("vaudit", "--ref", targets[0], targets[4], env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)

    def test_loose_dafny_dir(self):
        """A directory of loose .dfy files that mirrors no learner path (the DV0
        spikes' shape: cross-file imports, no project) is one program under --ref."""
        d = self.root / "Solutions" / "spikes" / "dafny"
        d.mkdir(parents=True)
        (d / "A_Base.dfy").write_text("module A_Base {\n  function Inc(n: nat): nat { n + 1 }\n\n"
                                      "  lemma IncGrows(n: nat)\n    ensures Inc(n) > n\n  {\n  }\n}\n")
        (d / "B_Use.dfy").write_text("module B_Use {\n  import opened A_Base\n\n"
                                     "  lemma IncTwice(n: nat)\n    ensures Inc(Inc(n)) > n\n  {\n"
                                     "    IncGrows(n);\n    IncGrows(Inc(n));\n  }\n}\n")
        rc, out, err = self.run_("vcheck", "--ref", d / "B_Use.dfy", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)                  # alone, its import does not resolve
        self.assertIn("stage resolve", out)
        rc, out, err = self.run_("vcheck", "--ref", d, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, "vcheck: Solutions/spikes/dafny [dafny, reference gate]: verified — "
                              "3 verified, 0 holes, 0 errors\n")
        rc, out, err = self.run_("vaudit", "--ref", d, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("vaudit: Solutions/spikes/dafny [dafny, reference]: 0 finding(s)", out)
        rc, out, err = self.run_("vcheck", d)
        self.assertEqual(rc, 3, out + err)                  # reference material, and no unit


class CountGate(RootCase):
    """Δ11: the learner gate on a registry unit meets its count pin."""

    def test_deleted_lemma_fails_the_gate(self):
        pin_counts(self)
        for rel in ("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy",
                    "verus/q/q04_proof_craft/src/lib.rs", "verus/q/q04_proof_craft/src/tests.rs"):
            shutil.copyfile(self.root / "Solutions" / rel, self.root / rel)   # a finished unit
        d, v = "dafny/Q/Q04_ProofCraft/core", "verus/q/q04_proof_craft"
        rc, out, err = self.run_("vcheck", "--gate", self.root / d)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, f"vcheck: {d} [dafny, gate]: verified — 7 verified, 0 holes, "
                              "0 errors\n")
        rc, out, err = self.run_("vcheck", "--gate", self.root / v / "src" / "lib.rs")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("[verus, gate]: verified — 6 verified, 0 holes, 0 errors", out)
        # delete a proved lemma: everything else still verifies, the pin fails the gate
        for rel, a, b in ((f"{d}/Q04_ProofCraft.dfy", "  // item: Q04.H3d",
                           "  method {:test} CheckSum()"),
                          (f"{v}/src/lib.rs", "// item: Q04.H3v", "} // verus!")):
            text = (self.root / rel).read_text()
            (self.root / rel).write_text(text[:text.index(a)] + text[text.index(b):])
        rc, out, err = self.run_("vcheck", "--gate", self.root / d)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"vcheck: {d} [dafny, gate]: failed — 6 verified, 0 holes, 0 errors, "
                      "1 finding", out)
        self.assertIn(f"{d}: pinned-symbol-missing: Q04_ProofCraft.SumFormula: no verification "
                      "task ran for this pinned declaration", out)
        rc, out, err = self.run_("vcheck", "--gate", self.root / v)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"vcheck: {v} [verus, gate]: failed — 4 verified, 0 holes, 0 errors, "
                      "1 finding", out)
        self.assertIn(f"{v}: pinned-symbol-missing: sum_formula", out)
        # a unit with no count pin never passes the gate
        (self.root / "expected" / "Q04.counts").unlink()
        rc, out, err = self.run_("vcheck", "--gate", self.root / d)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{d}: count-pin-missing: {d} has no count pin in expected/Q04.counts", out)


# =====================================================================================
# vaudit
# =====================================================================================

class Vaudit(unittest.TestCase):
    def test_dafny_silent_and_golden(self):
        import tempfile
        rc, out, err = C.tool("vaudit", f"{FX}/dafny/silent.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("silent.dfy:11: audit-axiom — ", out)
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-audit-", dir=C.TMP_BASE))
        try:
            pin = tmp / "silent.audit"
            rc, out, err = C.tool("vaudit", "--write", pin, f"{FX}/dafny/silent.dfy")
            self.assertEqual(rc, 0, out + err)
            self.assertIn("tests/wrappers/fixtures/dafny/silent.dfy:11: axiom-attribute",
                          pin.read_text())
            rc, out, err = C.tool("vaudit", "--compare", pin, f"{FX}/dafny/silent.dfy")
            self.assertEqual(rc, 0, out + err)
            self.assertIn("matches", out)
            pin.write_text(pin.read_text() + "x.dfy:1: audit-axiom\n")
            rc, out, err = C.tool("vaudit", "--compare", pin, f"{FX}/dafny/silent.dfy")
            self.assertEqual(rc, 1, out + err)
            self.assertIn("- x.dfy:1: audit-axiom", out)
            rc, out, err = C.tool("vaudit", "--compare", tmp / "none.audit",
                                  f"{FX}/dafny/ok.dfy")
            self.assertEqual(rc, 1, out + err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        rc, out, err = C.tool("vaudit", f"{FX}/dafny/ok.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("0 finding(s)", out)

    def test_verus_holes(self):
        rc, out, err = C.tool("vaudit", f"{FX}/verus/holes.rs")
        self.assertEqual(rc, 1, out + err)
        for kind in ("hole-assume", "hole-admit", "hole-external-body"):
            self.assertIn(kind, out)
        rc, out, err = C.tool("vaudit", f"{FX}/verus/clean.rs")
        self.assertEqual(rc, 0, out + err)


GIVEN_FX = C.ROOT / "tests" / "wrappers" / "fixtures" / "dafny" / "given"
ABSTRACT_LEARNER = (  # observed on the pin: refined.dfy audited as a learner file
    "3: abstract-module", "5: uninitialized-const", "6: bodyless-abstract",
    "7: bodyless-abstract", "8: bodyless-abstract", "10: bodyless-abstract",
    "13: bodyless-abstract")


class VauditGiven(RootCase):
    """Δ44: a frozen abstract spec the program refines in full audits clean as
    a given layer (by path in the tree; --mode given for an out-of-tree copy;
    --ref --mode given for a reference copy such as the DV0 L4 spike) and
    stays a finding in a learner file."""

    def lines(self, out, rel):
        return [x[len(rel) + 1:].split(" — ")[0] for x in out.splitlines()
                if x.startswith(rel + ":")]

    def test_in_tree_roles(self):
        given = "dafny/given/Q/QG_L4_Spec.dfy"
        shutil.copyfile(GIVEN_FX / "refined.dfy", self.root / given)
        probe = "instructor/scratch/probe.dfy"
        (self.root / probe).parent.mkdir(parents=True)
        shutil.copyfile(GIVEN_FX / "refined.dfy", self.root / probe)
        for args in ((), ("--mode", "given")):
            rc, out, err = self.run_("vaudit", *args, self.root / given)
            self.assertEqual(rc, 0, (args, out, err))
            self.assertEqual(out, f"vaudit: {given} [dafny, {'given' if args else 'learner'}]: "
                                  "0 finding(s)\n")
        rc, out, err = self.run_("vaudit", self.root / probe)
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(self.lines(out, probe), list(ABSTRACT_LEARNER))
        rc, out, err = self.run_("vaudit", "--mode", "given", self.root / probe)
        self.assertEqual(rc, 3, out + err)
        self.assertIn(f"--mode given: {probe} is not a given layer or a declared statement", err)
        # a reference directory shaped like the DV0 spikes (spec and refiner in
        # two loose files): reference rules, plus the given role on request
        spikes = self.root / "Solutions" / "spikes" / "dafny"
        spikes.mkdir(parents=True)
        for name in ("spec_only.dfy", "impl_only.dfy"):
            shutil.copyfile(GIVEN_FX / name, spikes / name)
        rc, out, err = self.run_("vaudit", "--ref", spikes, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(out, "Solutions/spikes/dafny/spec_only.dfy:3: abstract-module\n"
                              "Solutions/spikes/dafny/spec_only.dfy:4: bodyless-abstract\n"
                              "Solutions/spikes/dafny/spec_only.dfy:6: bodyless-abstract\n"
                              "vaudit: Solutions/spikes/dafny [dafny, reference]: 3 finding(s)\n")
        rc, out, err = self.run_("vaudit", "--ref", "--mode", "given", spikes, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, "vaudit: Solutions/spikes/dafny [dafny, reference, given]: "
                              "0 finding(s)\n")

    def test_out_of_tree_copy(self):
        """The DV1b e2e repro: given layers laid out in a scratch unit with no
        course tree around them."""
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-given-", dir=C.TMP_BASE))
        try:
            for name in ("refined.dfy", "partial.dfy"):
                shutil.copyfile(GIVEN_FX / name, tmp / name)
            unit = tmp / "unit"
            unit.mkdir()
            for name in ("spec_only.dfy", "impl_only.dfy"):
                shutil.copyfile(GIVEN_FX / name, unit / name)
            (unit / "dfyconfig.toml").write_text('includes = ["*.dfy"]\n\n[options]\n'
                                                 'resource-limit = 1000000\n')
            rc, out, err = C.tool("vaudit", tmp / "refined.dfy")
            self.assertEqual(rc, 1, out + err)
            self.assertEqual(self.lines(out, str(tmp / "refined.dfy")), list(ABSTRACT_LEARNER))
            rc, out, err = C.tool("vaudit", "--mode", "given", tmp / "refined.dfy")
            self.assertEqual(rc, 0, out + err)
            self.assertIn("[dafny, given]: 0 finding(s)", out)
            rc, out, err = C.tool("vaudit", "--mode", "given", tmp / "partial.dfy")
            self.assertEqual(rc, 1, out + err)
            self.assertEqual(self.lines(out, str(tmp / "partial.dfy")),
                             ["3: abstract-not-refined", "9: audit-bodyless-ghost",
                              "9: bodyless-abstract"])
            rc, out, err = C.tool("vaudit", unit)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("[dafny, learner]: 3 finding(s)", out)
            rc, out, err = C.tool("vaudit", "--mode", "given", unit)
            self.assertEqual(rc, 0, out + err)
            self.assertIn("[dafny, given]: 0 finding(s)", out)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


GIVEN_L1 = ("//! Invented given layer (tests/wrappers): one assumed lemma, one clean fn.\n"
            "use vstd::prelude::*;\n\nverus! {\n\n"
            "pub proof fn lemma_assumed(x: nat)\n    ensures\n        x * 2 == x + x,\n{\n"
            "    assume(false);\n}\n\n"
            "pub open spec fn twice(x: nat) -> nat {\n    x + x\n}\n\n} // verus!\n")
TRUST_ENTRY = ('[[trust]]\npath = "verus/given/qg_bignat_l1/src/lib.rs"\nsymbol = "{sym}"\n'
               'kind = "{kind}"\nreason = "test"\n\n')


class VauditCheckTrust(RootCase):
    """vaudit --check-trust (dvl.verus.check_trust) on a throwaway course root:
    its own verus/given/ crates (the armed tree's L1-L3, L1 given an invented
    assumed lemma) and its own expected/verus_trust.toml, never the scripts'
    checkout's."""

    def test_check_trust(self):
        (self.root / "verus/given/qg_bignat_l1/src/lib.rs").write_text(GIVEN_L1)
        lib = "verus/given/qg_bignat_l1/src/lib.rs"
        rc, out, err = self.run_("vaudit", "--check-trust")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(out, f"{lib}:10: hole-assume — an assume hole (in lemma_assumed) not on "
                              "the trust allowlist\nvaudit --check-trust: 3 given crate(s) under "
                              "verus/given/, 0 trust entries (expected/verus_trust.toml): "
                              "1 finding(s)\n")
        (self.root / "expected").mkdir()
        trust = self.root / "expected" / "verus_trust.toml"
        trust.write_text(TRUST_ENTRY.format(sym="lemma_assumed", kind="assume"))
        rc, out, err = self.run_("vaudit", "--check-trust")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, "vaudit --check-trust: 3 given crate(s) under verus/given/, "
                              "1 trust entry (expected/verus_trust.toml): 0 finding(s)\n")
        trust.write_text(TRUST_ENTRY.format(sym="lemma_assumed", kind="assume")
                         + TRUST_ENTRY.format(sym="twice", kind="uninterp"))
        rc, out, err = self.run_("vaudit", "--check-trust")
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{lib}:0: stale-trust-entry — trust entry twice (uninterp) matches no "
                      "hole of a given layer", out)
        trust.write_text(TRUST_ENTRY.format(sym="nosuch", kind="assume"))
        rc, out, err = self.run_("vaudit", "--check-trust")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("expected/verus_trust.toml:1: bad-trust-entry", out)
        self.assertIn("an invalid allowlist", out)


class SpecfreezeAgainst(unittest.TestCase):
    def test_refinement_and_hash_modes(self):
        rc, out, err = C.tool("specfreeze", "--against", f"{FX}/dafny/freeze/spec.dfy",
                              f"{FX}/dafny/freeze/good.dfy")
        self.assertEqual(rc, 0, out + err)
        rc, out, err = C.tool("specfreeze", "--against", f"{FX}/dafny/freeze/spec.dfy",
                              f"{FX}/dafny/freeze/weak.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("weak.dfy:6: freeze-refinement", out)
        rc, out, err = C.tool("specfreeze", "--against", f"{FX}/verus/freeze/base.rs",
                              f"{FX}/verus/freeze/cosmetic.rs")
        self.assertEqual(rc, 0, out + err)


# =====================================================================================
# firsttry and pins: the slot lifecycle on the armed Q04
# =====================================================================================

FILL = (  # (file, shipped slot text, filled text); the answers were observed on the pin
    ("specimens/Q04/P4d.dfy.specimen", "FAILS ???", "FAILS b d"),
    ("specimens/Q04/P3d.dfy.specimen", "FAILS ???", "FAILS none"),
    ("specimens/Q04/P5d.dfy.specimen", 'EXPECT @??? "???"',
     'EXPECT @7 "postcondition could not be proved"'),
    ("specimens/Q04/P6v.rs.specimen", "FAILS ???", "FAILS a"),                       # wrong
    ("specimens/Q04/P7v.rs.specimen", 'EXPECT @??? "???"',
     'EXPECT @10 "postcondition not satisfied"'),
    ("dafny/checks/Q04_checks.dfy", "expect Twice(21) == ???;", "expect Twice(21) == 42;"),
    ("dafny/checks/Q04_checks.dfy", "expect Twice(0) == ???;", "expect Twice(0) == 1;"),  # wrong
    ("verus/q/q04_proof_craft/src/tests.rs", "assert_eq!(twice(21), ???);",
     "assert_eq!(twice(21), 42);"),
    ("verus/q/q04_proof_craft/src/lib.rs", "assert(double(3) == ???) by (compute_only);",
     "assert(double(3) == 7) by (compute_only);"),                                    # wrong
    ("slots/Q04.slots", "P1dv = ???", 'P1dv = "verified  2"'),
    ("slots/Q04.slots", "P2dv = ???", 'P2dv = "x"'),                                  # wrong
)


class SlotLifecycle(RootCase):
    git = True

    def fill(self):
        for rel, old, new in FILL:
            self.rep(rel, old, new)
        shutil.copytree(REFERENCE, self.root / "Solutions")
        rc, out, err = self.run_("pins.py", "--update", "--ref", "--module", "Q04",
                                 env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)

    def test_check_report_pins(self):
        self.fill()
        rc, out, err = self.run_("firsttry.py", "Q04", "--check")
        self.assertEqual(rc, 0, out + err)
        for iid in ("P10v", "P8d", "P1dv", "P3d", "P4d", "P5d", "P7v"):
            self.assertIn(f"✓ Q04.{iid}  first try passes", out)
        for iid in ("P9d", "P2dv", "P11v", "P6v"):
            self.assertIn(f"✗ Q04.{iid}  first try fails", out)
        for leak in ("assertion might not hold", "postcondition", "42"):
            self.assertNotIn(leak, out.replace("could not be proved", ""))
        calib = (self.root / "instructor/calib/Q04.tsv").read_text().splitlines()
        self.assertEqual(len(calib), 11)
        self.assertTrue(all(r.split("\t")[1] == "predict" for r in calib))
        # enable two right and two wrong slots, then the report and the learner harness
        for rel, old in (("specimens/Q04/P4d.dfy.specimen", "// SLOT: FAILS b d"),
                         ("specimens/Q04/P6v.rs.specimen", "// SLOT: FAILS a"),
                         ("dafny/checks/Q04_checks.dfy", "// SLOT: expect Twice(0) == 1;"),
                         ("verus/q/q04_proof_craft/src/tests.rs",
                          "// SLOT: assert_eq!(twice(21), 42);")):
            self.rep(rel, old, old.replace("SLOT: ", "") if "FAILS" in old
                     else old.replace("// SLOT: ", ""))
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "// SLOT: CHECK P1dv",
                 "// CHECK P1dv")
        rc, out, err = self.run_("firsttry.py", "Q04", "--report", "--strict")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.P4d   obligation: enabled ✓ · first try ✓", out)
        self.assertIn("Q04.P1dv  verdict: enabled ✓ · first try ✓", out)
        self.assertIn("Q04.P9d   value: enabled ✗ · first try ✗", out)
        self.assertIn("dafny/checks/Q04_checks.dfy:16: failing: Q04.P9d: enabled slot fails", out)
        self.assertIn("specimens/Q04/P6v.rs.specimen:3: failing: Q04.P6v: enabled slot fails",
                      out)
        self.assertIn("first-try: 7/11 recorded P item(s) passed (64%)", out)
        rc, out, err = self.run_("pins.py", "Q04")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("✓ Q04.P10v", out)
        self.assertIn("✗ Q04.P9d  dafny/checks/Q04_checks.dfy:16", out)
        self.assertIn("pins Q04: 3 pass, 2 not", out)
        # repaired predictions pass; the record keeps the first try
        self.rep("dafny/checks/Q04_checks.dfy", "expect Twice(0) == 1;", "expect Twice(0) == 0;")
        self.rep("specimens/Q04/P6v.rs.specimen", "// FAILS a", "// FAILS b")
        rc, out, err = self.run_("pins.py", "Q04")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins Q04: 5 pass, 0 not", out)

    def test_enabled_before_recording_is_observed(self):
        self.fill()
        self.rep("specimens/Q04/P4d.dfy.specimen", "// SLOT: FAILS b d", "// FAILS b d")
        rc, out, err = self.run_("pins.py", "Q04")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.P4d  enabled, but its first try is not recorded", out)
        rc, out, err = self.run_("firsttry.py", "Q04", "--check")
        self.assertIn("· Q04.P4d  observed ✓ (not a first try", out)
        row = [r for r in (self.root / "instructor/calib/Q04.tsv").read_text().splitlines()
               if r.startswith("Q04.P4d\t")]
        self.assertEqual(row[0].split("\t")[1:3], ["observed", "pass"])

    def test_pins_author_modes(self):
        self.fill()
        rc, out, err = self.run_("pins.py", "--ref", env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --ref: 7 check(s); 0 problem(s)", out)
        rc, out, err = self.run_("pins.py", "--update", "specimens/Q04/C2d.dfy.specimen",
                                 "specimens/Q04/P6v.rs.specimen", env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)                  # P6v carries a slot: never pinned whole
        self.assertIn("specimens/Q04/P6v.rs.specimen carries prediction slots (Q04.P6v)", err)
        self.assertFalse((self.root / "expected/specimens").exists())
        rc, out, err = self.run_("pins.py", "--update", "specimens/Q04/C2d.dfy.specimen",
                                 env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        sc = self.root / "expected/specimens/Q04/C2d.dfy.specimen.expect"
        self.assertIn("C2d.dfy.specimen:7:5: error: assertion might not hold", sc.read_text())
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)                  # the count pins are missing
        self.assertIn("expected/Q04.counts:0: Q04 has 3 verification unit(s) and no count pin", out)
        pin_counts(self)
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        # 2 verdict pins, their 2 reference hashes, 3 count pins, 9 shipped-state file pins,
        # 1 EXPECT pin, 1 sidecar
        self.assertIn("pins --ci: 18 pin(s) checked over 1 module(s); 0 problem(s)", out)
        pins_file = self.root / "expected/Q04.pins"
        good = pins_file.read_text()
        local, digest = next((ln.split()[0], ln.split()[2]) for ln in good.splitlines()
                             if ln.startswith("P2dv"))
        pins_file.write_text(good.replace(digest, "0" * 64))
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)                  # a wrong hash: --ci catches it now
        self.assertIn("Solutions/slots/Q04.slots:", out)
        self.assertIn(": Q04.P2dv: the reference answer does not match its pin", out)
        pins_file.write_text(good)
        sc.write_text(sc.read_text().replace("assertion might not hold", "something else here"))
        self.rep("specimens/Q04/C2d.dfy.specimen", "// EXPECT @7", "// EXPECT @6")
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("specimens/Q04/C2d.dfy.specimen:3: EXPECT pin not matched", out)
        self.assertIn("specimens/Q04/C2d.dfy.specimen: golden mismatch at normalized line 6", out)
        self.assertNotIn("assertion might not hold", out)    # locations only
        self.assertNotIn("something else", out)


class ExitAndEmptyBody(RootCase):
    def test_exit_scoring(self):
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.X1d  now — unattempted: hole at line 10 · not recorded", out)
        self.assertIn("4 item(s) not yet recorded", out)
        self.assertFalse((self.root / "instructor/calib/Q04.tsv").exists())
        # one block has a resolution error: it is blanked and the others still judged
        self.rep("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "    ensures Double(n) == 2 * n\n",
                 "    ensures Double(n) == 2 * n\n  {\n    NoSuchLemma(n);\n  }\n")
        self.rep("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "    ensures Double(a) <= Double(b)\n",
                 "    ensures Double(a) <= Double(b)\n  {\n  }\n")
        self.rep("verus/q/q04_proof_craft/src/exit.rs",
                 '    #[verifier::proof_note("Q04.X1v")] assume(false);\n', "    let x: u8 = true;\n")
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.X2v  now — unattempted: hole at line 28", out)
        self.assertIn("nothing recorded: Q04.X2v hold no attempt yet", out)
        self.assertFalse((self.root / "instructor/calib/Q04.tsv").exists())
        self.rep("verus/q/q04_proof_craft/src/exit.rs",
                 '    #[verifier::proof_note("Q04.X2v")] assume(false);\n', "")
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.X1d  now ✗ error at line 12 · first run: recorded now", out)
        self.assertIn("Q04.X2d  now ✓ · first run: recorded now", out)
        self.assertIn("Q04.X1v  now ✗ error at line 17 · first run: recorded now", out)
        self.assertIn("Q04.X2v  now ✓ · first run: recorded now", out)
        self.assertIn("Q04 exit: 2/4 (threshold 3; per language Dafny 1/2 (≥1), Verus 1/2 (≥1)) "
                      "FAIL", out)
        rows = (self.root / "instructor/calib/Q04.tsv").read_text().splitlines()
        self.assertEqual([r.split("\t")[:3] for r in rows],
                         [["Q04.X1d", "exit", "fail"], ["Q04.X2d", "exit", "pass"],
                          ["Q04.X1v", "exit", "fail"], ["Q04.X2v", "exit", "pass"]])
        # repairs never change the score: the first complete run is the record
        self.rep("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "    NoSuchLemma(n);\n", "")
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertIn("Q04.X1d  now ✓ · first run ✗", out)
        self.assertIn("Q04 exit: 2/4", out)

    def test_empty_body_gate(self):
        rc, out, err = self.run_("firsttry.py", "Q04", "--empty-body", "--eb-modes", "E0",
                                 "--eb-seeds", "1", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("✗ Q04.H1d  FALLS TO AUTOMATION: the empty body verifies in maxauto, "
                      "shipped:seed=1, shipped:seed=2, shipped:seed=3", out)
        self.assertIn("✓ Q04.H3d  the empty body fails in every run", out)
        self.assertIn("Q04_ProofCraft.dfy:29: lever-needed", out)
        self.assertIn("✗ Q04.H1v  FALLS TO AUTOMATION: the empty body verifies in E0 seed=1", out)
        self.assertIn("✓ Q04.H3v  the empty body fails in every run", out)
        # the fixture's exit holes are closed by automation too (they are not course items)
        self.assertIn("✗ Q04.X1d  FALLS TO AUTOMATION", out)
        self.assertIn("✗ Q04.X2v  FALLS TO AUTOMATION: the empty body verifies in E0 seed=1", out)
        self.assertIn("Q04 empty-body: 2/9 hole(s) pass the gate", out)


class ModerateTierTools(RootCase):
    """DV3a tool items on real runs: the region gate of --empty-body (QPLAN §6
    Q18), a budget item at the exit (Q21) and property tests in the strict
    report (Q20)."""

    CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
    LIB_RS = "verus/q/q04_proof_craft/src/lib.rs"
    EXIT = "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy"

    def test_region_gate(self):
        shutil.copytree(REFERENCE, self.root / "Solutions")
        twin = self.root / "Solutions" / self.CORE
        C.replace_in(twin, "  {\n    if n > 0 {\n      SumFormula(n - 1);\n    }\n  }\n",
                     "  {\n    // @hole-begin Q04.H3d\n    if n > 0 {\n      SumFormula(n - 1);\n"
                     "    }\n    // @hole-end Q04.H3d\n  }\n")
        vt = self.root / "Solutions" / self.LIB_RS
        text = vt.read_text()
        s0 = text.index("pub proof fn sum_formula")
        s1 = text.index("    if n > 0 {", s0)
        e1 = text.index("\n}\n", s1)
        vt.write_text(text[:s1] + "    // @hole-begin Q04.H3v\n" + text[s1:e1]
                      + "\n    // @hole-end Q04.H3v" + text[e1:])
        rc, out, err = self.run_("firsttry.py", "Q04", "--empty-body", "--eb-modes", "RGN",
                                 "--eb-seeds", "1", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        # Dafny: both gates; the region gate on the twin, its location in the reference tree
        self.assertIn(f"✓ Q04.H3d  the empty body fails in every run ({self.CORE})", out)
        self.assertIn(f"✓ Q04.H3d  the twin without its 1 learner region(s) fails in every run "
                      f"({self.CORE})", out)
        line = next(i for i, x in enumerate(twin.read_text().split("\n"), 1)
                    if "lemma SumFormula" in x)
        self.assertIn(f"    Solutions/{self.CORE}:{line}: lever-needed", out)
        # Verus: --eb-modes RGN runs the region gate only, where the twin marks a region
        self.assertIn(f"✓ Q04.H3v  the twin without its 1 learner region(s) fails in every run "
                      f"({self.LIB_RS})", out)
        self.assertNotIn("✓ Q04.H3v  the empty body", out)
        self.assertIn("? Q04.H1v  no gate run: --eb-modes names only RGN and its twin marks no "
                      "learner region", out)
        self.assertIn("✗ Q04.H1d  FALLS TO AUTOMATION: the empty body verifies", out)
        self.assertFalse(any((self.root / "Solutions").rglob("*.vir")))
        # a region whose lines automation supplies falls to automation
        C.replace_in(twin, "    // @hole-begin Q04.H3d\n    if n > 0 {\n      SumFormula(n - 1);\n"
                     "    }\n    // @hole-end Q04.H3d\n",
                     "    if n > 0 {\n      SumFormula(n - 1);\n    }\n"
                     "    // @hole-begin Q04.H3d\n    assert true;\n    // @hole-end Q04.H3d\n")
        rc, out, err = self.run_("firsttry.py", "Q04", "--empty-body", "--eb-modes", "RGN",
                                 "--eb-seeds", "1", env={"CI": "true"})
        self.assertIn("✗ Q04.H3d  FALLS TO AUTOMATION: the twin without its 1 learner region(s) "
                      "verifies in region-maxauto, region-shipped:seed=1, region-shipped:seed=2, "
                      "region-shipped:seed=3", out)

    def test_budget_item_at_the_exit(self):
        self.rep(self.EXIT, "  // item: Q04.X2d S5\n  // uses: lemma-call\n",
                 "  // item: Q04.X2d S5\n  // uses: lemma-call, rlimit\n")
        self.rep(self.EXIT, "    ensures Double(n) == 2 * n\n",
                 "    ensures Double(n) == 2 * n\n  {\n  }\n")
        self.rep(self.EXIT, "    ensures Double(a) <= Double(b)\n",
                 "    ensures Double(a) <= Double(b)\n  {\n    Helper();\n  }\n\n"
                 "  lemma {:resource_limit 100000} Helper()\n    ensures true\n  {\n  }\n")
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertIn("Q04.X1d  now ✓ · not recorded", out)
        line = next(i for i, x in enumerate((self.root / self.EXIT).read_text().split("\n"), 1)
                    if "{:resource_limit 100000}" in x)
        self.assertIn(f"Q04.X2d  now ✗ a resource attribute at line {line} (resource-attribute): "
                      "a budget item proves at the pinned limit · not recorded", out)
        # without the attribute the same proof passes at the pinned limit
        self.rep(self.EXIT, "lemma {:resource_limit 100000} Helper()", "lemma Helper()")
        rc, out, err = self.run_("firsttry.py", "Q04", "--exit")
        self.assertIn("Q04.X2d  now ✓ · not recorded", out)

    def test_property_tests_in_the_strict_report(self):
        self.rep(self.CORE, "  // item: Q04.H3d S3\n  // uses: calc\n",
                 "  // item: Q04.H3d S3\n  // uses: calc, property-test\n")
        rc, out, err = self.run_("firsttry.py", "Q04", "--report", "--strict")
        self.assertEqual(rc, 1, out + err)
        unit = "dafny/Q/Q04_ProofCraft/core"
        self.assertIn(f"  property tests (Q04.H3d): {unit}: verified — 1 passed, 0 failed", out)
        self.assertIn("failing property-test runs 0", out)
        self.rep(self.CORE, "    // expect Sum(3) == 6;", "    expect Sum(3) == 7;")
        rc, out, err = self.run_("firsttry.py", "Q04", "--report", "--strict")
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{unit}:0: property tests: Q04.H3d: `scripts/vcheck --test {unit}`: "
                      "1 failed", out)
        self.assertIn("failing property-test runs 1", out)


# =====================================================================================
# DV2a fix round: the shipped-state pins, vcheck --test, the value and
# obligation judges, sealed sidecars, code test-outs, the planted marker
# =====================================================================================

CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
STD = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"
CRATE = "verus/q/q04_proof_craft"


def calib(root, *ids):
    d = root / "instructor" / "calib"
    d.mkdir(parents=True, exist_ok=True)
    with (d / "Q04.tsv").open("a") as f:
        for iid in ids:
            f.write(f"{iid}\tpredict\tpass\t2026-10-04\tx\n")


class Shipped(RootCase):
    """Q8: every file's shipped state (verdict, tool-counted holes, errors) is
    pinned beside the unit counts and compared by vcheck --shipped."""

    def test_shipped_state(self):
        pin_counts(self)
        rc, out, err = self.run_("vcheck", "--shipped", "Q04")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, "vcheck --shipped: Q04 (Dafny and Verus): 9 file(s) checked against "
                              "expected/Q04.counts; 0 problem(s)\n")
        # an exit hole filled, and a second hole inside an existing item's block
        self.rep(f"{CRATE}/src/exit.rs", '    #[verifier::proof_note("Q04.X2v")] assume(false);\n',
                 "")
        self.rep(f"{CRATE}/src/lib.rs", '    #[verifier::proof_note("Q04.H3v")] assume(false);\n',
                 '    #[verifier::proof_note("Q04.H3v")] assume(false);\n    assume(n > 0);\n')
        rc, out, err = self.run_("vcheck", "--shipped", "Q04", "v")
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CRATE}/src/exit.rs: not in its shipped state: pinned exit verified, "
                      "2 hole(s), 0 error(s); the learner loop gives exit verified, 1 hole(s), "
                      "0 error(s)", out)
        self.assertIn(f"{CRATE}/src/lib.rs: not in its shipped state: pinned exercise verified, "
                      "2 hole(s), 0 error(s); the learner loop gives exercise verified, 3 hole(s)",
                      out)
        self.assertIn("vcheck --shipped: Q04 (Verus): 4 file(s) checked against "
                      "expected/Q04.counts; 2 problem(s)", out)


class CompiledChecks(RootCase):
    """vcheck --test: the compiled checks, learner-safe (H5 on enabled slots)."""

    def test_dafny_and_verus(self):
        for rel in ("dafny/checks/Q04_checks.dfy", f"{CRATE}/src/lib.rs", f"{CRATE}/src/tests.rs"):
            shutil.copyfile(REFERENCE / rel, self.root / rel)      # finished, slots enabled
        rc, out, err = self.run_("vcheck", "--test", "dafny/checks/Q04_checks.dfy")
        self.assertEqual(rc, 3, out + err)                          # unrecorded first tries
        self.assertIn("Q04.P8d, Q04.P9d", err)
        calib(self.root, "Q04.P8d", "Q04.P9d", "Q04.P10v", "Q04.P11v")
        rc, out, err = self.run_("vcheck", "--test", "dafny/checks/Q04_checks.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, "vcheck: dafny/checks/Q04_checks.dfy [dafny, test]: verified — "
                              "2 passed, 0 failed\nPASSED Q04_Checks.P8\nPASSED Q04_Checks.P9\n")
        rc, out, err = self.run_("vcheck", "--test", "--name", "P9", "dafny/checks/Q04_checks.dfy")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("PASSED Q04_Checks.P9", out)
        self.assertNotIn("P8", out)
        self.rep("dafny/checks/Q04_checks.dfy", "expect Twice(0) == 0;", "expect Twice(0) == 1;")
        rc, out, err = self.run_("vcheck", "--test", "dafny/checks/Q04_checks.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("FAILED Q04_Checks.P9", out)
        rc, out, err = self.run_("vcheck", "--test", "--name", "Nope", "dafny/checks/Q04_checks.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("test-not-run", out)
        rc, out, err = self.run_("vcheck", "--test", CRATE)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, f"vcheck: {CRATE} [verus, test]: verified — 1 passed, 0 failed\n"
                              "PASSED tests::p10\n")


VALUE_SPEC = ("// item: Q04.P21v S2 value\n"
              "// **P21.** What are `double(3)` and `double(4)`? Answer form: numeral\n"
              "use vstd::prelude::*;\n\nverus! {\n\npub open spec fn double(n: nat) -> nat {\n"
              "    n + n\n}\n\nproof fn p21() {\n"
              "    // SLOT: assert(double(3) == 7) by (compute_only);\n"
              "    // SLOT: assert(double(4) == 8) by (compute_only);\n}\n\n} // verus!\n")
OBLIGATION_SPEC = ("// item: Q04.P23d S3 obligation\n"
                   "// **P23.** Which labelled assertions fail? Answer form: `FAILS` and the "
                   "failing labels.\n// SLOT: FAILS none\nmodule Q04_P23 {\n  method M(x: nat)\n"
                   "  {\n    assert NoSuchFunction(x);  // [a]\n  }\n}\n")


class Judges(RootCase):
    """A wrong `by (compute_only)` value fails at the VIR stage on its own line:
    a FAIL, recorded, never "could not run"; the other slots of the run are
    judged once it is commented out. An obligation slot needs a run that
    reached verification: `FAILS none` never passes on a specimen that does
    not resolve. (A git root: its shipped T1dv, unchanged, is no attempt.)"""

    git = True

    def test_compute_only_and_obligation_stage(self):
        (self.root / "specimens/Q04/P21v.rs.specimen").write_text(VALUE_SPEC)
        (self.root / "specimens/Q04/P23d.dfy.specimen").write_text(OBLIGATION_SPEC)
        rc, out, err = self.run_("firsttry.py", "Q04", "--check")
        self.assertEqual(rc, 1, out + err)                  # P23d is refused
        self.assertIn("✗ Q04.P21v  first try fails", out)
        self.assertIn("· Q04.P23d  the check could not run (the specimen stops at stage resolve "
                      "before verification", out)
        rows = [r.split("\t")[:3] for r in
                (self.root / "instructor/calib/Q04.tsv").read_text().splitlines()]
        self.assertEqual(rows, [["Q04.P21v", "predict", "fail"]])
        spec = self.root / "specimens/Q04/P21v.rs.specimen"
        spec.write_text(spec.read_text().replace("// SLOT: ", ""))
        rc, out, err = self.run_("pins.py", "Q04")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("✗ Q04.P21v  specimens/Q04/P21v.rs.specimen:12", out)  # the wrong one only
        self.assertNotIn(":13", out)
        self.assertNotIn("could not run", out)
        spec.write_text(spec.read_text().replace("== 7)", "== 6)"))
        rc, out, err = self.run_("pins.py", "Q04")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("✓ Q04.P21v", out)


DEMO = ("// Card demo Q04.C9d. Open it only after Q04's predictions are recorded.\n"
        "// after: Q04.P4d\n"
        "module Q04_C9 {\n  method Fails(x: nat)\n  {\n    assert x > 1;\n  }\n}\n")


class SealedSidecar(RootCase):
    """A demo that waits for a prediction (`// after:`) gets a sealed sidecar:
    its whole normalized output is one salted hash and no output line is
    shown, its diagnostics included (DV2b)."""

    DEMO = "specimens/Q04/card-c9d.dfy.specimen"

    def test_sealed(self):
        (self.root / self.DEMO).write_text(DEMO)
        rc, out, err = self.run_("pins.py", "--update", self.DEMO, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn(f"wrote expected/{self.DEMO}.expect (sealed for Q04.P4d: one hash, no "
                      "output line)", out)
        sc = self.root / "expected" / f"{self.DEMO}.expect"
        text = sc.read_text()
        for leak in ("exit:", "verdict:", "stage:", "verified:", "holes:",
                     "card-c9d.dfy.specimen:6", "assertion might not hold"):
            self.assertNotIn(leak, text)
        self.assertTrue(text.endswith("\nafter: Q04.P4d\noutcome: salted-sha256 "
                                      + text.rsplit(" ", 1)[1]), text)
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertNotIn("card-c9d", out)                    # the sealed pin matches
        sealed = text
        sc.write_text(sealed + "card-c9d.dfy.specimen:6:12: error: assertion might not hold\n")
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)                  # the pre-DV2b form shows text
        self.assertIn(f"expected/{self.DEMO}.expect: a sealed sidecar that still shows 1 output "
                      "line(s) (the pre-DV2b form): re-pin", out)
        self.assertNotIn(f"{self.DEMO}: golden mismatch", out)   # its hash still matches
        sc.write_text(sealed)
        self.rep(self.DEMO, "assert x > 1;", "assert x >= 0;")   # it verifies now
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{self.DEMO}: golden mismatch: the sealed output differs", out)
        self.assertNotIn("assertion might not hold", out)    # locations only
        sc.write_text(C.load_script("pins").render_sidecar(self.DEMO, "verify", ["exit: 0"]))
        rc, out, err = self.run_("pins.py", "--ci", env={"CI": "true"})
        self.assertIn(f"expected/{self.DEMO}.expect: an unsealed sidecar of a demo that waits for "
                      "Q04.P4d", out)


TOUT = ("  // item: Q04.T1dv S5\n"
        "  // ### T1dv · S5 — Write `function Inc(n: nat): nat`, which adds one. Then uncomment\n"
        "  //    the check below it.\n"
        "\n"
        "  // Uncomment as you go:\n"
        "  // lemma IncCheck()\n"
        "  //   ensures Inc(2) == 3\n"
        "  // {\n"
        "  // }\n")


# The P items of the synthetic Q04 with the tools overlay: a T item's first try
# waits for all of them (QPLAN §6 Q23).
P_ITEMS = tuple(f"Q04.P{n}" for n in ("1dv", "2dv", "3d", "4d", "5d", "6v", "7v", "8d", "9d",
                                      "10v", "11v"))


def tout_root():
    """A Q04 root whose T1dv is a prompt-as-heading test-out, as shipped."""
    root = C.build_root(git=False)
    C.replace_in(root / STD, "  // item: Q04.T1dv S5\n  const T1 := 0\n", TOUT)
    g = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True,  # noqa: E731
                                  capture_output=True, text=True)
    g("init", "-q", "-b", "main")
    g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
    g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m", "shipped")
    g("switch", "-q", "-c", "work")
    return root


class CodeTestOut(unittest.TestCase):
    """A code T item's first try: the first --check at which its block is
    complete, its commented checks enabled in a scratch copy (QPLAN §6 Q4)."""

    def run_in(self, root, *args):
        return C.tool("firsttry.py", "Q04", *args, root=root)

    def test_first_try_predict_then_observed(self):
        root = tout_root()
        self.addCleanup(C.remove_root, root)
        C.replace_in(root / STD, "  // Uncomment as you go:",
                     "  function Inc(n: nat): nat { n + 2 }\n\n  // Uncomment as you go:")
        # Q04 is moderate: the T item waits for every P item (QPLAN §6 Q23)
        rc, out, err = self.run_in(root, "--check")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("· Q04.T1dv  waits for the module's predictions (11 P item(s) unrecorded: "
                      "Q04.P1dv Q04.P2dv Q04.P3d", out)
        self.assertFalse((root / "instructor/calib/Q04.tsv").exists())
        calib(root, *P_ITEMS)
        rc, out, err = self.run_in(root, "--check")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("✗ Q04.T1dv  first try fails (test-out: its checks enabled in a scratch "
                      "copy)", out)
        self.assertIn("  // lemma IncCheck()", (root / STD).read_text())   # never edits the file
        C.replace_in(root / STD, "n + 2", "n + 1")
        rc, out, err = self.run_in(root, "--check")
        self.assertIn("= Q04.T1dv  first try already recorded", out)
        rows = [r.split("\t")[:3] for r in
                (root / "instructor/calib/Q04.tsv").read_text().splitlines()]
        self.assertEqual(rows[len(P_ITEMS):], [["Q04.T1dv", "predict", "fail"]])
        rc, out, err = self.run_in(root, "--report")
        self.assertIn("Q04.T1dv  test-out: attempted · first try ✗", out)
        self.assertIn("test-out: 0/1 recorded code T item(s) passed on the first try", out)
        # a second learner: the right code, but the check uncommented first
        root2 = tout_root()
        self.addCleanup(C.remove_root, root2)
        C.replace_in(root2 / STD, "  // Uncomment as you go:\n  // lemma IncCheck()\n"
                     "  //   ensures Inc(2) == 3\n  // {\n  // }\n",
                     "  function Inc(n: nat): nat { n + 1 }\n\n  // Uncomment as you go:\n"
                     "  lemma IncCheck()\n    ensures Inc(2) == 3\n  {\n  }\n")
        calib(root2, *P_ITEMS)
        rc, out, err = self.run_in(root2, "--check")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("· Q04.T1dv  observed ✓ (not a first try", out)
        rows = [r.split("\t")[:3] for r in
                (root2 / "instructor/calib/Q04.tsv").read_text().splitlines()]
        self.assertEqual(rows[len(P_ITEMS):], [["Q04.T1dv", "observed", "pass"]])


PLANTED = ("// item: Q04.P20d S12 verdict\n"
           "// **P20.** A delivery. Answer form: `<species> <instrument>`, in slots/Q04.slots.\n"
           "// SLOT: CHECK P20d\n"
           "module Q04_P20 {\n  lemma Step(x: nat)\n    ensures x + 0 == x\n  {\n"
           "    assume {:axiom} x + 0 == x;  // planted: Q04.P20d\n  }\n}\n")


class PlantedInstruments(RootCase):
    """The planted marker exempts nothing from the instruments: vaudit (and
    the gate's audit half) still report the planted leap."""

    def test_vaudit_reports_the_planted_line(self):
        p = self.root / "MODULES.toml"
        p.write_text(p.read_text().replace('strands = ["S1", "S2", "S3", "S4", "S5"]',
                                           'strands = ["S1", "S2", "S3", "S4", "S5", "S12"]', 1))
        self.rep("slots/Q04.slots", "P2dv = ???\n", "P2dv = ???\nP20d = ???\n")
        spec = "specimens/Q04/P20d.dfy.specimen"
        (self.root / spec).write_text(PLANTED)
        rc, out, err = self.run_("firsttry.py", "Q04", "--lint-hollow")
        self.assertEqual(rc, 0, out + err)                   # the shipping lint honours it
        calib(self.root, "Q04.P20d")
        rc, out, err = self.run_("vaudit", spec)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{spec}:8: ", out)
        self.assertIn("assume-axiom", out)



# =====================================================================================
# Chapter fences (DV2b): pins.py --update --chapter / --chapter on real runs
# =====================================================================================

CH = "docs/Q04_ProofCraft.md"
F3 = "```"
CH_TEXT = f"""# Q04 — Proof craft, loops and libraries

An invented chapter for the tools suites.

{F3}dafny
method Probe(x: nat)
{{
  assert x > 1;
}}
{F3}

<!-- pin: probe -->
{F3}
{F3}

The plain binary on the same file:

<!-- pin: raw -->
{F3}
{F3}

The demo, once P4d is recorded:

<!-- pin: demo -->
{F3}
{F3}
"""
CH_TOML = """schema = 1

[[entry]]
id = "probe"
cmd = ["scripts/vcheck", "--module", "Q04", "probe.dfy"]
cwd = "scratch"
[entry.normalize]
drop = ["^raw output: "]
[entry.scratch."probe.dfy"]
fence = "above"

[[entry]]
id = "raw"
cmd = ["dafny", "verify", "probe.dfy"]
cwd = "scratch"
[entry.normalize]
exit = true
[entry.scratch."probe.dfy"]
fence = "above"

[[entry]]
id = "demo"
cmd = ["scripts/vcheck", "specimens/Q04/card-c9d.dfy.specimen"]
[entry.normalize]
drop = ["^raw output: "]
"""


class ChapterPinsTool(RootCase):
    """Chapter fences captured from real runs of the pinned tools: a scratch
    probe through the wrapper, the plain binary on the same source, and an
    `after:` demo (run with its guard lifted, as a recorded learner sees it)."""

    def setUp(self):
        super().setUp()
        (self.root / "docs").mkdir()
        (self.root / CH).write_text(CH_TEXT)
        (self.root / "expected").mkdir(exist_ok=True)
        (self.root / "expected" / "Q04.chapter.toml").write_text(CH_TOML)
        (self.root / SealedSidecar.DEMO).write_text(DEMO)

    def check(self, env=None):
        return self.run_("pins.py", "--chapter", "Q04", env=env)

    def test_capture_and_check_real_runs(self):
        rc, out, err = self.run_("pins.py", "--update", "--chapter", "Q04", env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        text = (self.root / CH).read_text()
        self.assertNotIn(str(self.root), text)
        self.assertNotIn("/tmp/", text)                      # scratch paths redacted
        self.assertIn("<!-- pin: probe -->\n```\n$ scripts/vcheck --module Q04 probe.dfy\n"
                      "vcheck: probe.dfy [dafny", text)
        self.assertIn("<!-- pin: raw -->\n```\n$ dafny verify probe.dfy\n", text)
        self.assertRegex(text, r"probe\.dfy\(3,\d+\): Error")       # the plain binary's form
        self.assertRegex(text, r"\n\$ echo \$\?\n[1-9]\d*\n```\n\nThe demo")
        self.assertIn("<!-- pin: demo -->\n```\n$ scripts/vcheck specimens/Q04/card-c9d.dfy."
                      "specimen\n", text)
        self.assertNotIn("first try is not recorded", text)  # guards open: the recorded view
        rc, out, err = self.check({"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 3 pin(s) checked; 0 problem(s)", out)
        # outside the author's context the demo waits for P4d: not run (H5)
        rc, out, err = self.check()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 1 pin(s) not run", out)
        self.assertIn("pins --chapter Q04: 2 pin(s) checked; 0 problem(s)", out)
        calib(self.root, "Q04.P4d")
        rc, out, err = self.check()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 3 pin(s) checked; 0 problem(s)", out)
        # the source fence changes: both scratch entries are stale
        self.rep(CH, "  assert x > 1;\n", "  assert x >= 0;\n")
        rc, out, err = self.check({"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(out.count("stale: 1 input(s) changed since the capture (scratch:probe.dfy;"),
                         2, out)
        rc, out, err = self.check()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 2 pin(s) skipped", out)
        rc, out, err = self.run_("pins.py", "--update", "--chapter", "Q04", "--entry", "probe",
                                 "--entry", "raw", env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("vcheck: probe.dfy [dafny, learner loop]: verified", (self.root / CH)
                      .read_text())
        # the output drifts from the fence (here: the normalization changed):
        # a mismatch, by location only
        self.rep("expected/Q04.chapter.toml", "exit = true\n", "exit = false\n")
        rc, out, err = self.check({"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertRegex(out, rf"{CH}:\d+: pin raw: the fence differs from the captured output at "
                              r"fence line \d+ \(\d+ line\(s\) in the fence, \d+ captured\)")
        self.assertNotIn("echo", out)
        self.assertNotIn("verified", out.replace("pin(s) checked", ""))

if __name__ == "__main__":
    unittest.main()
