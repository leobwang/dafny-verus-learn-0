"""dvl.dafny against the pinned Dafny 4.11.0 on tiny invented programs.

Every expected value below was captured from a real run on 2026-10-04 (the
fixtures are in fixtures/dafny/). Each Dafny job runs under the 8 GB cgroup
cap of dvl.common.run_capped with --cores 2; jobs run one at a time unless
DVL_DAFNY_JOBS says otherwise (CLAUDE.md §Resources). A missing or broken
toolchain fails the suite in setUpModule: these tests never skip their tool.

Run: python3 -m unittest discover -s tests/wrappers -p 'test_dafny*.py'
"""

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402
from dvl import dafny as D  # noqa: E402

FX = ROOT / "tests/wrappers/fixtures/dafny"
ARMED = ROOT / "tests/course_map/armed"


def setUpModule():
    common.toolchain("dafny", fresh=True)   # raises ToolchainError: the suite fails, loudly


def fx(name):
    return str(FX / name)


def holes_of(r):
    return [(h.line, h.col, h.kind, h.label) for h in r.holes]


def kinds(findings):
    return sorted(f.kind for f in findings)


class Verify(unittest.TestCase):
    def test_hole_free_file(self):
        for gate in (False, True):
            r = D.verify(fx("ok.dfy"), gate=gate)
            self.assertEqual((r.verdict, r.stage, r.exit_code, r.verified_count),
                             ("verified", "verify", 0, 2))
            self.assertEqual(r.per_symbol, {"Fx_Ok.Double": "verified",
                                            "Fx_Ok.DoubleGrows": "verified"})
            self.assertEqual((r.holes, r.findings), ([], []))

    def test_pinned_command_line(self):
        r = D.verify(fx("ok.dfy"), gate=True)
        tc = common.toolchain("dafny")
        cmd = r.cmd
        self.assertEqual(cmd[:2], [str(tc["dafny"]), "verify"])
        for flag, value in (("--resource-limit", "5000000"), ("--cores", "2"),
                            ("--solver-path", str(tc["dafny_z3"])), ("--allow-axioms", "false"),
                            ("--allow-warnings", "false")):
            self.assertEqual(cmd[cmd.index(flag) + 1], value)
        self.assertNotIn("--find-project", cmd)
        loop = D.verify(fx("ok.dfy")).cmd
        self.assertEqual(loop[loop.index("--allow-warnings") + 1], "--log-format")
        self.assertTrue((Path(r.raw_dir) / "stdout.txt").is_file())

    def test_holes_counted_by_exact_wording_and_position(self):
        r = D.verify(fx("holes.dfy"))
        self.assertEqual((r.verdict, r.exit_code, r.verified_count), ("verified", 0, 4))
        self.assertEqual(holes_of(r), [(9, 5, "assume", "Fx_Holes.HoleAssume"),
                                       (19, 20, "bodyless-method", "Q04.H1d"),
                                       (23, 20, "bodyless-method", "Q04.H2d"),
                                       (24, 20, "bodyless-method", "Q04.H2d"),
                                       (28, 29, "bodyless-function", "Q04.H3d")])
        self.assertEqual([d.code for d in r.diagnostics],
                         ["W-D03", "W-D01", "W-D01", "W-D01", "W-D02"])
        g = D.verify(fx("holes.dfy"), gate=True)
        self.assertEqual((g.verdict, g.stage, g.exit_code), ("failed", "verify", 2))
        self.assertEqual(kinds(g.findings), ["warnings-fail-gate"])
        self.assertEqual(holes_of(g), holes_of(r))

    def test_holes_function_matches_verify(self):
        self.assertEqual([(h.line, h.col, h.kind, h.label) for h in D.holes(fx("holes.dfy"))],
                         holes_of(D.verify(fx("holes.dfy"))))
        self.assertEqual(D.holes(fx("ok.dfy")), [])

    def test_failing_proofs(self):
        r = D.verify(fx("fails.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code, r.verified_count),
                         ("failed", "verify", 4, 2))
        self.assertEqual(r.per_symbol, {"Fx_Fails.Inc": "verified", "Fx_Fails.Good": "verified",
                                        "Fx_Fails.Bad": "failed", "Fx_Fails.BadAssert": "failed"})
        self.assertEqual([(d.line, d.col, d.severity, d.code) for d in r.diagnostics],
                         [(12, 3, "error", "W-D10"), (11, 20, "related", "W-D10"),
                          (17, 5, "error", "W-D09")])   # a related location follows its error
        self.assertTrue(all(d.file == str((FX / "fails.dfy").resolve()) for d in r.diagnostics))

    def test_silent_kinds_pass_the_tool_and_need_the_lint(self):
        """Δ3: the silent kinds verify green, even in the gate, with no hole."""
        r = D.verify(fx("silent.dfy"), gate=True)
        self.assertEqual((r.verdict, r.exit_code, r.verified_count, r.holes),
                         ("verified", 0, 2, []))
        self.assertEqual(D.holes(fx("silent.dfy")), [])
        self.assertEqual(len(D.lint([fx("silent.dfy")], "learner")), 12)

    def test_loud_non_hole_warning(self):
        r = D.verify(fx("loud.dfy"))
        self.assertEqual((r.verdict, r.verified_count, kinds(r.findings)),
                         ("verified", 0, ["nothing-verified"]))
        self.assertEqual([d.code for d in r.diagnostics], ["W-D15"])
        self.assertEqual(D.holes(fx("loud.dfy")), [])
        g = D.verify(fx("loud.dfy"), gate=True)
        self.assertEqual((g.verdict, g.exit_code), ("failed", 2))

    def test_doubled_warning_kept_once(self):
        """Δ5: @VerifyOnly warns twice at one position; the wrong lemma is skipped."""
        r = D.verify(fx("only.dfy"))
        self.assertEqual((r.verdict, r.verified_count, r.per_symbol),
                         ("verified", 1, {"Fx_Only.Focus": "verified"}))
        self.assertEqual(D.normalized(r.diagnostics, FX),
                         ["only.dfy:4:3: warning: Members with @VerifyOnly temporarily disable "
                          "the verification of other members in the entire file"])
        raw = (Path(r.raw_dir) / "stdout.txt").read_text()
        self.assertEqual(raw.count("Members with @VerifyOnly"), 2)
        self.assertEqual(D.verify(fx("only.dfy"), gate=True).verdict, "failed")
        self.assertEqual([f.kind for f in D.lint([fx("only.dfy")], "learner")], ["verify-only"])

    def test_resource_counts(self):
        counts = D.resource_counts(D.verify(fx("fails.dfy"), seed=1))
        self.assertEqual(sorted(counts), ["Fx_Fails.Bad", "Fx_Fails.BadAssert", "Fx_Fails.Good",
                                          "Fx_Fails.Inc"])
        self.assertTrue(all(0 < c < 5000000 for c in counts.values()))

    def test_parse_and_resolution_stages(self):
        p = D.verify(fx("parse_error.dfy"), gate=True)
        self.assertEqual((p.verdict, p.stage, p.exit_code, p.verified_count),
                         ("failed", "parse", 2, None))
        r = D.verify(fx("resolve_error.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "resolve", 2))
        self.assertEqual([d.message for d in r.diagnostics], ["unresolved identifier: Undefined"])
        for name in ("parse_error.dfy", "resolve_error.dfy"):
            with self.assertRaises(D.HoleCountError):
                D.holes(fx(name))

    def test_out_of_resource_is_inconclusive(self):
        r = D.verify(fx("oor.dfy"), gate=True)
        self.assertEqual((r.verdict, r.exit_code, r.per_symbol),
                         ("inconclusive", 4, {"Fx_Oor.Hard": "inconclusive"}))
        self.assertEqual([d.code for d in r.diagnostics], ["W-D11"])

    def test_symbol_filter(self):
        r = D.verify(fx("sym.dfy"), symbol="Fx_Sym.Good")
        self.assertEqual((r.verdict, r.verified_count, r.per_symbol),
                         ("verified", 1, {"Fx_Sym.Good": "verified"}))   # not GoodLonger (Δ11)
        self.assertEqual(r.cmd[r.cmd.index("--filter-symbol") + 1], "Fx_Sym.Good.")
        b = D.verify(fx("sym.dfy"), symbol="Fx_Sym.Bad")
        self.assertEqual((b.verdict, b.exit_code, b.per_symbol),
                         ("failed", 4, {"Fx_Sym.Bad": "failed"}))
        n = D.verify(fx("sym.dfy"), symbol="Fx_Sym.Nope")
        self.assertEqual((n.verdict, n.exit_code, n.verified_count, kinds(n.findings)),
                         ("failed", 0, 0, ["symbol-not-verified"]))

    def test_pass_through_filters(self):
        """--filter-position prints W-D08: its count is of assertions (Δ39). A
        pass-through filter that matches nothing exits 0 but fails, as the
        --symbol channel does (Δ11, G8)."""
        r = D.verify(fx("sym.dfy"), extra_args=["--filter-position", "sym.dfy:5"])
        self.assertEqual((r.verdict, r.exit_code, r.verified_count, D.count_unit(r),
                          r.per_symbol, kinds(r.findings)),
                         ("verified", 0, 1, "assertions", {"Fx_Sym.Good": "verified"}, []))
        b = D.verify(fx("sym.dfy"), extra_args=["--filter-position", "sym.dfy:15"])
        self.assertEqual((b.verdict, b.exit_code, b.verified_count, b.per_symbol),
                         ("failed", 4, 0, {"Fx_Sym.Bad": "failed"}))
        for extra in (["--filter-position", "sym.dfy:99"], ["--filter-symbol", "Nope"]):
            n = D.verify(fx("sym.dfy"), extra_args=extra)
            self.assertEqual((n.verdict, n.exit_code, n.verified_count, kinds(n.findings)),
                             ("failed", 0, 0, ["filter-matched-nothing"]), extra)
        for gate, extra in ((True, ["--filter-symbol", "Good"]), (False, ["--boogie", "x"])):
            g = D.verify(fx("sym.dfy"), gate=gate, extra_args=extra)
            self.assertEqual((g.verdict, g.exit_code, g.cmd), ("refused", None, []))

    def test_gate_refuses_filters_and_isolation(self):
        for kw in ({"symbol": "Fx_Sym.Good"}, {"isolate": True}):
            r = D.verify(fx("sym.dfy"), gate=True, **kw)
            self.assertEqual((r.verdict, r.stage, r.exit_code, r.cmd), ("refused", "cli", None, []))

    def test_seeded_runs(self):
        r = D.verify(fx("fails.dfy"), seed=2)
        self.assertEqual(r.cmd[1:6], ["measure-complexity", "--random-seed", "2", "--mutations",
                                      "1"])
        self.assertEqual((r.verdict, r.exit_code, r.verified_count), ("failed", 4, 2))
        g = D.verify(fx("ok.dfy"), gate=True, seed=1)
        self.assertEqual((g.verdict, g.verified_count), ("verified", 2))
        h = D.verify(fx("holes.dfy"), gate=True, seed=1)
        self.assertEqual((h.verdict, h.exit_code, kinds(h.findings)),
                         ("failed", 2, ["warnings-fail-gate"]))

    def test_specimen_maps_back(self):
        r = D.verify(fx("p1.dfy.specimen"))
        self.assertEqual((r.verdict, r.exit_code, r.per_symbol),
                         ("failed", 4, {"Fx_P1.Demo": "failed"}))
        self.assertEqual([(d.file, d.line, d.code) for d in r.diagnostics],
                         [(str((FX / "p1.dfy.specimen").resolve()), 9, "W-D09")])
        self.assertEqual(D.failing_labels(r, FX / "p1.dfy.specimen"), {"b"})   # Δ38

    def test_refusals_run_nothing(self):
        for t in ("projects/poison_base", "projects/poison_solver", "projects/poison_options",
                  "projects/empty_glob", "projects/wrongname/project.toml"):
            r = D.verify(fx(t), gate=True)
            self.assertEqual((r.verdict, r.exit_code, r.raw_dir), ("refused", None, None), t)


class Projects(unittest.TestCase):
    def test_unit_by_file_dir_or_project(self):
        for t in ("projects/unit_ok", "projects/unit_ok/dfyconfig.toml",
                  "projects/unit_ok/unit.dfy"):
            r = D.verify(fx(t), gate=True)
            self.assertEqual((r.verdict, r.verified_count), ("verified", 2), t)
            self.assertEqual(r.cmd[2], str((FX / "projects/unit_ok/dfyconfig.toml").resolve()))

    def test_command_line_beats_the_project(self):
        """Δ10: the project says resource-limit = 100; the wrapper's pin wins."""
        r = D.verify(fx("projects/cli_wins"), gate=True)
        self.assertEqual((r.verdict, r.verified_count), ("verified", 2))
        tc = common.toolchain("dafny")
        rc, so, _ = common.run_capped(
            [str(tc["dafny"]), "verify", str((FX / "projects/cli_wins/dfyconfig.toml").resolve()),
             "--cores", "2", "--solver-path", str(tc["dafny_z3"]), "--show-snippets", "false"],
            8, 600, pool="dafny")
        self.assertEqual(rc, 4)
        self.assertIn("Dafny program verifier finished with 0 verified, 0 errors, "
                      "2 out of resource", so.read_text())


class Audit(unittest.TestCase):
    def test_hole_free(self):
        self.assertEqual(D.audit(fx("ok.dfy")), [])

    def test_audit_plus_lint(self):
        """Δ4: audit rows plus the lint for what audit misses."""
        got = [(f.line, f.kind) for f in D.audit(fx("silent.dfy"))]
        self.assertEqual(got, [(4, "audit-bodyless-compiled"), (4, "bodyless-silent"),
                               (6, "bodyless-silent"), (9, "audit-bodyless-compiled"),
                               (9, "bodyless-silent"), (11, "audit-axiom"),
                               (11, "axiom-attribute"), (18, "assume-axiom"),
                               (18, "audit-assume-axiom"), (21, "audit-decreases-star"),
                               (22, "decreases-star"), (25, "decreases-star"),
                               (34, "expect-outside-test"), (37, "trait"),
                               (38, "audit-bodyless-ghost"), (38, "bodyless-abstract"),
                               (43, "abstract-module"), (44, "bodyless-abstract")])

    def test_loud_holes_are_rows(self):
        self.assertEqual([(f.line, f.kind) for f in D.audit(fx("holes.dfy"))],
                         [(9, "audit-assume"), (18, "audit-bodyless-ghost"),
                          (22, "audit-bodyless-ghost"), (22, "multi-ensures-hole"),
                          (27, "audit-bodyless-compiled")])
        self.assertEqual([(f.line, f.kind) for f in D.audit(fx("loud.dfy"))],
                         [(3, "audit-verify-false"), (3, "verify-false")])

    def test_frozen_spec_in_the_given_role(self):
        """Δ44: an abstract spec that the same program refines in full is a
        finding in a learner file and none in the given role."""
        f = fx("given/refined.dfy")
        self.assertEqual(D.verify(f, gate=True).verdict, "verified")
        self.assertEqual(sorted(set(kinds(D.audit(f)))),
                         ["abstract-module", "bodyless-abstract", "uninitialized-const"])
        self.assertEqual(D.audit(f, lint_mode="given"), [])
        with self.assertRaises(ValueError):
            D.audit(f, lint_mode="loose")

    def test_unrunnable_audit_is_a_finding(self):
        self.assertEqual(kinds(D.audit(fx("projects/poison_base"))), ["refused"])
        got = kinds(D.audit(fx("parse_error.dfy")))
        self.assertIn("audit-error", got)


class GivenLayerInTree(unittest.TestCase):
    """A course tree's given layer gets the given role by its path: vaudit's
    default audit of it reports a fully refined frozen spec as nothing."""

    @classmethod
    def setUpClass(cls):
        cls.root = common.scratch_dir("dafny-given-tree") / "root"
        (cls.root / "dafny/given/Q").mkdir(parents=True)
        (cls.root / "MODULES.toml").write_text("schema = 1\n", encoding="utf-8")
        shutil.copytree(ROOT / "dafny/options", cls.root / "dafny/options")
        text = (FX / "given/refined.dfy").read_text(encoding="utf-8")
        cls.given = cls.root / "dafny/given/Q/QG_L1_FxSpec.dfy"
        cls.given.write_text(text, encoding="utf-8")
        cls.probe = cls.root / "probes/QG_L1_FxSpec.dfy"
        cls.probe.parent.mkdir()
        cls.probe.write_text(text, encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root.parent, ignore_errors=True)

    def test_given_layer(self):
        self.assertEqual([Path(f).name for f in D.program(self.given).files],
                         ["QG_L1_FxSpec.dfy"])
        self.assertEqual(D.verify(self.given, gate=True).verdict, "verified")
        self.assertEqual(D.audit(self.given), [])

    def test_same_text_elsewhere_in_the_tree(self):
        self.assertEqual(sorted(set(kinds(D.audit(self.probe)))),
                         ["abstract-module", "bodyless-abstract", "uninitialized-const"])


class Tests(unittest.TestCase):
    def test_all_tests(self):
        r = D.test(fx("tests.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "test", 3))
        self.assertEqual(r.per_symbol, {"Fx_Tests.PassOne": "passed",
                                        "Fx_Tests.FailOne": "failed",
                                        "Fx_Tests.PassTwo": "passed"})   # {:tset} never ran
        self.assertEqual([(d.line, d.message) for d in r.diagnostics],
                         [(2, "Test failures occurred: see above."), (11, "two doubled")])
        self.assertTrue(all(d.file == str((FX / "tests.dfy").resolve()) for d in r.diagnostics))

    def test_named_tests_and_misspelled_attribute(self):
        r = D.test(fx("tests.dfy"), names=["PassOne", "Fx_Tests.PassTwo"])
        self.assertEqual((r.verdict, r.exit_code, r.per_symbol),
                         ("verified", 0, {"Fx_Tests.PassOne": "passed",
                                          "Fx_Tests.PassTwo": "passed"}))
        self.assertEqual(r.cmd[r.cmd.index("--methods-to-test") + 1],
                         r"^(?:(?:.*\.)?PassOne|Fx_Tests\.PassTwo)$")
        t = D.test(fx("tests.dfy"), names=["NeverRuns"])
        self.assertEqual((t.verdict, t.exit_code, kinds(t.findings)),
                         ("failed", 0, ["no-tests", "test-not-run"]))

    def test_printing_tests(self):
        """A test's own output sits between "<Name>: " and its status, glued to it
        when the output ends without a newline (DV2b-2; the raw stdout is
        fixtures/dafny/captured/test_print_all.txt)."""
        r = D.test(fx("tests_print.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code, r.findings), ("failed", "test", 3, []))
        self.assertEqual(r.per_symbol, {"Fx_PrintTests.PrintsThenPasses": "passed",
                                        "Fx_PrintTests.PrintsThenFails": "failed",
                                        "Fx_PrintTests.PrintsNoNewline": "passed",
                                        "Fx_PrintTests.Quiet": "passed"})
        self.assertEqual([(d.line, d.message) for d in r.diagnostics],
                         [(3, "Test failures occurred: see above."), (14, "two doubled")])

    def test_no_tests_is_not_a_pass(self):
        r = D.test(fx("ok.dfy"))
        self.assertEqual((r.verdict, r.exit_code, kinds(r.findings)),
                         ("failed", 0, ["no-tests"]))

    def test_exec_hole_stops_compilation(self):
        r = D.test(fx("exec_hole.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "compile", 3))
        self.assertEqual([d.code for d in r.diagnostics if d.severity == "error"], ["W-D06"])

    def test_exec_holes_that_compile(self):
        """Δ2 (DV0-REPORT §8 item 7): an `assume false;` body is one counted hole
        that compiles under the learner loop; unrelated tests still run."""
        r = D.test(fx("exec_hole_compiles.dfy"))
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "test", 3))
        self.assertEqual(r.per_symbol, {"Fx_ExecHoles.UsesInc": "failed",
                                        "Fx_ExecHoles.UsesTwice": "failed",
                                        "Fx_ExecHoles.Unrelated": "passed"})
        self.assertEqual([(h.line, h.col, h.kind, h.label)
                          for h in D.holes(fx("exec_hole_compiles.dfy"))],
                         [(9, 5, "assume", "Fx_ExecHoles.Inc"),
                          (15, 5, "assume", "Fx_ExecHoles.Twice"),
                          (19, 19, "bodyless-method", "Fx_ExecHoles.ProofHole")])

    def test_compiles_only_in_scratch(self):
        """Δ32: no <stem>-py/ ever lands beside a source, and the scratch copy is
        gone afterwards (only the run's logs stay)."""
        r = D.test(fx("tests.dfy"))
        self.assertEqual(sorted(p.name for p in FX.glob("*-py")), [])
        raw = Path(r.raw_dir)
        self.assertEqual(sorted(p.name for p in raw.iterdir()),
                         ["cmd.txt", "exit.txt", "stderr.txt", "stdout.txt"])


class EmptyBody(unittest.TestCase):
    def test_hole_that_needs_its_lever(self):
        r = D.empty_body(fx("eb.dfy"), "Q09.H1d")
        self.assertEqual(r.verdict, "failed")    # the empty body fails as shipped: a real hole
        self.assertEqual(r.per_symbol, {"maxauto": "verified", "shipped:seed=1": "failed",
                                        "shipped:seed=2": "failed", "shipped:seed=3": "failed"})
        self.assertEqual(kinds(r.findings), ["lever-needed"])
        self.assertEqual(D.empty_body(fx("eb.dfy"), "Fx_Eb.SumClosed").per_symbol, r.per_symbol)

    def test_hole_at_maximal_automation(self):
        r = D.empty_body(fx("eb.dfy"), "Q09.H2d")
        self.assertEqual((r.verdict, r.findings), ("failed", []))
        self.assertEqual(set(r.per_symbol.values()), {"failed"})

    def test_not_a_hole(self):
        r = D.empty_body(fx("eb.dfy"), "Q09.H3d")
        self.assertEqual(r.verdict, "verified")  # the gate rejects the item
        self.assertEqual(set(r.per_symbol.values()), {"verified"})

    def test_unknown_item(self):
        self.assertEqual(D.empty_body(fx("eb.dfy"), "Q09.H9d").verdict, "refused")
        self.assertEqual(D.empty_body(fx("eb.dfy"), "Nope").verdict, "refused")

    def test_sources_untouched_and_no_copies_left(self):
        before = (FX / "eb.dfy").read_bytes()
        r = D.empty_body(fx("eb.dfy"), "Q09.H2d")
        self.assertEqual((FX / "eb.dfy").read_bytes(), before)
        self.assertEqual(list(Path(r.raw_dir).rglob("*.dfy")), [])
        self.assertEqual(sorted(p.name for p in Path(r.raw_dir).iterdir()),
                         ["maxauto", "shipped-seed1", "shipped-seed2", "shipped-seed3"])


class EmptyBodyRegions(unittest.TestCase):
    """QPLAN §6 Q18: a `function … by method` item keeps its function body and
    loses its method body; the region mode blanks a twin's learner regions."""

    def test_by_method_item(self):
        r = D.empty_body(fx("eb_regions.dfy"), "Q09.H4d")
        self.assertEqual((r.verdict, r.findings), ("failed", []))
        self.assertEqual(r.per_symbol, {"maxauto": "failed", "shipped:seed=1": "failed",
                                        "shipped:seed=2": "failed", "shipped:seed=3": "failed"})

    def test_region_mode(self):
        self.assertEqual(D.verify(fx("eb_regions.dfy")).verdict, "verified")
        for item in ("Q09.H4d", "Q09.H5d"):       # a by-method loop's invariants; a header clause
            r = D.empty_body(fx("eb_regions.dfy"), item, regions=True)
            self.assertEqual((r.verdict, r.findings), ("failed", []), item)
            self.assertEqual(set(r.per_symbol), {"region-maxauto", "region-shipped:seed=1",
                                                 "region-shipped:seed=2", "region-shipped:seed=3"})
        r = D.empty_body(fx("eb_regions.dfy"), "Q09.H6d", regions=True)   # a needless assertion
        self.assertEqual(r.verdict, "verified")
        self.assertEqual(set(r.per_symbol.values()), {"verified"})
        self.assertEqual(D.empty_body(fx("eb_regions.dfy"), "Q09.H6d").verdict, "failed")

    def test_region_refusals(self):
        for target, sym, why in (
                ("eb_regions.dfy", "Fx_EbRegions.Twice", "the region mode takes an item id"),
                ("eb.dfy", "Q09.H2d", "no @hole-begin/@hole-end region")):
            r = D.empty_body(fx(target), sym, regions=True)
            self.assertEqual(r.verdict, "refused")
            self.assertIn(why, r.findings[0].message)


class Freeze(unittest.TestCase):
    def check(self, name):
        return [(Path(f.file).name, f.line, f.kind)
                for f in D.freeze_check(fx("freeze/spec.dfy"), fx(f"freeze/{name}.dfy"))]

    def test_good_refinement(self):
        self.assertEqual(self.check("good"), [])

    def test_weakened_statement(self):
        self.assertEqual(self.check("weak"), [("weak.dfy", 6, "freeze-refinement")])

    def test_added_requires(self):
        self.assertEqual(self.check("addreq"), [("addreq.dfy", 4, "freeze-refinement")])

    def test_unrefined_statement(self):
        self.assertEqual(self.check("missing"), [("missing.dfy", 2, "freeze-not-concrete"),
                                                 ("spec.dfy", 8, "freeze-not-concrete")])

    def test_detached_module(self):
        self.assertEqual(self.check("detached"), [("detached.dfy", 0, "freeze-detached")])

    def test_axiom_child(self):
        self.assertEqual(self.check("axiom"), [("axiom.dfy", 3, "axiom-attribute"),
                                               ("axiom.dfy", 3, "bodyless-silent"),
                                               ("axiom.dfy", 3, "freeze-not-concrete")])


class ArmedUnits(unittest.TestCase):
    """The synthetic armed Q04 of tests/course_map/armed, in a scratch course root
    with generated units (scripts/gen_units.py)."""

    @classmethod
    def setUpClass(cls):
        import test_course_map as tcm  # the checker suite's armed registry text
        cls.root = common.scratch_dir("dafny-armed") / "root"
        (cls.root / "dafny").mkdir(parents=True)
        (cls.root / "MODULES.toml").write_text(tcm.ARMED, encoding="utf-8")
        shutil.copytree(ROOT / "dafny/options", cls.root / "dafny/options")
        for rel, text in tcm.TREE.items():
            p = cls.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        p = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/gen_units.py"), "--root",
                            str(cls.root)], capture_output=True, text=True)
        assert p.returncode == 0, p.stdout + p.stderr
        cls.unit = cls.root / "dafny/Q/Q04_ProofCraft"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root.parent, ignore_errors=True)

    def test_core_unit(self):
        for t in (self.unit / "core", self.unit / "core/Q04_ProofCraft.dfy"):
            r = D.verify(t)
            self.assertEqual((r.verdict, r.verified_count), ("verified", 2))
            self.assertEqual(holes_of(r), [(19, 19, "bodyless-method", "Q04.H1d")])
            self.assertEqual(r.cmd[2], str(self.unit / "core/dfyconfig.toml"))

    def test_std_unit(self):
        r = D.verify(self.unit / "std", gate=True)
        self.assertEqual((r.verdict, r.exit_code), ("failed", 2))
        self.assertEqual(holes_of(r), [(9, 19, "bodyless-method", "Q04.H2d")])
        self.assertEqual([(Path(f.file).name, f.line, f.kind) for f in D.audit(self.unit / "std")],
                         [("Q04_Library.dfy", 8, "audit-bodyless-ghost")])

    def test_exit_file_gets_its_chain_and_unit_options(self):
        prog = D.program(self.unit / "exit/Q04_Exit.dfy")
        self.assertEqual([Path(f).name for f in prog.files],
                         ["Q04_Exit.dfy", "QG_L1_BigNat.dfy", "QG_L2_BigNat.dfy"])
        r = D.verify(self.unit / "exit/Q04_Exit.dfy")
        self.assertIn("--manual-lemma-induction", r.cmd)
        self.assertEqual([(h.line, h.label) for h in r.holes], [(7, "Q04.X1d"), (13, "Q04.X2d")])

    def test_given_layers_verify_with_their_chain(self):
        for rel, files, std in (("QG_L1_BigNat.dfy", ["QG_L1_BigNat.dfy"], False),
                                ("QG_L3_BigNat.dfy", ["QG_L3_BigNat.dfy", "QG_L1_BigNat.dfy",
                                                      "QG_L2_BigNat.dfy"], True)):
            t = self.root / "dafny/given/Q" / rel
            prog = D.program(t)
            self.assertEqual(([Path(f).name for f in prog.files], prog.std), (files, std))
            self.assertEqual(D.verify(t, gate=True).verdict, "verified")

    def test_checks_file_runs_value_tests(self):
        """Δ43: a given-only check unit (design §14.1 dafny/checks/)."""
        f = self.root / "dafny/checks/Q04_checks.dfy"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("module Q04_Checks {\n  import opened QG_L1_BigNat\n"
                     "  import opened QG_L2_BigNat\n"
                     "  @Test\n  method P2() {\n    expect TWICE == 2 * BASE;\n  }\n}\n",
                     encoding="utf-8")
        try:
            r = D.test(f, names=["P2"])
            self.assertEqual((r.verdict, r.per_symbol), ("verified", {"Q04_Checks.P2": "passed"}))
            self.assertEqual([Path(x).name for x in D.program(f).files],
                             ["Q04_checks.dfy", "QG_L1_BigNat.dfy", "QG_L2_BigNat.dfy"])
        finally:
            f.unlink()

    def test_core_unit_cannot_reach_a_std_layer(self):
        """Δ34, Δ78: a core unit's includes stop at the core layers."""
        f = self.unit / "core/Q04_Reach.dfy"
        f.write_text("module Q04_Reach {\n  import opened QG_L3_BigNat\n}\n", encoding="utf-8")
        try:
            r = D.verify(self.unit / "core")
            self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "resolve", 2))
            self.assertIn("module QG_L3_BigNat does not exist",
                          [d.message for d in r.diagnostics if d.severity == "error"][0])
        finally:
            f.unlink()

    def test_unknown_and_edited_projects_are_refused(self):
        stray = self.unit / "exit/dfyconfig.toml"
        stray.write_text((self.unit / "core/dfyconfig.toml").read_text(), encoding="utf-8")
        try:
            r = D.verify(self.unit / "exit/Q04_Exit.dfy")
            self.assertEqual(r.verdict, "refused")
            self.assertIn("unknown dfyconfig.toml", r.findings[0].message)
        finally:
            stray.unlink()
        cfg = self.unit / "core/dfyconfig.toml"
        text = cfg.read_text(encoding="utf-8")
        cfg.write_text(text.replace("manual-lemma-induction = true\n", ""), encoding="utf-8")
        try:
            r = D.verify(self.unit / "core", gate=True)
            self.assertEqual(r.verdict, "refused")
            self.assertIn("edited dfyconfig.toml", r.findings[0].message)
        finally:
            cfg.write_text(text, encoding="utf-8")


class Server(unittest.TestCase):
    def test_server_never_writes_into_the_pinned_install(self):
        """Δ33: the server runs from a scratch copy; the pinned tree stays verified."""
        tc = common.toolchain("dafny")
        pinned = Path(tc["dafny_root"]) / "dafny"
        argv = D.server_argv()
        self.assertNotIn(str(Path(tc["dafny_root"]).resolve()), argv[0])
        rc, _, _ = common.run_capped(argv, 8, 8, pool="dafny")
        self.assertEqual(rc, common.WALL_CLOCK_EXIT)   # a server waits for its client
        logs = list((D.server_install() / "dafny").glob("DafnyLanguageServerLog*"))
        self.assertTrue(logs)
        self.assertEqual(list(pinned.glob("DafnyLanguageServerLog*")), [])
        common.toolchain("dafny", fresh=True)   # get_toolchain.sh --check still passes


if __name__ == "__main__":
    unittest.main()
