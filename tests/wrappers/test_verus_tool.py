"""Tests of dvl.verus that run the pinned Verus (tests/wrappers/fixtures/verus).

Every job runs through dvl.common.run_capped: one cgroup per job capped at the
pinned mem_gb (16G, Δ57), MemorySwapMax=0, and at most DVL_VERUS_JOBS jobs at
once (default 1), so this suite runs one solver job at a time unless told
otherwise (CLAUDE.md §Resources). The fixtures are tiny invented programs;
the whole suite takes about two minutes.

Run:  python3 -m unittest discover -s tests/wrappers -p 'test_verus_tool.py'
      python3 tests/wrappers/test_verus_tool.py --recapture   (re-capture the raw
      outputs the static suite reads, fixtures/verus/captured/)

A missing or unverified toolchain fails these tests (it never skips them):
an empty run must not pass.
"""

import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402
from dvl import verus as V  # noqa: E402

FX = ROOT / "tests/wrappers/fixtures/verus"
CAP = FX / "captured"


def kinds(holes):
    return [(h.line, h.kind, h.label) for h in holes]


def leftovers(raw_dir):
    """Files of a run other than its job logs (<nn>-<step>/{cmd,stdout,stderr,exit}.txt)."""
    raw = Path(raw_dir)
    return sorted(p.relative_to(raw).as_posix() for p in raw.rglob("*")
                  if not (p.is_dir() and re.match(r"\d\d-", p.name) and p.parent == raw) and
                  not re.fullmatch(r"\d\d-[^/]+/(cmd|stdout|stderr|exit)\.txt",
                                   p.relative_to(raw).as_posix()))


def steps(raw_dir):
    return sorted(p.name for p in Path(raw_dir).iterdir())


class Verify(unittest.TestCase):
    def test_clean_gate_passes(self):
        r = V.verify(FX / "clean.rs", gate=True)
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("verified", "verify", 0))
        self.assertEqual(r.verified_count, 2)
        self.assertEqual(r.per_symbol, {"add_one": "verified", "lemma_double": "verified"})
        self.assertEqual((r.holes, r.findings), ([], []))
        self.assertIn("--no-cheating", r.cmd)
        self.assertEqual(r.cmd[r.cmd.index("--rlimit") + 1], str(V.pins()["rlimit"]))
        self.assertEqual(r.cmd[r.cmd.index("--num-threads") + 1], "1")
        for name in ("cmd.txt", "stdout.txt", "stderr.txt", "exit.txt"):
            self.assertTrue(any(Path(r.raw_dir).glob(f"*/{name}")), name)

    def test_gate_minimum_count(self):
        r = V.verify(FX / "clean.rs", gate=True, min_verified=3)
        self.assertEqual(r.verdict, "failed")
        self.assertTrue(any(d.code == "gate" and "verified 2 < the unit's minimum 3" in d.message
                            for d in r.diagnostics))

    def test_holes_beside_a_real_failure(self):
        r = V.verify(FX / "holes.rs")
        self.assertEqual((r.verdict, r.stage, r.exit_code), ("failed", "verify", 1))
        self.assertEqual(kinds(r.holes), [(11, "external_body", "exec_hole"),
                                          (30, "assume", "Q04.H1v"),
                                          (38, "admit", "Q04.H2v")])
        self.assertEqual([(d.line, d.code) for d in r.diagnostics if d.severity == "error"],
                         [(22, "W-V04")])
        self.assertIsNone(r.verified_count)   # a cheat drops `verified` from the JSON (Δ12)
        self.assertEqual(r.per_symbol["really_fails"], "failed")
        self.assertEqual(r.per_symbol["labelled"], "hole")
        g = V.verify(FX / "holes.rs", gate=True)
        self.assertEqual(g.verdict, "failed")
        self.assertTrue(any(d.code == "gate" and "3 hole(s)" in d.message for d in g.diagnostics))

    def test_every_hole_kind(self):
        r = V.verify(FX / "kinds.rs")
        self.assertEqual([h.kind for h in r.holes],
                         ["uninterp", "bodyless_spec", "axiom", "assume_specification",
                          "assume_termination", "external_body", "assume"])
        self.assertIn("W-V18", [d.code for d in r.diagnostics if d.severity == "warning"])
        self.assertEqual(V.holes(FX / "kinds.rs"), r.holes)

    def test_rlimit_is_inconclusive(self):
        r = V.verify(FX / "rlimit.rs")
        self.assertEqual((r.verdict, r.stage, r.verified_count), ("inconclusive", "verify", 1))
        self.assertEqual([d.code for d in r.diagnostics], ["W-V05"])

    def test_stages(self):
        for name, stage, code in (("stages_parse.rs", "parse", ""),
                                  ("stages_type.rs", "resolve", "E0308"),
                                  ("stages_vir.rs", "resolve", "W-V21")):
            r = V.verify(FX / name)
            self.assertEqual((r.verdict, r.stage), ("failed", stage), name)
            self.assertEqual([d.code for d in r.diagnostics if d.severity == "error"], [code])
            with self.assertRaises(V.HoleCountError):
                V.holes(FX / name)

    def test_fast_channel(self):
        r = V.verify(FX / "clean.rs", symbol="lemma_double")
        self.assertEqual((r.verdict, r.per_symbol), ("verified", {"lemma_double": "verified"}))
        self.assertEqual(r.cmd[-3:], ["--verify-root", "--verify-function", "lemma_double"])
        r = V.verify(FX / "holes.rs", symbol="really_fails")
        self.assertEqual((r.verdict, r.per_symbol), ("failed", {"really_fails": "failed"}))
        # a hole elsewhere in the crate drops the counts (Δ12): no error is all we know
        r = V.verify(FX / "chain/tmod", symbol="sub::six")
        self.assertEqual(r.per_symbol, {"sub::six": "no-error"})
        self.assertEqual(r.cmd[-4:], ["--verify-only-module", "sub", "--verify-function", "six"])
        r = V.verify(FX / "chain/tmod", symbol="eight")
        self.assertEqual(r.per_symbol, {"eight": "hole"})
        r = V.verify(FX / "chain/tmod/src/exit.rs", symbol="nine")
        self.assertEqual(r.per_symbol, {"nine": "verified"})
        r = V.verify(FX / "clean.rs", symbol="nosuch")
        self.assertEqual((r.verdict, r.stage), ("failed", "resolve"))

    def test_seed_and_isolate(self):
        r = V.verify(FX / "clean.rs", seed=7)
        self.assertEqual(r.verdict, "verified")
        self.assertIn("smt.random_seed=7", r.cmd)
        r = V.verify(FX / "clean.rs", isolate=True)
        self.assertEqual(r.verdict, "verified")
        self.assertEqual(r.cmd[-2:], ["-V", "spinoff-all"])

    def test_refusals_run_nothing(self):
        for kw in ({"extra_args": ["--no-verify"]}, {"extra_args": ["--rlimit", "20"]},
                   {"extra_args": ["--smt-option", "smt.arith.solver=2"]},
                   {"extra_args": ["-V", "no-solver-version-check"]},
                   {"gate": True, "symbol": "lemma_double"},
                   {"gate": True, "extra_args": ["--expand-errors"]}, {"seed": -1}):
            r = V.verify(FX / "clean.rs", **kw)
            self.assertEqual((r.verdict, r.exit_code, r.raw_dir), ("refused", None, None), kw)
            self.assertEqual([f.kind for f in r.findings], ["refused"])
        r = V.verify(FX / "clean.rs", extra_args=["--expand-errors", "--rlimit", "2"])
        self.assertEqual(r.verdict, "verified")
        self.assertIn("--expand-errors", r.cmd)

    def test_environment_is_scrubbed(self):
        saved = {k: os.environ.get(k) for k in ("VERUS_Z3_PATH", "VERUS_EXTRA_ARGS")}
        os.environ["VERUS_Z3_PATH"] = "/nonexistent/z3"
        os.environ["VERUS_EXTRA_ARGS"] = "--no-verify"
        try:
            r = V.verify(FX / "clean.rs", gate=True)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual((r.verdict, r.verified_count), ("verified", 2))

    def test_wall_clock_kill(self):
        r = V.verify(FX / "hang.rs", timeout_s=10)
        self.assertEqual((r.verdict, r.exit_code), ("inconclusive", common.WALL_CLOCK_EXIT))
        self.assertEqual([d.code for d in r.diagnostics], ["wall-clock-kill"])
        with self.assertRaises(V.HoleCountError):
            V.holes(FX / "hang.rs", timeout_s=10)

    def test_specimen(self):
        spec = FX / "specimens/Q04/P9v.rs.specimen"
        r = V.verify(spec)
        self.assertEqual((r.verdict, r.stage), ("failed", "verify"))
        self.assertEqual([(d.file, d.line, d.code) for d in r.diagnostics],
                         [(str(spec), 13, "W-V04")])
        self.assertEqual(leftovers(r.raw_dir), [])         # the .rs copy is gone

    def test_missing_target(self):
        r = V.verify(FX / "nosuch.rs")
        self.assertEqual((r.verdict, r.exit_code), ("refused", None))


class Chain(unittest.TestCase):
    """Direct layer chains (Δ22, Δ25) on the invented crates tla <- tlb <- tmod."""

    def test_module_crate(self):
        r = V.verify(FX / "chain/tmod")
        self.assertEqual((r.verdict, r.stage), ("verified", "verify"))
        self.assertEqual(kinds(r.holes), [(17, "assume", "Q04.H3v")])
        self.assertEqual(r.per_symbol, {"add_two": "no-error", "eight": "hole",
                                        "sub::six": "no-error"})
        self.assertEqual([r.cmd[i + 1].split("=")[0] for i, a in enumerate(r.cmd)
                          if a == "--import"], ["tla", "tlb"])
        self.assertEqual(steps(r.raw_dir), ["01-dep-tla", "02-dep-tlb", "03-target"])
        self.assertEqual(leftovers(r.raw_dir), [])         # deps/ (.vir, .rlib) is gone
        sub = V.verify(FX / "chain/tmod/src/sub.rs")
        self.assertEqual(sub.cmd[sub.cmd.index("--crate-name") + 1], "tmod")

    def test_file_no_mod_reaches(self):
        r = V.verify(FX / "chain/tmod/src/exit.rs", gate=True)
        self.assertEqual((r.verdict, r.verified_count), ("verified", 1))
        self.assertEqual(r.cmd[r.cmd.index("--crate-name") + 1], "tmod_exit")

    def test_audit(self):
        found = V.audit(FX / "chain/tmod")
        self.assertEqual([(Path(f.file).name, f.line, f.kind) for f in found],
                         [("lib.rs", 17, "hole-assume")])

    def test_tests_beside_holes(self):
        r = V.test(FX / "chain/tmod")
        self.assertEqual((r.verdict, r.stage), ("verified", "test"))
        self.assertEqual(r.per_symbol, {"tests::adds_two": "passed"})
        self.assertEqual(leftovers(r.raw_dir), [])         # no test binary, no deps/


class ArmedQ04(unittest.TestCase):
    """The checker's synthetic armed Q04 tree (tests/course_map/armed/) as the
    unit generator wires it: its given layer crates and the module crate whose
    Cargo.toml scripts/gen_units.py renders (Δ22, Δ78)."""

    @classmethod
    def setUpClass(cls):
        import gen_units
        cls.tmp = Path(tempfile.mkdtemp(prefix="armed-", dir=common.scratch_root()))
        shutil.copytree(ROOT / "tests/course_map/armed/tree/verus", cls.tmp / "verus")
        crate = cls.tmp / "verus/q/q04_proof_craft"
        (crate / "Cargo.toml").write_text(gen_units.render_crate("Q04", "q04_proof_craft", "L3"))
        cls.crate = crate

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_unit(self):
        r = V.verify(self.crate)
        self.assertEqual((r.verdict, r.stage), ("verified", "verify"))
        self.assertEqual([(h.kind, h.label) for h in r.holes],
                         [("assume", "Q04.H1v"), ("assume", "Q04.H2v")])
        steps = sorted(p.name for p in Path(r.raw_dir).iterdir() if p.name[0].isdigit())
        self.assertEqual(steps, ["01-dep-qg_bignat_l1", "02-dep-qg_bignat_l2",
                                 "03-dep-qg_bignat_l3", "04-target"])
        self.assertEqual(V.lint([self.crate], "learner"), [])

    def test_exit_file_gate(self):
        # exit.rs is reached by no `mod`: it is its own crate root on the unit's
        # chain. x1 and x2 (`ensures true`, empty bodies) each count in `verified`.
        r = V.verify(self.crate / "src/exit.rs", gate=True)
        self.assertEqual((r.verdict, r.verified_count), ("verified", 2))
        self.assertEqual(r.per_symbol, {"x1": "verified", "x2": "verified"})
        r = V.verify(self.crate / "src/exit.rs", gate=True, min_verified=3)
        self.assertEqual(r.verdict, "failed")

    def test_specimen_gets_the_layer_chain(self):
        # A specimen under specimens/<ID>/ is verified on its module's given
        # layers (here the armed tree's, standing in for verus/given/).
        spec = FX / "specimens/Q04/P9v.rs.specimen"
        with mock.patch.object(V, "GIVEN_ROOT", self.tmp / "verus/given"):
            r = V.verify(spec)
        self.assertEqual((r.verdict, r.stage), ("failed", "verify"))
        self.assertEqual([(d.file, d.line, d.code) for d in r.diagnostics],
                         [(str(spec), 13, "W-V04")])
        self.assertEqual(steps(r.raw_dir), ["01-dep-qg_bignat_l1", "02-dep-qg_bignat_l2",
                                            "03-dep-qg_bignat_l3", "04-target"])
        self.assertEqual([r.cmd[i + 1].split("=")[0] for i, a in enumerate(r.cmd)
                          if a == "--import"], ["qg_bignat_l1", "qg_bignat_l2", "qg_bignat_l3"])
        self.assertEqual(leftovers(r.raw_dir), [])

    def test_later_layer_from_the_path(self):
        lib = self.crate / "src/lib.rs"
        text = lib.read_text().replace("use qg_bignat_l3::*;", "use qg_bignat_l3::*;\nuse qg_bignat_l4::*;")
        found = V.lint_source(text, str(lib), "learner")
        self.assertEqual([(f.line, f.kind) for f in found], [(4, "later-layer")])


class Audit(unittest.TestCase):
    def test_holes_and_allowlist(self):
        found = V.audit(FX / "holes.rs")
        self.assertEqual([(f.line, f.kind) for f in found],
                         [(11, "hole-external-body"), (30, "hole-assume"), (38, "hole-admit")])
        rel = common.display_path(FX / "holes.rs")
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(V, "TRUST_ROOTS", ("tests/wrappers/fixtures/verus/",)):
            allow = Path(d) / "trust.toml"
            allow.write_text(f'[[trust]]\npath = "{rel}"\nsymbol = "exec_hole"\n'
                             'kind = "external_body"\nreason = "test"\n\n'
                             f'[[trust]]\npath = "{rel}"\nsymbol = "really_fails"\n'
                             'kind = "assume"\nreason = "test"\n')   # a fn with no hole
            found = V.audit(FX / "holes.rs", allowlist=allow)
        self.assertEqual([(f.line, f.kind) for f in found],
                         [(0, "stale-trust-entry"), (30, "hole-assume"), (38, "hole-admit")])

    def test_clean_and_incomplete(self):
        self.assertEqual(V.audit(FX / "clean.rs"), [])
        found = V.audit(FX / "stages_type.rs")
        self.assertEqual([f.kind for f in found], ["audit-incomplete"])

    def test_lint_is_part_of_the_audit(self):
        found = V.audit(FX / "kinds.rs")
        self.assertIn("outside-verus", [f.kind for f in found])
        self.assertEqual(len([f for f in found if f.kind.startswith("hole-")]), 7)


class Trusted(unittest.TestCase):
    """Dependency holes (fixtures/verus/trusted/: tdep <- tuse). Captured on the
    pin: --no-cheating shows a crate each dependency external_body fn it calls
    (once per fn, not per call), never a dependency's assume; such a run drops
    `verified`, `errors` and `is-verifying-entire-crate`."""

    TDEP = FX / "trusted/tdep/src/lib.rs"

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="trust-", dir=common.scratch_root()))
        rel = common.display_path(cls.TDEP)
        entry = ('[[trust]]\npath = "{rel}"\nsymbol = "{sym}"\nkind = "{kind}"\n'
                 'reason = "test"\n\n')
        cls.empty = cls.tmp / "empty.toml"
        cls.empty.write_text("")
        cls.ok = cls.tmp / "ok.toml"
        cls.ok.write_text(entry.format(rel=rel, sym="copy_small", kind="external_body") +
                          entry.format(rel=rel, sym="lemma_trusted", kind="external_body"))
        cls.stale = cls.tmp / "stale.toml"
        cls.stale.write_text(cls.ok.read_text() +
                             entry.format(rel=rel, sym="lemma_assumed", kind="external_body"))
        cls.roots = mock.patch.object(V, "TRUST_ROOTS", ("tests/wrappers/fixtures/verus/trusted/",))
        cls.roots.start()

    @classmethod
    def tearDownClass(cls):
        cls.roots.stop()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def deps(self, r):
        return [(Path(f.file), f.line, f.kind) for f in r.findings]

    def test_dependency_holes_are_not_the_units(self):
        r = V.verify(FX / "trusted/tuse", allowlist=self.empty)
        self.assertEqual((r.verdict, r.stage, r.holes, r.verified_count),
                         ("verified", "verify", [], None))
        self.assertEqual(self.deps(r), [(self.TDEP, 9, "dependency-hole"),
                                        (self.TDEP, 17, "dependency-hole")])
        self.assertEqual(V.holes(FX / "trusted/tuse", allowlist=self.empty), [])
        g = V.verify(FX / "trusted/tuse", gate=True, allowlist=self.empty)
        self.assertEqual(g.verdict, "failed")
        self.assertTrue(any(d.code == "gate" and "2 untrusted dependency hole(s)" in d.message
                            for d in g.diagnostics))

    def test_trusted_dependency_holes_pass_the_gate(self):
        r = V.verify(FX / "trusted/tuse", gate=True, allowlist=self.ok)
        self.assertEqual((r.verdict, r.exit_code, r.verified_count), ("verified", 0, 4))
        self.assertEqual((r.holes, r.findings), ([], []))
        self.assertEqual(r.per_symbol, dict.fromkeys(
            ("use_assumed", "use_copy", "use_copy_again", "use_trusted"), "verified"))
        self.assertEqual([(d.line, d.code) for d in r.diagnostics],
                         [(9, "trusted-dependency-hole"), (17, "trusted-dependency-hole"),
                          (0, "trusted-record")])
        # the hole count ran with --no-cheating; the record without it
        self.assertEqual(steps(r.raw_dir), ["01-dep-tdep", "02-target", "03-target"])
        first = (Path(r.raw_dir) / "02-target/cmd.txt").read_text()
        self.assertIn("--no-cheating", first)
        self.assertNotIn("--no-cheating", r.cmd)
        self.assertEqual(r.cmd, (Path(r.raw_dir) / "03-target/cmd.txt").read_text().split())

    def test_own_hole_beside_a_dependency_hole(self):
        exit_rs = FX / "trusted/tuse/src/exit.rs"
        r = V.verify(exit_rs, allowlist=self.empty)
        self.assertEqual(kinds(r.holes), [(19, "assume", "own_hole")])
        self.assertEqual(self.deps(r), [(self.TDEP, 9, "dependency-hole")])
        self.assertEqual(r.per_symbol, {"copy_twice": "no-error", "own_hole": "hole"})
        r = V.verify(exit_rs, gate=True, allowlist=self.ok)
        self.assertEqual((r.verdict, len(r.holes), r.findings), ("failed", 1, []))
        self.assertEqual(steps(r.raw_dir), ["01-dep-tdep", "02-target"])   # no second run

    def test_audit_reports_each_hole_once(self):
        found = V.audit(FX / "trusted/tuse", allowlist=self.empty)
        self.assertEqual([(Path(f.file), f.line, f.kind) for f in found],
                         [(self.TDEP, 9, "hole-external-body"),
                          (self.TDEP, 17, "hole-external-body"), (self.TDEP, 27, "hole-assume")])
        found = V.audit(FX / "trusted/tuse", allowlist=self.stale)
        self.assertEqual([(Path(f.file), f.line, f.kind) for f in found],
                         [(self.TDEP, 0, "stale-trust-entry"), (self.TDEP, 27, "hole-assume")])

    def test_check_trust(self):
        with mock.patch.object(V, "GIVEN_ROOT", FX / "trusted"):
            found = V.check_trust(self.stale)
            self.assertEqual([(Path(f.file), f.line, f.kind) for f in found],
                             [(self.TDEP, 0, "stale-trust-entry"),
                              (self.TDEP, 27, "hole-assume")])
            self.assertEqual([f.kind for f in V.check_trust(self.empty)],
                             ["hole-external-body", "hole-external-body", "hole-assume"])


class Tests(unittest.TestCase):
    """test(): libtest through `verus --compile --test` (Δ42, Δ11)."""

    def test_all_tests(self):
        r = V.test(FX / "tests.rs")
        self.assertEqual((r.verdict, r.stage, r.verified_count), ("failed", "test", 1))
        self.assertEqual(r.per_symbol, {"tests::add1_ignored": "ignored",
                                        "tests::add1_three": "passed",
                                        "tests::add1_wrong": "failed",
                                        "tests::stub_panics": "failed"})

    def test_named_tests(self):
        self.assertEqual(V.test(FX / "tests.rs", names=["add1_three"]).verdict, "verified")
        for names in (["nosuch"], [], ["add1_three", "add1_wrong"]):
            r = V.test(FX / "tests.rs", names=names)
            self.assertEqual(r.verdict, "failed", names)
        r = V.test(FX / "tests.rs", names=["nosuch"])
        self.assertEqual([d.code for d in r.diagnostics], ["test-not-found"])

    def test_verification_failure_stops_tests(self):
        r = V.test(FX / "holes.rs")
        self.assertEqual((r.verdict, r.stage), ("failed", "verify"))

    def test_a_build_failure_after_verification_names_its_stage(self):
        """A proved crate whose test build fails reports the stage that failed: the native
        linker (link) or rustc's later passes (compile), never verify; verification itself
        stays green (the R13 P5v shape)."""
        for name, stage in (("link_test.rs", "link"), ("lint_test.rs", "compile")):
            with self.subTest(fixture=name):
                self.assertEqual(V.verify(FX / name).verdict, "verified")
                r = V.test(FX / name)
                self.assertEqual((r.verdict, r.stage, r.verified_count), ("failed", stage, 1),
                                 r.diagnostics)
                self.assertEqual(r.per_symbol["sum_thirteen"], "no-error")


class EmptyBody(unittest.TestCase):
    """The empty-body gate (Δ45, Δ47); verdict failed = the hole is real."""

    def test_real_hole_every_mode(self):
        r = V.empty_body(FX / "eb.rs", "Q04.H5v")
        self.assertEqual((r.verdict, r.verified_count), ("failed", 0))
        seeds = [str(s) for s in V.pins()["seeds"]]
        want = {f"{m} seed={s}" for m in ("E0", "E0H", "E1", "E2", "NL", "BV") for s in seeds}
        want.add(f"EM seed={seeds[0]}")
        self.assertEqual(set(r.per_symbol), want)
        for k, v in r.per_symbol.items():
            if k.startswith("BV"):
                self.assertTrue(v.startswith("no-verify("), (k, v))
            else:
                self.assertEqual(v, "fails(error)", k)
        self.assertIn("--rlimit", r.cmd)

    def test_item_that_falls_to_automation(self):
        r = V.empty_body(FX / "eb.rs", "lemma_easy", modes=["E0"], seeds=[1])
        self.assertEqual((r.verdict, r.per_symbol), ("verified", {"E0 seed=1": "verifies"}))
        self.assertEqual([d.code for d in r.diagnostics], ["empty-body"])
        self.assertEqual(leftovers(r.raw_dir), [])         # the variant copy is gone

    def test_exec_item(self):
        r = V.empty_body(FX / "eb_exec.rs", "count_up", seeds=[1])
        self.assertEqual(r.verdict, "failed")
        self.assertEqual(set(r.per_symbol), {f"{m} seed=1" for m in
                                             ("E0", "E0H", "E1", "E2", "EM", "INV", "TRIV")})
        self.assertTrue(all(v == "fails(error)" for v in r.per_symbol.values()), r.per_symbol)

    def test_proof_blocks_after_if_else_reach_verification(self):
        """QPLAN §6 Q9: E0 strips the ghost let and the proof blocks that use it
        (one directly after an if/else, one after the loop), so the variant
        reaches verification and fails there; INV keeps them and drops only
        the invariant. The item as written verifies."""
        self.assertEqual(V.verify(FX / "eb_ghost.rs").verdict, "verified")
        r = V.empty_body(FX / "eb_ghost.rs", "count_big", modes=["E0", "INV"], seeds=[1])
        self.assertEqual(r.per_symbol, {"E0 seed=1": "fails(error)", "INV seed=1": "fails(error)"})
        self.assertEqual(r.verdict, "failed")

    def test_course_group_and_module_item(self):
        r = V.empty_body(FX / "chain/tmod", "sub::six", modes=["E0", "EC"], seeds=[1])
        self.assertEqual(r.verdict, "verified")
        self.assertEqual(r.per_symbol, {"E0 seed=1": "verifies", "EC seed=1": "verifies"})

    def test_region_mode(self):
        """QPLAN §6 Q18: RGN verifies a twin with the item's learner regions
        blanked; it runs only when asked for, and a twin's broken markers
        are refused."""
        self.assertEqual(V.verify(FX / "eb_regions.rs").verdict, "verified")
        r = V.empty_body(FX / "eb_regions.rs", "Q09.H4v", modes=["RGN"], seeds=[1])
        self.assertEqual((r.verdict, r.per_symbol), ("failed", {"RGN seed=1": "fails(error)"}))
        r = V.empty_body(FX / "eb_regions.rs", "Q09.H5v", modes=["RGN"], seeds=[1])
        self.assertEqual((r.verdict, r.per_symbol), ("verified", {"RGN seed=1": "verifies"}))
        # a region holding a loop's whole invariant list: the keyword goes with it, so
        # the variant parses and fails (it used to end in no verdict, Δ137 Open)
        r = V.empty_body(FX / "eb_regions.rs", "Q09.H6v", modes=["RGN"], seeds=[1])
        self.assertEqual((r.verdict, r.per_symbol), ("failed", {"RGN seed=1": "fails(error)"}))
        r = V.empty_body(FX / "eb_regions.rs", "Q09.H4v", modes=["E0", "INV"], seeds=[1])
        self.assertEqual(set(r.per_symbol), {"E0 seed=1", "INV seed=1"})   # never by default
        for target, sym in ((FX / "eb_regions.rs", "count_to"), (FX / "eb_exec.rs", "count_up")):
            r = V.empty_body(target, sym, modes=["RGN"], seeds=[1])
            self.assertEqual(r.verdict, "refused")
            self.assertIn("none of the requested modes applies", r.findings[0].message)
        broken = (FX / "eb_regions.rs").read_text().replace("            // @hole-end Q09.H4v\n", "")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "broken.rs"
            f.write_text(broken)
            r = V.empty_body(f, "Q09.H4v", modes=["RGN"], seeds=[1])
        self.assertEqual(r.verdict, "refused")
        self.assertIn("regions never nest", r.findings[0].message)

    def test_refusals(self):
        for args, kw in (((FX / "eb.rs", "Q04.H5v"), {"modes": ["IR"]}),
                         ((FX / "eb.rs", "Q04.H5v"), {"seeds": []}),
                         ((FX / "eb.rs", "tri"), {}),
                         ((FX / "eb.rs", "nosuch"), {})):
            self.assertEqual(V.empty_body(*args, **kw).verdict, "refused", (args, kw))


# --- capture -------------------------------------------------------------------------------

CAPTURES = (
    ("holes_nc", "holes.rs", True), ("kinds_nc", "kinds.rs", True),
    ("rlimit_nc", "rlimit.rs", True), ("clean_nc", "clean.rs", True),
    ("parse_nc", "stages_parse.rs", True), ("type_nc", "stages_type.rs", True),
    ("vir_nc", "stages_vir.rs", True), ("holes_normal", "holes.rs", False),
)


def recapture():
    """Re-capture raw Verus outputs into fixtures/verus/captured/: each run is
    `verus <file> --crate-type=lib --crate-name <stem> <pinned flags>
    [--no-cheating] --output-json --error-format=json --time` with the fixture
    directory as its working directory and a relative file name, so the
    captured spans name the fixture file relative to it."""
    p = V.pins()
    vb = V.verus_bin()
    CAP.mkdir(exist_ok=True)
    for name, src, nocheat in CAPTURES:
        argv = [vb, src, "--crate-type=lib", "--crate-name", Path(src).stem, *V._base_args(p)]
        argv += ["--no-cheating"] if nocheat else []
        argv += ["--output-json", "--error-format=json", "--time"]
        out = Path(tempfile.mkdtemp(prefix="cap-", dir=common.scratch_root()))
        rc, so, se = common.run_capped([str(a) for a in argv], p["mem_gb"], p["wall_clock_s"],
                                       env=V.job_env(out), cwd=FX, pool="verus", out_dir=out)
        shown = ["verus"] + [str(a) for a in argv[1:]]
        (CAP / f"{name}.cmd").write_text(" ".join(shown) + "\n")
        shutil.copyfile(so, CAP / f"{name}.stdout")
        shutil.copyfile(se, CAP / f"{name}.stderr")
        (CAP / f"{name}.exit").write_text(f"{rc}\n")
        shutil.rmtree(out, ignore_errors=True)
        print(f"captured {name}: exit {rc}")


if __name__ == "__main__":
    if "--recapture" in sys.argv:
        recapture()
    else:
        unittest.main()
