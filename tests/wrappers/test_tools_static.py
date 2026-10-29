"""Tool-free tests for the DV1b tools: scripts/vcheck (its shared core and CLI
refusals), scripts/firsttry.py (the shared slot rules, --lint-hollow, the
static parts of --check/--report/--record), scripts/pins.py (pin files, the
normalization of captured real outputs), scripts/specfreeze,
scripts/reference_lint.py and scripts/update_rubric_pins.sh.

Nothing here runs Dafny or Verus: every case either needs no verifier or is
refused before one would run. Fixtures: the synthetic armed Q04
(tests/course_map/armed) plus tests/wrappers/fixtures/tools/ (an overlay of
invented specimens and checks, and invented hole-free twins for the reference
lint), assembled by test_tools_common.build_root(). The Dafny and Verus
outputs normalized here were captured from the pinned tools by the library
lanes (tests/wrappers/fixtures/{dafny,verus}/captured/).

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_tools_static.py'
"""

import hashlib
import io
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import types
import unittest
import unittest.mock
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
pins = C.load_script("pins")
firsttry = C.load_script("firsttry")
SR = pins.SR
FX = C.ROOT / "tests" / "wrappers" / "fixtures"
REFERENCE = FX / "tools" / "reference"


def h(s):
    """The legacy unsalted verdict hash (read only in the migration window)."""
    return hashlib.sha256(" ".join(s.split()).encode()).hexdigest()


def hs(local, s, mid="Q04"):
    """The salted verdict hash: sha256 of "<module id>:<item id>:<answer>"."""
    return hashlib.sha256(f"{mid}:{local}:{' '.join(s.split())}".encode()).hexdigest()


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, env={**os.environ, "GIT_AUTHOR_NAME": "t",
                                          "GIT_AUTHOR_EMAIL": "t@example.invalid",
                                          "GIT_COMMITTER_NAME": "t",
                                          "GIT_COMMITTER_EMAIL": "t@example.invalid"})


class RootCase(unittest.TestCase):
    git = False
    overlay = True

    def setUp(self):
        self.root = C.build_root(overlay=self.overlay, git=self.git)

    def tearDown(self):
        C.remove_root(self.root)

    def rep(self, rel, old, new):
        C.replace_in(self.root / rel, old, new)

    def line_of(self, rel, needle):
        lines = (self.root / rel).read_text().split("\n")
        return next(i for i, x in enumerate(lines, 1) if needle in x)


# =====================================================================================
# The shared slot rules (one implementation, loaded by marker lines)
# =====================================================================================

class SharedRules(unittest.TestCase):
    def test_one_section_three_consumers(self):
        rl = C.load_script("reference_lint")
        for name in ("sr_obligation", "sr_error", "sr_value", "sr_slot_problems",
                     "sr_twin_leftovers", "sr_salted_answer_hash"):
            self.assertTrue(callable(getattr(SR, name)))
            self.assertTrue(callable(getattr(rl.SR, name)))
            self.assertEqual(getattr(SR, name).__code__.co_code,
                             getattr(firsttry, name).__code__.co_code)
        text = (C.SCRIPTS / "firsttry.py").read_text(encoding="utf-8")
        self.assertEqual(text.count(pins.BEGIN), 1)
        self.assertEqual(text.count(pins.END), 1)

    def test_obligation(self):
        self.assertEqual(SR.sr_obligation("FAILS ???"), (None, None))
        self.assertEqual(SR.sr_obligation("FAILS b d"), (frozenset({"b", "d"}), None))
        self.assertEqual(SR.sr_obligation("FAILS none"), (frozenset(), None))
        self.assertEqual(SR.sr_obligation("FAILS"), (frozenset(), None))
        self.assertIsNotNone(SR.sr_obligation("FAILS B")[1])
        self.assertIsNotNone(SR.sr_obligation("FAILS a a")[1])
        self.assertIsNotNone(SR.sr_obligation("fails a")[1])

    def test_error(self):
        self.assertEqual(SR.sr_error('EXPECT @??? "???"'), (None, None, None))
        self.assertEqual(SR.sr_error('EXPECT @12 "could not be \\"proved\\""'),
                         (12, 'could not be "proved"', None))
        self.assertIsNotNone(SR.sr_error("EXPECT 12 x")[2])

    def test_value_shapes(self):
        self.assertEqual(SR.sr_value("expect Twice(21) == 42;", "d"), ("Twice(21)", "42"))
        self.assertEqual(SR.sr_value("expect F(a == b) == true;", "d"), ("F(a == b)", "true"))
        self.assertEqual(SR.sr_value("assert_eq!(twice(21), ???);", "v"), ("twice(21)", "???"))
        self.assertEqual(SR.sr_value('assert_eq!(f(1, 2), 3, "msg");', "v"), ("f(1, 2)", "3"))
        self.assertEqual(SR.sr_value("assert(double(3) == 6) by (compute_only);", "v"),
                         ("double(3)", "6"))
        self.assertEqual(SR.sr_value("assert f(3) == 9", "py"), ("f(3)", "9"))
        self.assertIsNone(SR.sr_value("expect F(3);", "d"))

    def test_h1_h3_h2(self):
        self.assertIsNotNone(SR.sr_rule_h1("short"))
        self.assertIsNotNone(SR.sr_rule_h1("error:   short"))
        self.assertIsNone(SR.sr_rule_h1("could not be proved"))
        self.assertIsNotNone(SR.sr_rule_h3("error: could not be proved"))
        self.assertIsNotNone(SR.sr_rule_h3("Warning: something long enough"))
        self.assertIsNone(SR.sr_rule_h3("could not be proved"))
        self.assertIsNotNone(SR.sr_rule_h2_echo("a[i+1] >= a[i]", "assert a[i + 1] >= a[ i ];"))
        self.assertIsNone(SR.sr_rule_h2_echo("assertion might not hold", "assert x > 0;"))

    def test_value_literals(self):
        ok = SR.sr_rule_h2_value
        self.assertEqual(ok("numeral", "Twice(21)", "42"), [])
        self.assertEqual(ok("numeral", "f(1)", "-3u64"), [])
        self.assertTrue(ok("numeral", "Twice(21)", "Twice(21)"))          # echo
        self.assertTrue(ok("numeral", "Twice(21)", "21 + 21"))            # not a literal
        self.assertEqual(ok("constructors", "Turn(North)", "East"), [])
        self.assertEqual(ok("constructors", "Turn(North)", "Dir::East"), [])
        self.assertTrue(ok("constructors", "Turn(Turn(North))", "Turn(North)"))  # applies Turn
        self.assertEqual(ok("option literal", "Find(3)", "Some(2)"), [])
        self.assertEqual(ok("bool literal", "P(3)", "true"), [])
        self.assertEqual(ok("string literal", "S()", '"ab"'), [])
        self.assertEqual(ok("char literal", "C()", "'x'"), [])
        self.assertTrue(ok(None, "F(1)", "3"))                            # no Answer form line
        self.assertEqual(SR.sr_answer_form(["// **P8.** What? Answer form: numeral"]), "numeral")

    def test_answer_hash(self):
        # the unsalted hash is retired (DV2b): the salted one is the only verdict hash
        self.assertFalse(hasattr(SR, "sr_answer_hash"))
        self.assertEqual(SR.sr_salted_answer_hash("Q04", "P1dv", "  4   2 0 "),
                         hs("P1dv", "4 2 0"))
        self.assertEqual(SR.sr_slot_value('"a \\"b\\""'), 'a "b"')
        vals = SR.sr_slot_file_values('# c\nP1dv = "x y"\nP2dv = ???\n')
        self.assertEqual(vals, {"P1dv": (2, '"x y"'), "P2dv": (3, "???")})

    def test_commented_checks(self):
        raw = ["method {:test} T() {", "  // Uncomment as you go:", "  // expect F(1) == 2;",
               "  // // prose, not a check", "  //", "  // expect F(2) == 4;", "}",
               "// expect F(3) == 6;"]
        self.assertEqual(SR.sr_commented_checks(raw, "x.dfy"), [3, 6])
        self.assertEqual(SR.sr_stray_commented_checks(raw, "x.dfy"), [8])
        rs = ["#[test]", "#[ignore]", "fn t() {}"]
        self.assertEqual(SR.sr_commented_checks(rs, "x.rs"), [2])

    def test_receipts_and_need(self):
        text = ("verus! {\n// item: Q04.H3v S3\npub proof fn f(x: int)\n{\n"
                "    assert(x * x >= 0) by (nonlinear_arith);\n"
                "    // did: the square is non-negative\n"
                "    assert(x * x * x * x >= 0) by (nonlinear_arith);\n}\n} // verus!\n")
        items, errs = core.ci.parse_items("x.rs", text)
        self.assertEqual(errs, [])
        self.assertEqual(SR.sr_missing_receipts(text, "x.rs", items[0]), [5])
        text = ("module M {\n  // item: Q04.X1d S4\n  // need: lemma L(n: nat)\n"
                "  lemma L(n: nat)\n    ensures n >= 0\n  {\n  }\n}\n")
        items, _ = core.ci.parse_items("x.dfy", text)
        self.assertEqual(SR.sr_need_missing(text, "x.dfy", items[0]), [])
        gone = text.replace("lemma L(n: nat)\n    ensures", "lemma K(n: nat)\n    ensures")
        items, _ = core.ci.parse_items("x.dfy", gone)
        self.assertEqual(SR.sr_need_missing(gone, "x.dfy", items[0]), ["lemma L(n: nat)"])

    def test_enable_line(self):
        self.assertEqual(SR.sr_enable_line("    // SLOT: expect F(1) == 2;", "x.dfy"),
                         "    expect F(1) == 2;")
        self.assertEqual(SR.sr_enable_line("// SLOT: FAILS a", "x.dfy.specimen"), "// FAILS a")
        self.assertEqual(SR.sr_enable_line("# SLOT: assert f(1) == 2", "x.py"),
                         "assert f(1) == 2")
        self.assertEqual(SR.sr_twin_leftovers(["ok", "// SLOT: x", "a ??? b"]), [2, 3])


# =====================================================================================
# The shared core and CLI refusals (no tool runs)
# =====================================================================================

class Core(unittest.TestCase):
    def test_lang_of_and_reference(self):
        self.assertEqual(core.lang_of("a.dfy"), "d")
        self.assertEqual(core.lang_of("x/P1.dfy.specimen"), "d")
        self.assertEqual(core.lang_of("x/P1.rs.specimen"), "v")
        self.assertEqual(core.lang_of("Cargo.toml"), "v")
        self.assertIsNone(core.lang_of("a.py"))
        self.assertTrue(core.is_reference_path(C.ROOT / "Solutions" / "x.dfy", C.ROOT))
        self.assertTrue(core.is_reference_path(C.ROOT / "paper" / "solutions" / "Q04.tex",
                                               C.ROOT))
        self.assertFalse(core.is_reference_path(C.ROOT / "dafny" / "Q" / "x.dfy", C.ROOT))

    def test_author_gate(self):
        """Independent of where the temp dir lies (DVL_TEST_TMP, TMPDIR) and of
        the cwd: git discovery stops at the temp dir's parent."""
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-gate-", dir=C.TMP_BASE))
        ceiling = os.environ.get("GIT_CEILING_DIRECTORIES")
        os.environ["GIT_CEILING_DIRECTORIES"] = str(tmp.resolve().parent)
        try:
            env_ci = os.environ.pop("CI", None)
            self.assertEqual(core.author_gate(tmp), "not inside a git checkout")
            prim = tmp / "prim"
            prim.mkdir()
            git(prim, "init", "-q", "-b", "main")
            git(prim, "commit", "-q", "--allow-empty", "-m", "x")
            self.assertEqual(core.author_gate(prim), "this is the primary worktree")
            git(prim, "worktree", "add", "-q", str(tmp / "learner"), "-b", "leobwang-me")
            self.assertEqual(core.author_gate(tmp / "learner"), "HEAD is on a learner branch")
            git(prim, "worktree", "add", "-q", str(tmp / "auth"), "-b", "authoring")
            self.assertIsNone(core.author_gate(tmp / "auth"))
            os.environ["CI"] = "true"
            self.assertIsNone(core.author_gate(tmp))
        finally:
            os.environ.pop("CI", None)
            if env_ci is not None:
                os.environ["CI"] = env_ci
            if ceiling is None:
                os.environ.pop("GIT_CEILING_DIRECTORIES", None)
            else:
                os.environ["GIT_CEILING_DIRECTORIES"] = ceiling
            shutil.rmtree(tmp, ignore_errors=True)

    def test_check_trust_with_nothing_to_check(self):
        """No given crate and no allowlist (the committed tree): a loud pass,
        no tool run; --check-trust takes no target and no other mode."""
        if any((C.ROOT / "verus" / "given").glob("*/Cargo.toml")) or \
                (C.ROOT / "expected" / "verus_trust.toml").exists():
            self.skipTest("the checkout has given crates or an allowlist: the tool suite "
                          "covers them")
        rc, out, err = C.tool("vaudit", "--check-trust")
        self.assertEqual((rc, out), (0, "vaudit --check-trust: no given crate under "
                                        "verus/given/ and no entry in expected/verus_trust.toml: "
                                        "nothing to check (passing loudly)\n"), err)
        for args in (("--check-trust", "x.rs"), ("--check-trust", "--mode", "given"),
                     ("--check-trust", "--ref"), ("--check-trust", "Q04")):
            rc, out, err = C.tool("vaudit", *args)
            self.assertEqual(rc, 2, (args, out, err))
        rc, out, err = C.tool("vaudit", "--check-trust", "--trust", "no/such.toml")
        self.assertEqual(rc, 3, out + err)

    def test_given_mode_refused_for_learner_files(self):
        """--mode given never lets a file inside the course tree that is not a
        given layer or a declared statement opt out of the abstract-module
        rule (a refusal: no tool runs)."""
        for target in ("tests/wrappers/fixtures/dafny/given/refined.dfy",
                       "tests/wrappers/fixtures/verus/clean.rs"):
            rc, out, err = C.tool("vaudit", "--mode", "given", target)
            self.assertEqual(rc, 3, (target, out, err))
            self.assertIn(f"--mode given: {target} is not a given layer or a declared statement",
                          err)

    def test_learner_prefix_from_course_mode(self):
        self.assertEqual(core.learner_prefix(C.ROOT), "leobwang-")

    def test_cli_usage_and_refusals(self):
        for args, want in ((["--function", "f", "x.rs"], 2),
                           ([], 2),
                           (["Q99"], 3),
                           (["Q19"], 3),                       # planned in the registry
                           (["--module", "Q19"], 3),
                           (["--module", "notanid"], 2),
                           (["no/such/file.dfy"], 3),
                           (["README.md"], 3),
                           (["--selftest", "x.dfy"], 2)):
            rc, out, err = C.tool("vcheck", *args)
            self.assertEqual(rc, want, (args, out, err))
        rc, out, err = C.tool("vcheck", "--gate", "--symbol", "M.F",
                              "tests/wrappers/fixtures/dafny/ok.dfy")
        self.assertEqual(rc, 3, err)
        self.assertIn("filter is refused", err)

    def test_passthrough_refusals(self):
        ok_d, ok_v = "tests/wrappers/fixtures/dafny/ok.dfy", "tests/wrappers/fixtures/verus/clean.rs"
        for args, why in (([ok_d, "--", "--allow-axioms"], "silences hole warnings"),
                          ([ok_d, "--", "/compile:0"], "the legacy CLI is refused"),
                          ([ok_d, "--", "--solver-path", "/usr/bin/z3"], "--solver-path: refused"),
                          ([ok_d, "--", "--boogie", "/x"], "Boogie pass-through"),
                          (["--gate", ok_d, "--", "--isolate-assertions"], "refused in the gate"),
                          ([ok_v, "--", "--no-verify"], "--no-verify: refused by the pins"),
                          ([ok_v, "--", "--rlimit", "100"], "only the pinned --rlimit"),
                          ([ok_v, "--", "--smt-option", "smt.arith.solver=2"],
                           "only smt.random_seed=<int>"),
                          (["--gate", ok_v, "--", "--expand-errors"], "not part of the gate")):
            rc, out, err = C.tool("vcheck", *args)
            self.assertEqual(rc, 3, (args, out, err))
            self.assertIn("refused (no tool ran)", out)
            self.assertIn(why, out)
        rc, out, err = C.tool("vcheck", "--selftest", "--", "--expand-errors")
        self.assertEqual(rc, 2, err)

    def test_smt_log_refusals(self):
        # D53 (R14): --smt-log takes one Verus target in the learner loop or fast channel,
        # and a new or empty directory outside the reference trees; no tool runs.
        ok_d, ok_v = "tests/wrappers/fixtures/dafny/ok.dfy", "tests/wrappers/fixtures/verus/clean.rs"
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-smt-", dir=C.TMP_BASE))
        try:
            (tmp / "full").mkdir()
            (tmp / "full" / "old.smt2").write_text("x")
            for args, want in ((["--smt-log", str(tmp / "a"), "--gate", ok_v], "never the gate"),
                               (["--smt-log", str(tmp / "a"), "--brittleness", ok_v],
                                "never the gate"),
                               (["--smt-log", str(tmp / "a"), ok_d], "one Verus target"),
                               (["--smt-log", str(tmp / "a"), ok_v, ok_v], "one Verus target"),
                               (["--smt-log", str(tmp / "full"), ok_v], "new or empty"),
                               (["--smt-log", "Solutions/smt", ok_v], "reference tree")):
                rc, out, err = C.tool("vcheck", *args)
                self.assertNotEqual(rc, 0, (args, out, err))
                self.assertIn(want, out + err, args)
            self.assertFalse((tmp / "a").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_reference_targets_refused(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-ref-", dir=C.TMP_BASE))
        try:
            (tmp / "MODULES.toml").write_text((C.ROOT / "MODULES.toml").read_text())
            (tmp / "Solutions").mkdir()
            (tmp / "Solutions" / "x.dfy").write_text("module X {}\n")
            rc, out, err = C.tool("vcheck", tmp / "Solutions" / "x.dfy", root=tmp)
            self.assertEqual(rc, 3, err)
            self.assertIn("reference material", err)
            rc, out, err = C.tool("vcheck", "--ref", tmp / "Solutions" / "x.dfy", root=tmp)
            self.assertEqual(rc, 3, err)                 # the author gate: not a git checkout
            self.assertIn("author-only", err)
            rc, out, err = C.tool("vaudit", tmp / "Solutions" / "x.dfy", root=tmp)
            self.assertEqual(rc, 3, err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


    def test_registry_missing_or_unusable_is_a_refusal(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-noreg-", dir=C.TMP_BASE))
        try:
            git(tmp, "init", "-q", "-b", "main")
            runs = (("reference_lint.py",), ("firsttry.py", "Q04", "--report"),
                    ("firsttry.py", "--all", "--lint-hollow"), ("vcheck", "Q04"),
                    ("vaudit", "Q04"), ("specfreeze", "--check", "Q04"), ("pins.py", "Q04"),
                    ("pins.py", "--ci"))
            for broken in (None, "x = [\n"):
                if broken is not None:
                    (tmp / "MODULES.toml").write_text(broken)
                for args in runs:
                    rc, out, err = C.tool(*args, root=tmp, env={"CI": "true"})
                    self.assertEqual(rc, 3, (args, out, err))
                    self.assertNotIn("Traceback", err)
                    self.assertIn("refused: the module registry is unusable: MODULES.toml", err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_pin_counts_usage(self):
        rc, out, err = C.tool("vcheck", "--pin-counts", "Q04")
        self.assertEqual(rc, 2, err)
        rc, out, err = C.tool("vcheck", "--ref", "--pin-counts")
        self.assertEqual(rc, 2, err)
        rc, out, err = C.tool("vcheck", "--ref", "--pin-counts", "Q04", "--gate")
        self.assertEqual(rc, 2, err)
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-pc-", dir=C.TMP_BASE))
        try:
            (tmp / "MODULES.toml").write_text((C.ROOT / "MODULES.toml").read_text())
            rc, out, err = C.tool("vcheck", "--ref", "--pin-counts", "Q04", root=tmp)
            self.assertEqual(rc, 3, err)                 # the author gate: not a git checkout
            self.assertIn("author-only", err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class H5Guard(RootCase):
    def test_unrecorded_specimen_refused(self):
        rc, out, err = C.tool("vcheck", "specimens/Q04/P4d.dfy.specimen", root=self.root)
        self.assertEqual(rc, 3, err)
        self.assertIn("Q04.P4d, whose first try is not recorded", err)
        self.assertEqual(out, "")
        rc, out, err = C.tool("vaudit", "specimens/Q04/P4d.dfy.specimen", root=self.root)
        self.assertEqual(rc, 3, err)


# =====================================================================================
# firsttry: static modes and the refusals before any run
# =====================================================================================

class LintHollow(RootCase):
    def test_shipped_tree_is_hollow(self):
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("Q04 lint-hollow: OK (13 file(s))", out)

    def test_findings(self):
        self.rep("specimens/Q04/P4d.dfy.specimen", "// SLOT: FAILS ???", "// SLOT: FAILS b")
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "// SLOT: CHECK P1dv",
                 "// CHECK P1dv")
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy",
                 "    ensures x + 0 == x\n", "    ensures x + 0 == x\n  {\n  }\n")
        self.rep("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "    ensures Double(n) == 2 * n\n",
                 "    ensures Double(n) == 2 * n\n  {\n  }\n")
        self.rep("dafny/checks/Q04_checks.dfy", "  function Twice",
                 "  // expect Twice(1) == 2;\n  function Twice")
        self.rep("slots/Q04.slots", "P2dv = ???", 'P2dv = "x"')
        self.rep("specimens/Q04/P5d.dfy.specimen", "  method Demo", "  method {:axiom} Demo")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 1, out + err)
        for want in ("specimens/Q04/P4d.dfy.specimen:3: Q04.P4d: slot ships filled-disabled",
                     "Q04_ProofCraft.dfy:11: a live CHECK switch ships enabled",
                     "Q04.H1d: an H item ships a hole form",
                     "Q04.X1d: an X item ships empty or with a hole form",
                     "dafny/checks/Q04_checks.dfy:5: a commented check outside",
                     "slots/Q04.slots:3: Q04.P2dv: slot ships filled-disabled, not unfilled",
                     "specimens/Q04/P5d.dfy.specimen:5: lint: axiom-attribute"):
            self.assertIn(want, out)

    def test_static_holes_sees_the_verus_spec_definition_hole(self):
        """QPLAN §14.0's spec-definition hole (`uninterp spec fn`, counted by the
        tool, Δ8) is a shipped hole form; the filled `open spec fn` is not, and a
        comment naming the keyword is no hole (DV3b integration)."""
        it = {"id": "Q99.H1v", "line_start": 1, "line_end": 4}
        shipped = ("// item: Q99.H1v S2\n"
                   "pub uninterp spec fn tally(k: int) -> bool\n"
                   "    ;\n\n")
        filled = ("// item: Q99.H1v S2\n"
                  "pub open spec fn tally(k: int) -> bool // was uninterp spec fn\n"
                  "{ k > 0 }\n\n")
        self.assertEqual(firsttry.static_holes(shipped, "verus/q/x/src/lib.rs", it), [2])
        self.assertEqual(firsttry.static_holes(filled, "verus/q/x/src/lib.rs", it), [])

    def test_static_holes_sees_a_test_todo(self):
        """D98 (Δ316): `todo!("<item id>")` inside #[cfg(test)] is a shipped hole form (the
        tool's test-todo kind); the empty-body gate skips the block as a test hole and
        runs its compiled tests instead; a `todo!` outside every test item is no form."""
        text = ("use vstd::prelude::*;\n"
                "verus! { pub fn f() -> u8 { 1 } }\n"
                "#[cfg(test)]\n"
                "mod tests {\n"
                "    // item: R99.H2v\n"
                "    fn pattern(n: u8) -> String {\n"
                "        todo!(\"R99.H2v\")\n"
                "    }\n"
                "}\n")
        it = {"id": "R99.H2v", "line_start": 5, "line_end": 8}
        rel = "verus/r/x/src/lib.rs"
        self.assertEqual(firsttry.static_holes(text, rel, it), [7])
        self.assertTrue(firsttry.eb_skip_reason(text, rel, it).startswith(firsttry.TEST_SKIP))
        filled = text.replace('todo!(\"R99.H2v\")', '"a".repeat(n as usize)')
        self.assertEqual(firsttry.static_holes(filled, rel, it), [])
        outside = text.replace("#[cfg(test)]\n", "")
        self.assertEqual(firsttry.static_holes(outside, rel, it), [])

    def test_dafny_value_slot_outside_a_check_unit(self):
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "  method {:test} CheckSum() {",
                 "  // item: Q04.P12d S1 value\n  // Answer form: numeral\n"
                 "  method {:test} P12() {\n    // SLOT: expect Sum(2) == ???;\n  }\n\n"
                 "  method {:test} CheckSum() {")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.P12d: a Dafny value slot lives in a specimen or a given-only check unit",
                      out)

    def test_wrong_proof_note_label(self):
        self.rep("verus/q/q04_proof_craft/src/lib.rs", 'proof_note("Q04.H3v")',
                 'proof_note("Q04.H9v")')
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 1, out)
        self.assertIn("Q04.H3v: its proof_note label is not its own item id", out)

    def test_all_and_empty(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-idle-", dir=C.TMP_BASE))
        try:                         # the real registry with every module planned
            (tmp / "MODULES.toml").write_text(C.plan_real_modules(
                (C.ROOT / "MODULES.toml").read_text()))
            for extra in ((), ("--allow-empty",)):
                rc, out, err = C.tool("firsttry.py", "--all", "--lint-hollow", *extra, root=tmp)
                self.assertEqual(rc, 0, out + err)
                self.assertRegex(out, r"^firsttry --lint-hollow --all: no armed module: nothing "
                                      r"to check \(all \d+ module\(s\) in MODULES.toml are "
                                      r"planned\): passing loudly\n$")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        rc, out, err = C.tool("firsttry.py", "--all", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("Q04 lint-hollow: OK", out)
        # an armed module whose exercise and exit files are all gone: empty fails
        for rec in ("exercises", "exits"):
            for rel in self.registry_paths(rec):
                p = self.root / rel
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
        rc, out, err = C.tool("firsttry.py", "--all", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04: no exercise or exit file exists (an empty list fails)", out)

    def registry_paths(self, field):
        data = tomllib.loads((self.root / "MODULES.toml").read_text())
        rec = next(m for m in data["module"] if m["id"] == "Q04")
        return rec[field]


class FirstTryStatic(RootCase):
    git = True

    def test_usage(self):
        for args, want in ((["Q04", "--check", "--strict"], 2), ([], 2),
                           (["Q99", "--report"], 3), (["Q05", "--report"], 3),
                           (["Q04", "--eb-modes", "E0"], 2), (["Q04", "--all"], 2)):
            rc, out, err = C.tool("firsttry.py", *args, root=self.root)
            self.assertEqual(rc, want, (args, out, err))

    def test_report_static(self):
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("summary: unfilled 11 (of 11 slot(s); 0 filled but not enabled) · test-outs "
                      "unattempted 1 · missing 0 · vacuous 0 · commented checks 1 · banned 0 · "
                      "forms not met 0 · failing enabled slots 0", out)
        # the fixture's T1dv ships with code and is unchanged since: no attempt yet
        self.assertIn("Q04.T1dv  test-out: empty · unrecorded", out)
        self.assertIn("Q04_Library.dfy:11: unfilled: Q04.T1dv: the test-out block is empty", out)
        self.assertIn("Q04_ProofCraft.dfy:34: to uncomment: commented check", out)
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out)
        self.assertIn("strict: FAIL", out)

    def test_exit_skips_an_exit_file_with_no_item(self):
        """QPLAN §30 Q50 (Δ197's open item, DV5c): an exit file of the pair that
        ships with no X block is skipped, the other is scored; when no exit
        file holds an X item, --exit refuses (exit 3) before any run."""
        exits = ["dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "verus/q/q04_proof_craft/src/exit.rs"]
        empty = exits[1]
        ctx = firsttry.Ctx(self.root, "Q04")
        real = ctx.items_in
        ctx.items_in = lambda rels: [] if rels == [empty] else real(rels)
        xs = [i for i in real([exits[0]]) if i["kind"] == "X"]
        self.assertTrue(xs)
        ran = []

        def fake_run(c, rel, items):
            ran.append(rel)
            return {it["id"]: ("unattempted", ["the block is empty"]) for it in items}
        buf, err = io.StringIO(), io.StringIO()
        with unittest.mock.patch.object(firsttry, "exit_run", fake_run), \
                contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            firsttry.mode_exit(ctx)
        self.assertEqual(ran, [exits[0]])                 # the empty file is never run
        out = buf.getvalue()
        self.assertIn(f"Q04 exit — {exits[0]}", out)
        self.assertNotIn(empty, out)
        self.assertIn("nothing recorded", out)
        # both files empty: refused before any run
        ctx.items_in = lambda rels: [] if rels[0] in exits else real(rels)
        ran.clear()
        with unittest.mock.patch.object(firsttry, "exit_run", fake_run), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                firsttry.mode_exit(ctx)
        self.assertEqual(cm.exception.code, core.EXIT_REFUSED)
        self.assertEqual(ran, [])
        self.assertIn(f"{exits[0]} and {empty} have no X items", err.getvalue())

    def test_deleted_slot_check_and_marker_are_missing(self):
        self.rep("specimens/Q04/P3d.dfy.specimen", "// SLOT: FAILS ???\n", "")
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "    // expect Sum(3) == 6;\n",
                 "")
        self.rep("dafny/checks/Q04_checks.dfy", "  // item: Q04.P9d S1 value\n", "")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("specimens/Q04/P3d.dfy.specimen:1: missing: Q04.P3d: its slot is missing",
                      out)
        self.assertIn("1 shipped check(s) deleted instead of uncommented", out)
        self.assertIn("missing: Q04.P9d: its marker is gone", out)

    def test_uncommented_check_is_not_missing(self):
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "    // expect Sum(3) == 6;",
                 "    expect Sum(3) == 6;")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertIn("missing 0", out)
        self.assertIn("commented checks 0", out)

    def test_check_refusals_record_nothing(self):
        self.rep("specimens/Q04/P5d.dfy.specimen", '// SLOT: EXPECT @??? "???"',
                 '// SLOT: EXPECT @7 "error: proved"')
        self.rep("dafny/checks/Q04_checks.dfy", "expect Twice(21) == ???;",
                 "expect Twice(21) == Twice(21);")
        self.rep("specimens/Q04/P4d.dfy.specimen", "// SLOT: FAILS ???", "// SLOT: FAILS b z")
        self.rep("specimens/Q04/P6v.rs.specimen", "    assert(x > 0);  // [b]",
                 "    assert(x >= 0);  // [b]")
        self.rep("specimens/Q04/P6v.rs.specimen", "// SLOT: FAILS ???", "// SLOT: FAILS b")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 1, out + err)                  # a refusal is a failure (exit 1)
        self.assertIn("refused: 4 item(s), nothing recorded for them (exit 1)", out)
        self.assertIn("Q04.P5d  refused (specimens/Q04/P5d.dfy.specimen:3): H1 (vacuous fragment)",
                      out)
        self.assertIn("H3 (severity prefix)", out)
        self.assertIn("Q04.P8d  refused (dafny/checks/Q04_checks.dfy:10): H2 (echo)", out)
        self.assertIn("names label(s) the specimen does not carry: z", out)
        self.assertIn("Q04.P6v  its given code is not as shipped", out)
        self.assertFalse((self.root / "instructor" / "calib" / "Q04.tsv").exists())

    def test_each_vacuity_refusal_exits_1(self):
        """An empty fragment (H1), a severity prefix (H3) or an echo (H2), alone."""
        spec = "specimens/Q04/P5d.dfy.specimen"
        shipped = (self.root / spec).read_text()
        for fill in ('EXPECT @7 ""', 'EXPECT @7 "error: a postcondition could not be proved"',
                     'EXPECT @7 "ensures y > x"'):
            (self.root / spec).write_text(shipped.replace('EXPECT @??? "???"', fill))
            rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
            self.assertEqual(rc, 1, (fill, out + err))
            self.assertIn("Q04.P5d  refused (specimens/Q04/P5d.dfy.specimen:3): H", out)
            self.assertIn("refused: 1 item(s)", out)
            self.assertFalse((self.root / "instructor" / "calib" / "Q04.tsv").exists())

    def test_check_nothing_new_exits_0(self):
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("nothing new to check", out)
        self.rep("specimens/Q04/P3d.dfy.specimen", "// SLOT: FAILS ???\n", "")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 1, out + err)                   # fewer slots than shipped
        self.assertIn("Q04.P3d  its slot is missing", out)

    def test_deleted_files_are_missing(self):
        """A specimen (or exit) file deleted since it shipped: its items are
        missing in the report, refused by --check, and not passing in pins.py."""
        os.remove(self.root / "specimens/Q04/P3d.dfy.specimen")
        os.remove(self.root / "specimens/Q04/P6v.rs.specimen")
        os.remove(self.root / "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        for want in ("specimens/Q04/P3d.dfy.specimen:0: missing: Q04.P3d: its file is gone (the "
                     "item shipped at line 1 with 1 slot(s))",
                     "specimens/Q04/P6v.rs.specimen:0: missing: Q04.P6v: its file is gone",
                     "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy:0: missing: Q04.X1d: its file is gone",
                     "missing: Q04.X2d: its file is gone",
                     "· missing 4 ·"):
            self.assertIn(want, out)
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.P6v  its file specimens/Q04/P6v.rs.specimen is gone", out)
        self.assertIn("Q04.P3d  its file specimens/Q04/P3d.dfy.specimen is gone", out)
        self.assertNotIn("Q04.X1d", out)                     # --check judges P/T items only
        rc, out, err = C.tool("pins.py", "Q04", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("· Q04.P3d  its file specimens/Q04/P3d.dfy.specimen is gone since it shipped",
                      out)
        self.assertIn("pins Q04: 0 pass, 2 not", out)
        rc, out, err = C.tool("firsttry.py", "Q04", "--record", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("unfilled 14;", out)           # 9 left + 4 gone + 1 unattempted test-out

    def test_empty_body_is_author_only(self):
        rc, out, err = C.tool("firsttry.py", "Q04", "--empty-body", root=self.root)
        self.assertEqual(rc, 3, out + err)                   # a primary worktree, no CI
        self.assertIn("firsttry --empty-body is author-only", err)
        self.assertEqual(out, "")

    def test_partial_fill_is_not_checked(self):
        self.rep("slots/Q04.slots", "P1dv = ???", 'P1dv = "verified 2"')
        (self.root / "expected").mkdir()
        (self.root / "expected" / "Q04.pins").write_text(
            f"P1dv  salted-sha256 {hs('P1dv', 'verified 2')}\n"
            f"P2dv  salted-sha256 {hs('P2dv', 'y')}\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("✓ Q04.P1dv  first try passes", out)       # verdicts need no tool
        rows = (self.root / "instructor" / "calib" / "Q04.tsv").read_text().splitlines()
        self.assertEqual(len(rows), 1)
        item, kind, verdict, day, digest = rows[0].split("\t")
        self.assertEqual((item, kind, verdict), ("Q04.P1dv", "predict", "pass"))
        self.assertEqual(digest, hashlib.sha256(b"verified 2").hexdigest())
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertIn("= Q04.P1dv  first try already recorded", out)
        self.assertEqual(len((self.root / "instructor" / "calib" / "Q04.tsv")
                             .read_text().splitlines()), 1)              # append-only, first wins

    def test_record(self):
        calib = self.root / "instructor" / "calib"
        calib.mkdir(parents=True)
        (calib / "Q04.tsv").write_text(
            "Q04.P1dv\tpredict\tpass\t2026-10-04\tx\nQ04.P4d\tpredict\tfail\t2026-10-04\tx\n"
            "Q04.P3d\tobserved\tpass\t2026-10-04\tx\nQ04.X1d\texit\tpass\t2026-10-04\tx\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--record", root=self.root)
        self.assertEqual(rc, 0, out + err)
        last = (self.root / "instructor" / "gradebook.md").read_text().splitlines()[-1]
        # unfilled: 11 slots and the unattempted test-out; unrecorded: 8 P items and T1dv
        self.assertRegex(last, r"^\| \d{4}-\d\d-\d\d \| Q04 \| calib \| first-try 1/11 \(9%\); "
                               r"exit 1/4 \| unfilled 12; unrecorded 9 \|$")


class ModerateTierGates(RootCase):
    """DV3a tool items on the synthetic Q04 (moderate tier): T items wait for the
    predictions (QPLAN §6 Q23), budget items report resource attributes (Q21),
    property-test items name their test targets (Q20). Nothing here runs a tool."""
    git = True
    CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
    STD = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"

    def test_test_outs_wait_for_the_predictions(self):
        self.assertTrue(firsttry.predictions_first({"track": "Q", "id": "Q04"}))
        self.assertTrue(firsttry.predictions_first({"track": "Q", "id": "Q18"}))
        self.assertFalse(firsttry.predictions_first({"track": "Q", "id": "Q03"}))
        self.assertFalse(firsttry.predictions_first({"track": "R", "id": "R07"}))
        # T1dv complete (code beyond what shipped, no hole): its try waits for 11 P items
        self.rep(self.STD, "  const T1 := 0\n", "  function Inc(n: nat): nat { n + 1 }\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("· Q04.T1dv  waits for the module's predictions (11 P item(s) unrecorded: "
                      "Q04.P1dv", out)
        self.assertIn("refused: 1 item(s), nothing recorded for them (exit 1)", out)
        self.assertFalse((self.root / "instructor" / "calib" / "Q04.tsv").exists())
        # one P item recorded is not enough
        calib = self.root / "instructor" / "calib"
        calib.mkdir(parents=True)
        (calib / "Q04.tsv").write_text("Q04.P1dv\tpredict\tpass\t2026-10-05\tx\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("(10 P item(s) unrecorded: Q04.P2dv Q04.P3d", out)
        ctx = firsttry.Ctx(self.root, "Q04")
        self.assertEqual(len(firsttry.waiting_predictions(ctx)), 10)
        ctx.calib = {it["id"]: {} for it in ctx.items if it["kind"] == "P"}
        self.assertEqual(firsttry.waiting_predictions(ctx), [])

    def budget_root(self):
        self.rep(self.CORE, "  // uses: calc\n  lemma SumFormula", "  // uses: calc, rlimit\n"
                 "  lemma SumFormula")
        self.rep(self.CORE, "  const Example := 1\n", "  const Example := 1\n\n"
                 "  lemma {:resource_limit 100} Helper()\n    ensures true\n  {\n  }\n")

    def test_budget_items_charge_resource_attributes(self):
        self.budget_root()
        ctx = firsttry.Ctx(self.root, "Q04")
        got = firsttry.rlimit_charges(ctx, self.CORE)
        helper = self.line_of(self.CORE, "lemma {:resource_limit 100} Helper")
        self.assertEqual(got, {"Q04.H3d": [(helper, "resource-attribute", False)]})
        self.assertEqual(firsttry.rlimit_charges(ctx, self.STD), {})
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{self.CORE}:{helper}: budget: Q04.H3d: resource-attribute outside every "
                      "item block", out)
        self.assertIn(", budget 1, ", out)
        # inside the item's own block it is charged there (and the report's banned count has it)
        self.rep(self.CORE, "  lemma SumFormula", "  lemma {:resource_limit 9} SumFormula")
        ctx = firsttry.Ctx(self.root, "Q04")
        line = self.line_of(self.CORE, "lemma {:resource_limit 9} SumFormula")
        self.assertIn((line, "resource-attribute", True), firsttry.rlimit_charges(ctx, self.CORE)
                      ["Q04.H3d"])
        it = next(i for i in ctx.items if i["id"] == "Q04.H3d")
        st, reasons = firsttry.judge_block(ctx, self.CORE, it, [], [], [(line, "resource-attribute",
                                                                          True)])
        self.assertEqual(st, "fail")
        self.assertIn(f"a resource attribute at line {line} (resource-attribute): a budget item "
                      "proves at the pinned limit", reasons)

    def test_property_test_targets(self):
        self.rep(self.CORE, "  // uses: calc\n  lemma SumFormula", "  // uses: calc, property-test\n"
                 "  lemma SumFormula")
        self.rep("verus/q/q04_proof_craft/src/lib.rs", "// uses: calc\n// pair: Q04.H1d",
                 "// uses: calc, property-test\n// pair: Q04.H1d")
        self.rep("verus/q/q04_proof_craft/src/exit.rs", "// uses: calc", "// uses: property-test")
        ctx = firsttry.Ctx(self.root, "Q04")
        files = ctx.exercises + ctx.exits
        got = [(lang, C.Path(t).relative_to(self.root).as_posix(), ids)
               for lang, t, _, ids in firsttry.property_test_targets(ctx, files)]
        self.assertEqual(sorted(got), [
            ("d", "dafny/Q/Q04_ProofCraft/core", ["Q04.H3d"]),
            ("v", "verus/q/q04_proof_craft", ["Q04.H1v"]),
            ("v", "verus/q/q04_proof_craft/src/exit.rs", ["Q04.X1v"])])
        # none in the report files: nothing to run, no tool
        self.assertEqual(firsttry.run_property_tests(ctx, [self.STD]), [])


# =====================================================================================
# pins.py: pin files, hygiene, normalization of captured outputs
# =====================================================================================

class PinsStatic(RootCase):
    overlay = False

    def test_hygiene_and_refusal(self):
        (self.root / "expected").mkdir()
        (self.root / "expected" / "Q04.pins").write_text(
            f"# c\nP1dv  sha256 {h('a')}\nP7dv  sha256 {h('b')}\nP2dv sha256 xyz\n")
        # --ci runs outside the author's context too (here: not a git checkout),
        # with the reference half skipped and said so; --update and --ref do not
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("expected/Q04.pins:4: malformed pin", out)
        self.assertIn("pins --ci: the reference half (verdict pins against the reference "
                      "answers) skipped: not the author's context (not inside a git checkout); "
                      "pins.py --ref runs it there", out)
        for args in (("--ref",), ("--update",)):
            rc, out, err = C.tool("pins.py", *args, root=self.root)
            self.assertEqual(rc, 3, (args, out, err))
            self.assertIn("author-only", err)
        sc = self.root / "expected" / "specimens" / "Q04" / "gone.dfy.specimen.expect"
        sc.parent.mkdir(parents=True)
        sc.write_text("command: verify\nexit: 0\n")
        leak = self.root / "expected" / "specimens" / "Q04" / "P3d.dfy.specimen.expect"
        leak.write_text("command: verify\nexit: 4\n")
        rc, out, err = C.tool("pins.py", "--ci", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        for want in ("expected/Q04.pins:4: malformed pin",
                     "expected/Q04.pins:3: P7dv names no verdict item of Q04",
                     "expected/Q04.pins:0: verdict item Q04.P2dv has no pin",
                     "stale sidecar: its source specimens/Q04/gone.dfy.specimen is gone",
                     "expected/specimens/Q04/P3d.dfy.specimen.expect: a sidecar of "
                     "specimens/Q04/P3d.dfy.specimen, whose items carry prediction slots",
                     "expected/Q04.counts:0: Q04 has 3 verification unit(s) and no count pin"):
            self.assertIn(want, out)

    def test_update_refuses_slot_files(self):
        for rel in ("specimens/Q04/P3d.dfy.specimen",
                    "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"):     # a CHECK switch
            rc, out, err = C.tool("pins.py", "--update", rel, root=self.root, env={"CI": "true"})
            self.assertEqual(rc, 3, (rel, out, err))
            self.assertIn("carries prediction slots", err)
        self.assertFalse((self.root / "expected").exists())
        leak = self.root / "expected" / "specimens" / "Q04" / "P3d.dfy.specimen.expect"
        leak.parent.mkdir(parents=True)
        leak.write_text("command: verify\nexit: 4\n")
        rc, out, err = C.tool("pins.py", "--update", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)                 # refreshing it is refused too

    def test_ci_checks_counts_and_reference_hashes(self):
        exp = self.root / "expected"
        exp.mkdir()
        (exp / "Q04.pins").write_text(f"P1dv  salted-sha256 {hs('P1dv', 'verified 2')}\n"
                                      f"P2dv  salted-sha256 {hs('P2dv', 'y')}\n")
        ref = self.root / "Solutions" / "slots"
        ref.mkdir(parents=True)
        (ref / "Q04.slots").write_text('P1dv = "verified   2"\nP2dv = "verified 3"\n')
        (exp / "Q04.counts").write_text(core.render_counts("Q04", [
            ("dafny/Q/Q04_ProofCraft/core", "dafny", 5, ["Q04_ProofCraft.H1", "Q04_ProofCraft.Gone"]),
            ("dafny/Q/Q04_ProofCraft/std", "verus", 2, ["Q04_Library.H2"]),
            ("dafny/Q/Q04_ProofCraft/agent", "dafny", 1, ["Q04_AgentRetriever.X"])]))
        (exp / "Q05.counts").write_text("schema = 1\n")
        rc, out, err = C.tool("pins.py", "--ci", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        for want in ("Solutions/slots/Q04.slots:2: Q04.P2dv: the reference answer does not match "
                     "its pin",
                     "expected/Q04.counts:0: unit verus/q/q04_proof_craft has no count pin",
                     "expected/Q04.counts:0: dafny/Q/Q04_ProofCraft/agent is not a unit of Q04",
                     "expected/Q04.counts:0: dafny/Q/Q04_ProofCraft/std is a dafny unit, pinned "
                     "as verus",
                     "expected/Q04.counts:0: dafny/Q/Q04_ProofCraft/core: 1 pinned symbol(s) no "
                     "longer declared with a contract in its learner files (Q04_ProofCraft.Gone)",
                     "expected/Q05.counts: Q05 is not a non-planned module"):
            self.assertIn(want, out)
        self.assertNotIn("P1dv", out)                      # its reference answer matches
        self.assertNotIn("verified 3", out)                # locations only, never an answer
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)     # not the author's context
        self.assertEqual(rc, 1, out + err)
        self.assertNotIn("Solutions/", out)                # the reference is never read here
        self.assertIn("expected/Q05.counts: Q05 is not a non-planned module", out)
        self.assertIn("the reference half (verdict pins against the reference answers) skipped",
                      out)

    def test_no_armed_module_passes_loudly(self):
        """Every module planned (the committed registry, its modules set back to
        planned): --ci and --ref have nothing to check and say so; a stray count
        pin still fails (a pin that matches nothing), and so does a registry with
        no module."""
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-idle-", dir=C.TMP_BASE))
        try:
            (tmp / "MODULES.toml").write_text(C.plan_real_modules(
                (C.ROOT / "MODULES.toml").read_text()))
            for args in (("--ci",), ("--ci", "--allow-empty"), ("--ref",)):
                rc, out, err = C.tool("pins.py", *args, root=tmp, env={"CI": "true"})
                self.assertEqual(rc, 0, (args, out, err))
                self.assertIn("no armed module: nothing to check (all ", out)
                self.assertIn("passing loudly", out)
            (tmp / "expected").mkdir()
            (tmp / "expected" / "Q05.counts").write_text("schema = 1\n")
            rc, out, err = C.tool("pins.py", "--ci", root=tmp, env={"CI": "true"})
            self.assertEqual(rc, 1, out + err)
            self.assertIn("expected/Q05.counts: Q05 is not a non-planned module", out)
            (tmp / "MODULES.toml").write_text("# no module\n")
            for args in (("--ci",), ("--ref",)):
                rc, out, err = C.tool("pins.py", *args, root=tmp, env={"CI": "true"})
                self.assertEqual(rc, 3, (args, out, err))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_verdict_outcome(self):
        (self.root / "expected").mkdir()
        (self.root / "expected" / "Q04.pins").write_text(
            f"P1dv  salted-sha256 {hs('P1dv', 'verified 2')}\n")
        it = {"id": "Q04.P1dv"}
        self.assertEqual(pins.verdict_outcome(self.root, "Q04", it, '"verified   2 "'), "pass")
        self.assertEqual(pins.verdict_outcome(self.root, "Q04", it, '"verified 3"'), "fail")
        self.assertEqual(pins.verdict_outcome(self.root, "Q04", {"id": "Q04.P2dv"}, '"x"'),
                         "error")

    def test_salted_pins_and_the_retired_legacy_reader(self):
        """Salted pins differ per item for equal answers and hide the well-known
        hash of a short answer; a legacy unsalted pin is never read any more
        (DV2b retired the reader): it matches no answer, --ci reports it in
        every context, and the author's re-pin writes salted pins only."""
        self.assertFalse(pins.LEGACY_PINS_READABLE)
        self.assertEqual(SR.sr_salted_answer_hash("Q04", "P1dv", " a  b "),
                         hashlib.sha256(b"Q04:P1dv:a b").hexdigest())
        self.assertNotEqual(hs("P1dv", "a"), hs("P2dv", "a"))
        self.assertNotEqual(hs("P1dv", "a"), h("a"))
        exp = self.root / "expected"
        exp.mkdir()
        (exp / "Q04.pins").write_text(f"P1dv  sha256 {h('verified 2')}\n"
                                      f"P2dv  salted-sha256 {hs('P2dv', 'verified 3')}\n")
        it = {"id": "Q04.P1dv"}
        self.assertEqual(pins.verdict_outcome(self.root, "Q04", it, '"verified 2"'), "error")
        self.assertFalse(pins.pin_matches("Q04", "P1dv", '"verified 2"',
                                          pins.read_pins(self.root, "Q04")[0]["P1dv"]))
        self.assertEqual(pins.verdict_outcome(self.root, "Q04", {"id": "Q04.P2dv"},
                                              '"verified 3"'), "pass")
        for env in ({}, {"CI": "true"}):
            rc, out, err = C.tool("pins.py", "--ci", root=self.root, env=env)
            self.assertEqual(rc, 1, out + err)
            self.assertIn("expected/Q04.pins:1: P1dv is a legacy unsalted pin, which no tool "
                          "reads any more: re-pin with scripts/pins.py --update --ref --module "
                          "Q04", out)
            self.assertNotIn("P2dv is a legacy", out)
        (exp / "Q04.pins").write_text(f"P1dv  sha256 {'z' * 64}\n")
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        self.assertIn("expected/Q04.pins:1: malformed pin (`<K><n><lang>  salted-sha256 <64 hex>`)",
                      out)
        ref = self.root / "Solutions" / "slots"
        ref.mkdir(parents=True)
        (ref / "Q04.slots").write_text('P1dv = "verified 2"\nP2dv = "verified 3"\n')
        rc, out, err = C.tool("pins.py", "--update", "--ref", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        text = (exp / "Q04.pins").read_text()
        self.assertIn(f"P1dv  salted-sha256 {hs('P1dv', 'verified 2')}", text)
        self.assertIn(f"P2dv  salted-sha256 {hs('P2dv', 'verified 3')}", text)
        body = [x for x in text.splitlines() if not x.startswith("#")]
        self.assertEqual(len(body), 2)
        self.assertTrue(all(x.split()[1] == "salted-sha256" for x in body), body)
        self.assertNotIn("verified", text)                    # never the answer itself

    def test_ref_module_with_nothing_to_check(self):
        """pins.py --ref --module on an armed module with no verdict item and no
        reference slot (Q16's shape) passes loudly; a run over every armed module
        whose set is empty still fails (DV5c gaps lane's fix; DV5d small fixes'
        test)."""
        for rel, iid in (("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "P1dv"),
                         ("verus/q/q04_proof_craft/src/lib.rs", "P2dv")):
            self.rep(rel, f"// item: Q04.{iid}", "// no item here")
            self.rep(rel, f"// SLOT: CHECK {iid}", "// no slot here")
        (self.root / "slots" / "Q04.slots").write_text("# no verdict slot\n")
        rc, out, err = C.tool("pins.py", "--ref", "--module", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --ref: Q04 has no verdict item and no reference slot: nothing to "
                      "check for it (passing loudly", out)
        rc, out, err = C.tool("pins.py", "--ref", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("pins --ref: nothing to check (1 module(s)); an empty set fails", out)


class Normalization(unittest.TestCase):
    """golden() over outputs the library lanes captured from the pinned tools."""

    def test_dafny_captured(self):
        cap = FX / "dafny" / "captured" / "verify_fails.jsonl"
        diags, status, errors = core.D.parse_json_lines(cap.read_text())
        res = core.common.Result("dafny", "fails.dfy", 4, "failed", "verify", 1, [],
                                 core.D._sorted(diags))
        lines, _ = pins.golden(FX / "dafny", "fails.dfy", res=res)
        self.assertEqual(lines[:5], ["exit: 4", "verdict: failed", "stage: verify", "verified: 1",
                                     "holes: 0"])
        body = "\n".join(lines)
        self.assertNotIn("/home/", body)
        self.assertNotIn("file://", body)
        self.assertTrue(any(":" in x and "error" in x for x in lines[5:]))

    def test_verus_captured(self):
        cap = FX / "verus" / "captured"
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-norm-", dir=C.TMP_BASE))
        try:
            job = tmp / "01-target"
            job.mkdir()
            shutil.copyfile(cap / "holes_nc.stdout", job / "stdout.txt")
            shutil.copyfile(cap / "holes_nc.stderr", job / "stderr.txt")
            res = core.common.Result("verus", "holes.rs", 1, "failed", "verify", None, [], [],
                                     raw_dir=str(tmp))
            lines, _ = pins.golden(FX / "verus", "holes.rs", res=res)
            body = "\n".join(lines[5:])
            doc = json.loads(body)
            self.assertEqual(set(doc), {"json", "diagnostics", "other"})
            self.assertNotIn("times-ms", doc["json"] or {})
            self.assertFalse(any("aborting due to" in d["message"] for d in doc["diagnostics"]))
            self.assertNotIn("/home/", body)
            again, _ = pins.golden(FX / "verus", "holes.rs", res=res)
            self.assertEqual(lines, again)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_redact_and_sidecar_roundtrip(self):
        self.assertEqual(pins.redact("see /a/b/c/x.rs:3 and 1 / 2", "/nowhere"),
                         "see x.rs:3 and 1 / 2")
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-sc-", dir=C.TMP_BASE))
        try:
            p = tmp / "x.expect"
            p.write_text(pins.render_sidecar("specimens/Q04/x.dfy.specimen", "verify",
                                             ["exit: 4", "a"]))
            self.assertEqual(pins.read_sidecar(p), ("verify", ["exit: 4", "a"]))
            p.write_text("exit: 4\n")
            with self.assertRaises(ValueError):
                pins.read_sidecar(p)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_author_expects_skip_slots(self):
        text = ('// item: Q04.P5d S3 error\n// EXPECT @5 "a postcondition here"\n'
                'module M {}\n')
        items, _ = core.ci.parse_items("x.dfy.specimen", text)
        self.assertEqual(pins.author_expects("x.dfy.specimen", text, items), [])
        text2 = '// item: Q04.C2d S3 write:calc\n// EXPECT @5 "a \\"q\\" here"\nmodule M {}\n'
        items, _ = core.ci.parse_items("y.dfy.specimen", text2)
        self.assertEqual(pins.author_expects("y.dfy.specimen", text2, items),
                         [(2, 5, 'a "q" here')])


# =====================================================================================
# specfreeze (static modes)
# =====================================================================================

class SpecFreeze(RootCase):
    CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
    RS = "verus/q/q04_proof_craft/src/lib.rs"

    def test_pin_and_check(self):
        self.rep(self.CORE, "  function Sum", "  function Hole(n: nat): nat\n"
                                              "    ensures Hole(n) >= n\n\n  function Sum")
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual(rc, 3, err)                       # no pin yet
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root)
        self.assertEqual(rc, 3, err)                       # author-only: no CI, not a worktree
        self.assertIn("specfreeze --pin is author-only", err)
        self.assertFalse((self.root / "expected" / "Q04.freeze").exists())
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        freeze = (self.root / "expected" / "Q04.freeze").read_text()
        self.assertIn('open_bodies = ["Q04_ProofCraft.Hole"]', freeze)
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual((rc, out.strip().splitlines()[-1]), (0, "specfreeze: Q04: 0 finding(s)"))
        # filling holes changes no statement (a function hole is pinned by its header)
        self.rep(self.CORE, "    ensures x + 0 == x\n", "    ensures x + 0 == x\n  {\n  }\n")
        self.rep(self.CORE, "    ensures Hole(n) >= n\n", "    ensures Hole(n) >= n\n  {\n    n\n  }\n")
        self.rep(self.RS, '    #[verifier::proof_note("Q04.H1v")] assume(false);\n', "")
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual(rc, 0, out + err)
        # a changed clause, a changed signature, a deleted declaration
        self.rep(self.CORE, "ensures 2 * Sum(n) == n * (n + 1)", "ensures 2 * Sum(n) >= n")
        self.rep(self.RS, "        x < 1000,", "        x < 100,")
        self.rep("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy",
                 "lemma DoubleMono(a: nat, b: nat)\n    requires",
                 "lemma DoubleMonoX(a: nat, b: nat)\n    requires")
        (self.root / "specimens/Q04/P9d.dfy.specimen").write_text(
            "// item: Q04.P9d S3 obligation\n// SLOT: FAILS ???\nmodule Q04_P9 {\n"
            "  method M() { assert true; // [a]\n  }\n}\n")
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual(rc, 1, out + err)
        line = self.line_of(self.CORE, "lemma SumFormula")
        for want in (f"Q04_ProofCraft.dfy:{line}: freeze-changed — Q04_ProofCraft.SumFormula",
                     "src/lib.rs:12: freeze-changed — twice",
                     "Q04_Exit.dfy:0: freeze-missing — Q04_Exit.DoubleMono",
                     "specimens/Q04/P9d.dfy.specimen:0: freeze-unpinned-file"):
            self.assertIn(want, out)
        self.assertNotIn("2 * Sum", out)               # symbols only, never statement text

    BOX = ("  method Clear(a: array<int>)\n      requires a.Length > 0\n"
           "      ensures a[0] == 0\n    {\n      assume false;\n      a[0] := 0;\n    }\n\n"
           "  function Sum")
    TWIN_BOX = ("  method Clear(a: array<int>)\n      requires a.Length > 0\n"
                "      // @hole-begin Q04.H9d\n      modifies a\n      // @hole-end Q04.H9d\n"
                "      ensures a[0] == 0\n      // @hole-begin Q04.H9d\n"
                "      ensures a.Length == old(a.Length)\n      // @hole-end Q04.H9d\n    {\n"
                "      a[0] := 0;\n    }\n\n  function Sum")

    def test_open_frames(self):
        """QPLAN §6 Q22: a frame annotation hole's added modifies and ensures
        clauses are no freeze change; a weakened or dropped clause still is."""
        self.rep(self.CORE, "  function Sum", self.BOX)
        twin = self.root / "Solutions" / self.CORE
        twin.parent.mkdir(parents=True)
        twin.write_text((self.root / self.CORE).read_text().replace(self.BOX, self.TWIN_BOX))
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        freeze = (self.root / "expected" / "Q04.freeze").read_text()
        self.assertIn('open_frames = ["Q04_ProofCraft.Clear"]', freeze)
        self.assertIn("[file.frame_ensures]", freeze)
        files = {f["path"]: f for f in tomllib.loads(freeze)["file"]}
        self.assertEqual(len(files[self.CORE]["frame_ensures"]["Q04_ProofCraft.Clear"]), 1)
        self.assertEqual([r for r, f in files.items() if "open_frames" in f], [self.CORE])
        # the learner's answer: the twin's clauses added (and the assume gone)
        self.rep(self.CORE, "      requires a.Length > 0\n      ensures a[0] == 0\n    {\n"
                 "      assume false;\n",
                 "      requires a.Length > 0\n      modifies a\n      ensures a[0] == 0\n"
                 "      ensures a.Length == old(a.Length)\n    {\n")
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual((rc, out.strip().splitlines()[-1]), (0, "specfreeze: Q04: 0 finding(s)"))
        line = self.line_of(self.CORE, "method Clear")
        for old, new in (("      ensures a[0] == 0\n", ""),                    # a shipped ensures gone
                         ("      ensures a[0] == 0\n", "      ensures a[0] <= 0\n"),
                         ("      requires a.Length > 0\n", "      requires a.Length > 1\n"),
                         ("      requires a.Length > 0\n",
                          "      requires a.Length > 0\n      requires a[0] < 9\n"),
                         ("  method Clear(a: array<int>)", "  method Clear(a: array<nat>)")):
            text = (self.root / self.CORE).read_text()
            self.rep(self.CORE, old, new)
            rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
            self.assertEqual(rc, 1, (old, new, out + err))
            self.assertIn(f"Q04_ProofCraft.dfy:{line}: freeze-changed — Q04_ProofCraft.Clear",
                          out)
            (self.root / self.CORE).write_text(text)
        # an ensures moved before the shipped one is still in order: accepted
        self.rep(self.CORE, "      ensures a[0] == 0\n      ensures a.Length == old(a.Length)\n",
                 "      ensures a.Length == old(a.Length)\n      ensures a[0] == 0\n")
        rc, out, err = C.tool("specfreeze", "--check", "Q04", root=self.root)
        self.assertEqual(rc, 0, out + err)

    def test_open_frames_pin_refusals(self):
        self.rep(self.CORE, "  function Sum", self.BOX)
        twin = self.root / "Solutions" / self.CORE
        twin.parent.mkdir(parents=True)
        # A requires-only region is now an open spec (PLAN R11). Keep
        # this refusal case a frame that also tries to add a precondition.
        bad = self.TWIN_BOX.replace("      modifies a\n",
                                    "      modifies a\n      requires a[0] < 9\n")
        twin.write_text((self.root / self.CORE).read_text().replace(self.BOX, bad))
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("Q04_ProofCraft.Clear: the twin's header differs from the shipped one",
                      err)
        twin.write_text((self.root / self.CORE).read_text().replace(
            self.BOX, self.TWIN_BOX.replace("      // @hole-end Q04.H9d\n      ensures a[0] == 0",
                                            "      ensures a[0] == 0", 1)))
        rc, out, err = C.tool("specfreeze", "--pin", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("inside the open region of Q04.H9d", err)
        self.assertFalse((self.root / "expected" / "Q04.freeze").exists())

    def test_hash(self):
        rc, out, err = C.tool("specfreeze", "--hash", self.root / self.RS, "--json",
                              root=self.root)
        self.assertEqual(rc, 0, err)
        table = json.loads(out)
        self.assertIn("sum_formula", table)
        self.assertEqual(len(table["sum_formula"]), 64)

    def pin_files(self, mid="Q04"):
        rc, out, err = C.tool("specfreeze", "--pin", mid, root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        freeze = tomllib.loads((self.root / "expected" / f"{mid}.freeze").read_text())
        return {f["path"]: f for f in freeze["file"]}

    def check(self, mid="Q04"):
        rc, out, err = C.tool("specfreeze", "--check", mid, root=self.root)
        return rc, out + err

    def test_opacity_is_part_of_a_dafny_statement(self):
        """DV3a follow-up (Q06's opaque definitions): making a shipped opaque
        function transparent, or a transparent one opaque, is freeze-changed;
        `opaque` and `{:opaque}` are one statement; a file without an opaque
        declaration pins the plain hashes it pinned before."""
        rc, out, err = C.tool("specfreeze", "--hash", self.root / self.CORE, "--json",
                              root=self.root)
        self.assertEqual(rc, 0, err)
        plain = json.loads(out)
        files = self.pin_files()
        self.assertEqual(files[self.CORE]["statements"], plain)     # nothing opaque: unchanged
        self.rep(self.CORE, "  function Sum", "  opaque function Sum")
        files = self.pin_files()
        got = files[self.CORE]["statements"]
        self.assertEqual(got["Q04_ProofCraft.Sum"], hashlib.sha256(
            ("opaque\0" + plain["Q04_ProofCraft.Sum"]).encode()).hexdigest())
        self.assertEqual({k: v for k, v in got.items() if k != "Q04_ProofCraft.Sum"},
                         {k: v for k, v in plain.items() if k != "Q04_ProofCraft.Sum"})
        self.assertEqual(self.check()[0], 0)
        line = self.line_of(self.CORE, "function Sum")
        want = f"Q04_ProofCraft.dfy:{line}: freeze-changed — Q04_ProofCraft.Sum"
        self.rep(self.CORE, "  opaque function Sum", "  function {:opaque} Sum")
        rc, out = self.check()
        self.assertEqual(rc, 0, out)                       # the attribute spelling: same statement
        self.rep(self.CORE, "  function {:opaque} Sum", "  function Sum")
        rc, out = self.check()
        self.assertEqual(rc, 1, out)                       # made transparent
        self.assertIn(want, out)
        self.assertEqual(out.count("freeze-changed"), 1, out)
        self.pin_files()                                   # shipped transparent ...
        self.rep(self.CORE, "  function Sum", "  opaque function Sum")
        rc, out = self.check()
        self.assertEqual(rc, 1, out)                       # ... and made opaque
        self.assertIn(want, out)

    def test_an_automation_off_lever_is_frozen(self):
        """DV5b review fix: --pin records a file's automation-off levers; --check and
        --against report one that is gone (a module's nonlinear switch, a
        lemma's `{:induction false}`), and adding a lever is no finding."""
        off = "module {:disableNonlinearArithmetic} Q04_ProofCraft {"
        self.rep(self.CORE, "module Q04_ProofCraft {", off)
        files = self.pin_files()
        self.assertEqual(files[self.CORE].get("frozen_levers"),
                         ["module Q04_ProofCraft {:disableNonlinearArithmetic}"])
        self.assertNotIn("frozen_levers", files[self.RS])
        self.assertEqual(self.check()[0], 0)
        shipped = (self.root / self.CORE).read_text()
        self.rep(self.CORE, off, "module Q04_ProofCraft {")
        rc, out = self.check()
        self.assertEqual(rc, 1, out)
        self.assertIn("Q04_ProofCraft.dfy:0: freeze-lever-removed — module "
                      "Q04_ProofCraft {:disableNonlinearArithmetic}", out)
        self.assertEqual(out.count("freeze-"), 1, out)     # no statement changed
        frozen = self.root / "frozen.dfy"
        frozen.write_text(shipped)
        rc, out, err = C.tool("specfreeze", "--against", frozen, self.root / self.CORE,
                              root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("freeze-lever-removed", out)
        (self.root / self.CORE).write_text(shipped.replace(
            off, "module {:disableNonlinearArithmetic} {:vcs_split_on_every_assert} "
            "Q04_ProofCraft {"))
        self.assertEqual(self.check()[0], 0)                # an added lever is no finding
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-lev-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, tmp, True)
        body = "module Toy {\n  lemma %sL(n: nat)\n    ensures n + 0 == n\n  {\n  }\n}\n"
        (tmp / "frozen.dfy").write_text(body % "{:induction false} ")
        for name, text, rc_want in (("kept.dfy", body % "{:induction false} ", 0),
                                    ("gone.dfy", body % "", 1)):
            (tmp / name).write_text(text)
            rc, out, err = C.tool("specfreeze", "--against", tmp / "frozen.dfy", tmp / name,
                                  root=self.root)
            self.assertEqual(rc, rc_want, (name, out + err))
        self.assertIn("gone.dfy:0: freeze-lever-removed — Toy.L {:induction false}", out)

    def test_report_strict_runs_the_lever_freeze(self):
        """DV5c (Δ199's open item): firsttry --report --strict reports a removed
        automation-off lever, as specfreeze --check does, and fails on it."""
        off = "module {:disableNonlinearArithmetic} Q04_ProofCraft {"
        self.rep(self.CORE, "module Q04_ProofCraft {", off)
        self.pin_files()
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertIn("levers removed 0", out, out + err)
        self.assertNotIn(": lever:", out)
        self.rep(self.CORE, off, "module Q04_ProofCraft {")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"  {self.CORE}:0: lever: freeze-lever-removed — module Q04_ProofCraft "
                      "{:disableNonlinearArithmetic}", out)
        self.assertIn("levers removed 1", out)
        # the plain report does not run it
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", root=self.root)
        self.assertNotIn(": lever:", out)

    def test_a_dafny_statement_trigger_is_frozen(self):
        """DV5c (Δ204 item 9): a trigger written in a Dafny statement clause is part
        of the statement, as a Verus `#[trigger]` is: adding, moving or removing
        one is freeze-changed; one in a proof line is not. Before, a clause's
        top-level trigger was dropped and a parenthesized one kept."""
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-trig-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, tmp, True)
        body = ("module Toy {\n  function F(k: nat): nat { k + 1 }\n"
                "  lemma L(n: nat)\n    requires forall k: nat %s:: F(k) > 0\n"
                "    ensures F(n) > 0\n  {\n    %s\n  }\n}\n")
        (tmp / "frozen.dfy").write_text(body % ("", "assert F(n) > 0;"))
        for name, text, rc_want in (
                ("same.dfy", body % ("", "assert F(n) > 0;"), 0),
                ("proof.dfy", body % ("", "forall k: nat {:trigger F(k)} ensures F(k) > 0 { }"),
                 0),
                ("added.dfy", body % ("{:trigger F(k)} ", "assert F(n) > 0;"), 1)):
            (tmp / name).write_text(text)
            rc, out, err = C.tool("specfreeze", "--against", tmp / "frozen.dfy", tmp / name,
                                  root=self.root)
            self.assertEqual(rc, rc_want, (name, out + err))
        self.assertIn("freeze-changed — Toy.L", out)
        h = core.D.spec_hash_source
        one = body % ("{:trigger F(k)} ", "")
        self.assertNotEqual(h(one)["Toy.L"], h(body % ("", ""))["Toy.L"])
        self.assertNotEqual(h(one)["Toy.L"], h(body % ("{:trigger F(k + 1)} ", ""))["Toy.L"])
        # other attributes stay out of the statement
        self.assertEqual(h(body.replace("lemma L", "lemma {:isolate_assertions} L") %
                           ("", ""))["Toy.L"], h(body % ("", ""))["Toy.L"])

    def test_against_reports_an_opacity_change(self):
        """--against (hash mode, static): a Dafny declaration whose statement is
        unchanged but whose opacity is not is freeze-changed; the Verus
        attribute is part of the statement already."""
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-opq-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, tmp, True)
        body = "module Toy {\n  %sfunction Twice(x: nat): nat\n  {\n    x + x\n  }\n}\n"
        (tmp / "frozen.dfy").write_text(body % "opaque ")
        for name, text, rc_want in (("same.dfy", body % "opaque ", 0),
                                    ("attr.dfy", body.replace("%sfunction", "function {:opaque}"),
                                     0),
                                    ("open.dfy", body % "", 1)):
            (tmp / name).write_text(text)
            rc, out, err = C.tool("specfreeze", "--against", tmp / "frozen.dfy", tmp / name,
                                  root=self.root)
            self.assertEqual(rc, rc_want, (name, out + err))
            if rc_want:
                self.assertIn(f"{name}:2: freeze-changed — Toy.Twice: the statement differs "
                              "from the frozen one (its opacity)", out)
        vbody = ("use vstd::prelude::*;\nverus! {\n%spub open spec fn twice(x: nat) -> nat {\n"
                 "    x + x\n}\n} // verus!\n")
        (tmp / "frozen.rs").write_text(vbody % "#[verifier::opaque]\n")
        (tmp / "open.rs").write_text(vbody % "")
        rc, out, err = C.tool("specfreeze", "--against", tmp / "frozen.rs", tmp / "open.rs",
                              root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("freeze-changed", out)

    PY_TEXT = ('"""Toy learner Python file (tests). Not course content."""\n\n\n'
               "class Tally:\n    def add(self, k: int = 1) -> None:\n"
               '        raise NotImplementedError("Q06.H9py")\n\n\n'
               "def double(x: int) -> int:\n"
               '    """Twice x."""\n    raise NotImplementedError("Q06.H8py")\n')

    def test_python_statements(self):
        """DV3a follow-up: the registry's harness files are frozen by their
        signatures (dvl.python.spec_hash); filling a hole, or a docstring
        edit, is no change. Python enters at Q06, so the real Q06 record is
        armed here, its harness path holding an invented toy file (none of
        Q06's other files exists in this root, so none is pinned)."""
        reg = self.root / "MODULES.toml"
        text = reg.read_text()
        s = text.index('[[module]]\nid = "Q06"')
        e = text.find("\n[[", s + 1)
        reg.write_text(text[:s] + text[s:e].replace('status = "planned"', 'status = "authoring"', 1)
                       + text[e:])
        py = core.record(self.root, "Q06")["harness"][0]
        (self.root / py).parent.mkdir(parents=True)
        (self.root / py).write_text(self.PY_TEXT)
        files = self.pin_files("Q06")
        self.assertEqual(list(files), [py])
        self.assertEqual(files[py]["lang"], "py")
        self.assertEqual(sorted(files[py]["statements"]), ["Tally", "Tally.add", "double"])
        rc, out, err = C.tool("specfreeze", "--hash", self.root / py, root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn(f"{py}:9: double sha256 ", out)
        self.rep(py, '    """Twice x."""\n    raise NotImplementedError("Q06.H8py")\n',
                 '    """Two times x."""\n    return 2 * x\n')
        self.rep(py, '        raise NotImplementedError("Q06.H9py")\n', "        pass\n")
        self.assertEqual(self.check("Q06")[0], 0)
        saved = (self.root / py).read_text()
        for old, new in (("def double(x: int) -> int:", "def double(x: int) -> float:"),
                         ("def double(x: int)", "def double(x: int, y: int = 0)"),
                         ("k: int = 1", "k: int = 2")):
            self.rep(py, old, new)
            rc, out = self.check("Q06")
            self.assertEqual(rc, 1, (old, out))
            self.assertIn("freeze-changed", out)
            (self.root / py).write_text(saved)
        self.rep(py, "def double(", "def twice(")
        rc, out = self.check("Q06")
        self.assertIn(f"{py}:0: freeze-missing — double", out)
        (self.root / py).write_text("def broken(:\n")
        rc, out = self.check("Q06")
        self.assertEqual(rc, 1, out)
        self.assertIn(f"{py}:1: freeze-parse-error — (file)", out)


# =====================================================================================
# reference_lint.py (reads twins, runs no verifier)
# =====================================================================================

class ReferenceLint(RootCase):
    def setUp(self):
        super().setUp()
        shutil.copytree(REFERENCE, self.root / "Solutions")

    def lint(self):
        return C.tool("reference_lint.py", root=self.root, env={"CI": "true"})

    def test_bin_tree_exempt(self):
        """A Verus twin reached from its crate's binary root (CRATE_BINS: R16's rexc and
        its trust-report module) is exempt from the outside-verus rule; a lib module is not."""
        rl = C.load_script("reference_lint")
        unit = self.root / "verus/r/r16_capstone/src"
        unit.mkdir(parents=True)
        (unit / "main.rs").write_text("mod trust_report;\nfn main() {}\n", encoding="utf-8")
        (unit / "trust_report.rs").write_text("pub fn f() {}\n", encoding="utf-8")
        (unit / "lib.rs").write_text("pub fn g() {}\n", encoding="utf-8")
        L = types.SimpleNamespace(root=self.root, exercises={"R16": [
            "verus/r/r16_capstone/src/lib.rs", "verus/r/r16_capstone/src/trust_report.rs"]})
        tp = self.root / "Solutions/verus/r/r16_capstone/src/trust_report.rs"
        self.assertEqual(rl.bin_tree_exempt(L, "R16", "verus/r/r16_capstone/src/trust_report.rs",
                                            "v", tp), {"test_files": [tp]})
        self.assertEqual(rl.bin_tree_exempt(L, "R16", "verus/r/r16_capstone/src/lib.rs", "v", tp), {})
        self.assertEqual(rl.bin_tree_exempt(L, "R15", "verus/r/r16_capstone/src/trust_report.rs",
                                            "v", tp), {})

    def test_firsttry_bin_tree_files(self):
        """firsttry's learner lint (--lint-hollow) exempts the same binary-tree files:
        a module reached from a CRATE_BINS [[bin]] root is the tool's trusted shell; a lib
        module, or a bin target not in CRATE_BINS, is not."""
        unit = self.root / "verus/r/r16_capstone"
        (unit / "src").mkdir(parents=True)
        (unit / "Cargo.toml").write_text(
            '[package]\nname = "r16_capstone"\nversion = "0.1.0"\n\n[lib]\npath = "src/lib.rs"\n\n'
            '[[bin]]\nname = "rexc"\npath = "src/main.rs"\n', encoding="utf-8")
        (unit / "src/main.rs").write_text("mod trust_report;\nfn main() {}\n", encoding="utf-8")
        (unit / "src/trust_report.rs").write_text("pub fn f() {}\n", encoding="utf-8")
        (unit / "src/lib.rs").write_text("pub fn g() {}\n", encoding="utf-8")
        got = {p.name for p in firsttry.bin_tree_files(self.root, "verus/r/r16_capstone")}
        self.assertEqual(got, {"main.rs", "trust_report.rs"})
        kinds = lambda rel: {f.kind for f in firsttry.lint_file(self.root, rel)}
        self.assertNotIn("outside-verus", kinds("verus/r/r16_capstone/src/trust_report.rs"))
        self.assertIn("outside-verus", kinds("verus/r/r16_capstone/src/lib.rs"))
        (unit / "Cargo.toml").write_text(
            '[package]\nname = "r16_capstone"\nversion = "0.1.0"\n\n[lib]\npath = "src/lib.rs"\n\n'
            '[[bin]]\nname = "other"\npath = "src/main.rs"\n', encoding="utf-8")
        self.assertEqual(firsttry.bin_tree_files(self.root, "verus/r/r16_capstone"), [])

    def test_refused_without_author_context(self):
        rc, out, err = C.tool("reference_lint.py", root=self.root)
        self.assertEqual(rc, 3, err)
        self.assertEqual(out, "")

    def test_clean_twins(self):
        rc, out, err = self.lint()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("reference_lint: 0 finding(s); 8 twin(s) in 1 module(s)", out)

    def test_open_frames(self):
        """QPLAN §6 Q22 (DV3a integration): a twin whose header region adds
        frame clauses is no statement difference; a twin that drops or changes
        a shipped clause still is."""
        core = SpecFreeze.CORE
        self.rep(core, "  function Sum", SpecFreeze.BOX)
        twin = self.root / "Solutions" / core
        twin.write_text(twin.read_text().replace("  function Sum", SpecFreeze.TWIN_BOX, 1))
        rc, out, err = self.lint()
        self.assertEqual(rc, 0, out + err)
        text = twin.read_text()
        for old, new in (("      ensures a[0] == 0\n      // @hole-begin", "      // @hole-begin"),
                         ("      requires a.Length > 0\n      // @hole-begin",
                          "      requires a.Length > 1\n      // @hole-begin")):
            twin.write_text(text.replace(old, new, 1))
            rc, out, err = self.lint()
            self.assertEqual(rc, 1, (old, out + err))
            self.assertIn("statement-differs", out)
        twin.write_text(text)

    def test_opacity(self):
        """DV3a follow-up: a Dafny twin whose declaration differs from the
        learner's only by its opacity differs in statement (as specfreeze);
        the two spellings of opacity are one statement."""
        core = SpecFreeze.CORE
        twin = self.root / "Solutions" / core
        text = twin.read_text()
        line = text.split("\n").index("  function Sum(n: nat): nat") + 1
        twin.write_text(text.replace("  function Sum", "  opaque function Sum", 1))
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"Solutions/{core}:{line}: statement-differs", out)
        self.rep(core, "  function Sum", "  function {:opaque} Sum")
        rc, out, err = self.lint()
        self.assertEqual(rc, 0, out + err)

    def test_python_twin(self):
        """DV3a follow-up: a harness (learner Python) file needs a twin, which
        is compared by names and parameters and gets the Python reference
        lint (a hole left in it is a finding). Python enters at Q06, so the
        real Q06 record is armed here with an invented toy file at its
        harness path (none of Q06's other files exists in this root)."""
        reg = self.root / "MODULES.toml"
        text = reg.read_text()
        s = text.index('[[module]]\nid = "Q06"')
        e = text.find("\n[[", s + 1)
        reg.write_text(text[:s] + text[s:e].replace('status = "planned"', 'status = "authoring"', 1)
                       + text[e:])
        py = core.record(self.root, "Q06")["harness"][0]
        twin = self.root / "Solutions" / py
        (self.root / py).parent.mkdir(parents=True)
        twin.parent.mkdir(parents=True)
        (self.root / py).write_text(SpecFreeze.PY_TEXT)
        good = ('"""Toy twin (tests; Reference Solution). Not course content."""\n\n\n'
                "class Tally:\n    def add(self, k: int = 1) -> None:\n        self.n = k\n\n\n"
                "def double(x: int) -> int:\n    \"\"\"Twice x.\"\"\"\n    return x + x\n")
        twin.write_text(good)
        rc, out, err = self.lint()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("reference_lint: 0 finding(s); 9 twin(s) in 2 module(s)", out)
        for bad, want in (
                (good.replace("    return x + x\n", '    raise NotImplementedError("Q06.H8py")\n'),
                 f"Solutions/{py}:11: hole"),
                (good.replace("def double(x: int)", "def double(y: int)"),
                 f"{py}:9: declaration-missing"),
                (good.replace("def double(x: int) -> int", "def double(x: float) -> int"),
                 f"Solutions/{py}:9: statement-differs"),
                (good.replace("k: int = 1", "k: int = 0"), f"Solutions/{py}:5: statement-differs"),
                (good.replace("Reference Solution", "reference"), f"Solutions/{py}:1: twin-header"),
                (good.replace('"""\n\n\n', '"""\nimport numpy\n\n', 1),
                 f"Solutions/{py}:2: import-outside-tier")):
            twin.write_text(bad)
            rc, out, err = self.lint()
            self.assertEqual(rc, 1, (want, out + err))
            self.assertIn(want, out)
        twin.unlink()
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"Solutions/{py}:0: twin-missing", out)
        orphan = self.root / "Solutions" / "harness" / "q" / "fvh_q" / "q99_toy.py"
        orphan.write_text(good)
        twin.write_text(good)
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Solutions/harness/q/fvh_q/q99_toy.py:0: twin-orphan", out)

    def test_no_armed_module(self):
        """Every module planned: no reference file is a loud pass; reference
        files are still walked for reserved names; no module at all fails."""
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-idle-", dir=C.TMP_BASE))
        try:
            (tmp / "MODULES.toml").write_text(C.plan_real_modules(
                (C.ROOT / "MODULES.toml").read_text()))
            run = lambda *a: C.tool("reference_lint.py", *a, root=tmp,  # noqa: E731
                                    env={"CI": "true"})
            for args in ((), ("--allow-empty",)):
                rc, out, err = run(*args)
                self.assertEqual(rc, 0, (args, out, err))
                self.assertRegex(out, r"^reference_lint: no armed module: nothing to check "
                                      r"\(all \d+ module\(s\) in MODULES.toml are planned\); no "
                                      r"reference file: passing loudly\n$")
            (tmp / "Solutions" / "spikes").mkdir(parents=True)
            (tmp / "Solutions" / "spikes" / "solutions_policy.dfy").write_text("module M {}\n")
            rc, out, err = run()
            self.assertEqual(rc, 1, out + err)
            self.assertIn("Solutions/spikes/solutions_policy.dfy", out)
            self.assertIn("reserved-name", out)
            (tmp / "MODULES.toml").write_text("# no module\n")
            rc, out, err = run()
            self.assertEqual(rc, 3, out + err)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_findings_locations_only(self):
        S = "Solutions/"
        twin = S + "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
        self.rep(twin, "ensures 2 * Sum(n) == n * (n + 1)", "ensures 2 * Sum(n) >= n")
        self.rep(twin, "  function Sum", "  lemma Extra()\n    ensures true\n  {\n  }\n\n"
                                         "  // reference-only: a helper the learner invents\n"
                                         "  lemma Helper()\n    ensures true\n  {\n  }\n\n"
                                         "  function Sum")
        self.rep(S + "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "  // uses: lemma-call\n", "")
        self.rep(S + "dafny/checks/Q04_checks.dfy", "expect Twice(0) == 0;",
                 "// SLOT: expect Twice(0) == ???;")
        rs = S + "verus/q/q04_proof_craft/src/lib.rs"
        self.rep(rs, "        // did: the product step of the induction\n", "")
        self.rep(rs, "pub proof fn h1(x: nat)\n    ensures\n        x + 0 == x,\n{\n}",
                 "pub proof fn h1(x: nat)\n    ensures\n        x + 0 == x,\n{\n    admit();\n}")
        self.rep(S + "slots/Q04.slots", 'P2dv = "verified 3"\n', "")
        (self.root / S / "verus/q/q04_proof_craft/src/old.rs").write_text("// orphan\n")
        os.remove(self.root / S / "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy")
        bad = self.root / S / "spikes" / "solutions_policy"
        bad.mkdir(parents=True)
        (bad / "lib.rs").write_text("use solutions_first::x;\n")
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        core_t, exit_t = twin, S + "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy"
        checks_t = S + "dafny/checks/Q04_checks.dfy"
        L = self.line_of
        for want in (f"{core_t}:{L(core_t, 'lemma SumFormula')}: statement-differs",
                     f"{core_t}:{L(core_t, 'lemma Extra()')}: declaration-extra",
                     f"{exit_t}:{L(exit_t, '// item: Q04.X2d')}: marker-mismatch",
                     f"{checks_t}:{L(checks_t, 'SLOT: expect Twice(0)')}: slot-leftover",
                     f"{checks_t}:{L(checks_t, 'SLOT: expect Twice(0)')}: slot-not-enabled",
                     f"{rs}:{L(rs, 'by (nonlinear_arith)')}: receipt-missing",
                     f"{rs}:{L(rs, 'admit();')}: admit",
                     f"{rs}:{L(rs, '// item: Q04.P2dv')}: answer-missing",
                     "Solutions/verus/q/q04_proof_craft/src/old.rs:0: twin-orphan",
                     "Solutions/dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy:0: twin-missing",
                     "Solutions/spikes/solutions_policy:0: reserved-name",
                     "Solutions/spikes/solutions_policy/lib.rs:1: reserved-name"):
            self.assertIn(want, out)
        self.assertNotIn("Helper", out)
        for line in out.strip().splitlines()[:-1]:          # `path:line: rule` only
            self.assertRegex(line, r"^[\w./-]+:\d+: [a-z-]+$")

    def test_twin_only_declaration_in_a_learner_region(self):
        """D92 (Δ310): a declaration the twin adds inside an item's
        @hole-begin/@hole-end region is the learner's only when the item's
        admissible row says `writes = "module"` (R08.H1/H4's engines). Inside
        an ordinary annotation region, and outside every region, it is
        extra."""
        S = "Solutions/"
        twin = S + "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
        self.rep(twin, "  function Sum", "  // @hole-begin Q04.H1d\n"
                                         "  lemma LearnerWritten()\n    ensures true\n  {\n  }\n"
                                         "  // @hole-end Q04.H1d\n\n"
                                         "  lemma NotInARegion()\n    ensures true\n  {\n  }\n\n"
                                         "  function Sum")
        L = self.line_of
        inside = f"{twin}:{L(twin, 'lemma LearnerWritten()')}: declaration-extra"
        outside = f"{twin}:{L(twin, 'lemma NotInARegion()')}: declaration-extra"
        # an ordinary region (Q04.H1d's row carries no `writes`): both are extra
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertIn(inside, out)
        self.assertIn(outside, out)
        # a module-writing item: the declaration inside its region is the learner's
        reg = self.root / "MODULES.toml"
        text = reg.read_text()
        at = text.index("admissible = {}", text.index('id = "Q04"'))
        reg.write_text(text[:at] + 'admissible = { "Q04.H1d" = { admitted = true, minutes = 5, '
                       'fallback = "", writes = "module" } }' + text[at + len("admissible = {}"):])
        rc, out, err = self.lint()
        self.assertEqual(rc, 1, out + err)
        self.assertNotIn(inside, out)
        self.assertIn(outside, out)

    def test_slot_sidecar_flagged(self):
        sc = self.root / "expected" / "specimens" / "Q04" / "P4d.dfy.specimen.expect"
        sc.parent.mkdir(parents=True)
        sc.write_text("command: verify\nexit: 4\n")
        ok = self.root / "expected" / "specimens" / "Q04" / "C2d.dfy.specimen.expect"
        ok.write_text("command: verify\nexit: 4\n")       # a card: no slot, may be pinned
        for args in ((), ("--module", "Q04")):
            rc, out, err = C.tool("reference_lint.py", *args, root=self.root, env={"CI": "true"})
            self.assertEqual(rc, 1, out + err)
            self.assertIn("expected/specimens/Q04/P4d.dfy.specimen.expect:0: sidecar-on-slot-file",
                          out)
            self.assertNotIn("C2d.dfy.specimen.expect", out)

    def test_declaration_missing_and_order(self):
        twin = "Solutions/verus/q/q04_proof_craft/src/exit.rs"
        text = (self.root / twin).read_text()
        a = text.index("// item: Q04.X1v")
        b = text.index("// item: Q04.X2v")
        c = text.index("} // verus!")
        (self.root / twin).write_text(text[:a] + text[b:c] + text[a:b] + text[c:])
        rc, out, err = self.lint()
        self.assertIn(f"{twin}:", out)
        self.assertIn("marker-order", out)
        self.assertIn("declaration-order", out)
        self.rep("Solutions/dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy",
                 "  function Double(n: nat): nat { n + n }\n", "")
        rc, out, err = self.lint()
        self.assertIn("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy:5: declaration-missing", out)


# =====================================================================================
# Count pins (Δ11): the static half (vcheck's shared core)
# =====================================================================================

class CountPins(RootCase):
    CORE = "dafny/Q/Q04_ProofCraft/core"
    STD = "dafny/Q/Q04_ProofCraft/std"
    CRATE = "verus/q/q04_proof_craft"

    def pin(self, entries=None):
        entries = entries or [
            (self.CORE, "dafny", 7, ["Q04_ProofCraft.H1", "Q04_ProofCraft.Sum",
                                     "Q04_ProofCraft.SumFormula"]),
            (self.STD, "dafny", 3, ["Q04_Library.H2"]),
            (self.CRATE, "verus", 6, ["h1", "sum", "sum_formula", "twice"])]
        (self.root / "expected").mkdir(exist_ok=True)
        core.counts_path(self.root, "Q04").write_text(core.render_counts("Q04", entries))

    def result(self, lang, target, verdict="verified", count=7, per=None, stage="verify"):
        return core.common.Result(lang, str(self.root / target), 0, verdict, stage, count, [], [],
                                  [], dict(per or {}))

    def test_contract_symbols(self):
        self.assertEqual(set(core.contract_symbols(self.root, self.CORE, "d")),
                         {"Q04_ProofCraft.H1", "Q04_ProofCraft.Sum", "Q04_ProofCraft.SumFormula"})
        self.assertEqual(set(core.contract_symbols(self.root, self.STD, "d")), {"Q04_Library.H2"})
        # p11 has no contract; the #[cfg(test)] module is left out
        self.assertEqual(set(core.contract_symbols(self.root, self.CRATE, "v")),
                         {"h1", "sum", "sum_formula", "twice"})

    def test_trait_impl_task_identity_and_missing_task(self):
        path = self.root / self.CRATE / "src/lib.rs"
        path.write_text('''use vstd::prelude::*;
verus! {
pub trait Model { fn run(&self) -> (b: bool) ensures b; }
pub struct Engine { }
impl Model for Engine {
    fn run(&self) -> (b: bool) ensures b, { true }
}
}
''')
        symbols = core.contract_symbols(self.root, self.CRATE, "v")
        self.assertIn("Engine::run", symbols)
        self.assertNotIn("<Engine as Model>::run", symbols)
        # Freeze still identifies the exact trait implementation separately.
        self.assertIn("<Engine as Model>::run", core.V.spec_hash(path))
        self.pin([(self.CRATE, "verus", 1, ["Engine::run"])])
        good = core.apply_count_pin(self.result("verus", self.CRATE, count=1,
                                   per={"Engine::run": "verified"}),
                                   self.root / self.CRATE, self.root)
        self.assertEqual((good.verdict, good.findings), ("verified", []))
        missing = core.apply_count_pin(self.result("verus", self.CRATE, count=1,
                                      per={"unrelated": "verified"}),
                                      self.root / self.CRATE, self.root)
        self.assertIn("pinned-symbol-missing", {f.kind for f in missing.findings})

    def test_trait_impl_hole_holds_task_identity(self):
        path = self.root / self.CRATE / "src/lib.rs"
        text = '''use vstd::prelude::*;
verus! {
pub struct Engine { }
impl Model for Engine {
 fn run(&self) -> (b: bool) ensures b,
 { assume(false); true }
}
}
'''
        path.write_text(text)
        line = next(i for i, s in enumerate(text.splitlines(), 1) if "assume(false)" in s)
        hole = core.common.Hole(str(path), line, 1, "assume", "H1")
        self.assertEqual(core.hole_held_symbols(self.root, self.CRATE, "verus", [hole]),
                         {"Engine::run"})

    def test_trait_impl_ambiguous_task_identity_refused(self):
        path = self.root / self.CRATE / "src/lib.rs"
        path.write_text('''use vstd::prelude::*;
verus! {
pub struct Engine { }
impl First for Engine { fn run(&self)->(b:bool) ensures b, { true } }
impl Second for Engine { fn run(&self)->(b:bool) ensures b, { true } }
}
''')
        with self.assertRaisesRegex(core.Refusal, "ambiguous verification task identity"):
            core.contract_symbols(self.root, self.CRATE, "v")

    def test_unit_of(self):
        r = self.root
        for path, want in ((self.CORE, ("Q04", self.CORE)),
                           (f"{self.CORE}/Q04_ProofCraft.dfy", ("Q04", self.CORE)),
                           (f"{self.CRATE}/src/lib.rs", ("Q04", self.CRATE)),
                           (f"{self.CRATE}/src/tests.rs", ("Q04", self.CRATE)),
                           (f"Solutions/{self.STD}", ("Q04", self.STD)),
                           (f"{self.CRATE}/src/exit.rs", None),            # a standalone file
                           ("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", None),
                           ("dafny/checks/Q04_checks.dfy", None),
                           ("specimens/Q04/P4d.dfy.specimen", None)):
            self.assertEqual(core.unit_of(r / path, r), want, path)

    def test_learner_gate(self):
        self.pin()
        full = {"Q04_ProofCraft.H1": "verified", "Q04_ProofCraft.Sum": "verified",
                "Q04_ProofCraft.SumFormula": "verified", "Q04_ProofCraft.CheckSum": "verified"}
        res = core.apply_count_pin(self.result("dafny", self.CORE, per=full), self.root / self.CORE,
                                   self.root)
        self.assertEqual((res.verdict, res.findings), ("verified", []))
        gone = {k: v for k, v in full.items() if k != "Q04_ProofCraft.SumFormula"}
        res = core.apply_count_pin(self.result("dafny", self.CORE, count=6, per=gone),
                                   self.root / f"{self.CORE}/Q04_ProofCraft.dfy", self.root)
        self.assertEqual(res.verdict, "failed")
        self.assertEqual([(f.kind, f.message.split(":")[0]) for f in res.findings],
                         [("pinned-symbol-missing", "Q04_ProofCraft.SumFormula")])
        res = core.apply_count_pin(self.result("dafny", self.CORE, count=2, per=full),
                                   self.root / self.CORE, self.root)
        self.assertEqual([f.kind for f in res.findings], ["count-below-pin"])
        res = core.apply_count_pin(self.result("verus", self.CRATE, count=4,
                                               per={"h1": "verified", "sum": "verified",
                                                    "twice": "verified", "p11": "verified"}),
                                   self.root / self.CRATE, self.root)
        self.assertEqual([(f.kind, f.message.split(":")[0]) for f in res.findings],
                         [("pinned-symbol-missing", "sum_formula")])
        # DV5c: a pinned declaration still there as a counted hole (a bodyless lemma
        # runs no task) is held by its hole, not missing; a hole elsewhere holds nothing
        src = (self.root / self.CORE / "Q04_ProofCraft.dfy").read_text().split("\n")
        ln = next(i for i, x in enumerate(src, 1) if "lemma SumFormula" in x)
        held = self.result("dafny", self.CORE, count=6, per=gone)
        held.holes = [core.common.Hole(str(self.root / self.CORE / "Q04_ProofCraft.dfy"), ln + 1,
                                       3, "bodyless-method", "Q04.H1d")]
        res = core.apply_count_pin(held, self.root / self.CORE, self.root)
        self.assertNotIn("pinned-symbol-missing", [f.kind for f in res.findings])
        far = self.result("dafny", self.CORE, count=6, per=gone)
        far.holes = [core.common.Hole(str(self.root / self.CORE / "Q04_ProofCraft.dfy"), 1, 1,
                                      "assume", "Q04.H1d")]
        res = core.apply_count_pin(far, self.root / self.CORE, self.root)
        self.assertIn("pinned-symbol-missing", [f.kind for f in res.findings])
        vsrc = (self.root / self.CRATE / "src" / "lib.rs").read_text().split("\n")
        vln = next(i for i, x in enumerate(vsrc, 1) if "fn sum_formula" in x)
        vheld = self.result("verus", self.CRATE, count=4,
                            per={"h1": "verified", "sum": "verified", "twice": "verified"})
        vheld.holes = [core.common.Hole(str(self.root / self.CRATE / "src" / "lib.rs"), vln, 1,
                                        "external_body", "Q04.H2v")]
        res = core.apply_count_pin(vheld, self.root / self.CRATE, self.root)
        self.assertEqual([f.kind for f in res.findings], [])
        # a run that stopped before verification is left alone
        res = core.apply_count_pin(self.result("dafny", self.CORE, "failed", None, {}, "resolve"),
                                   self.root / self.CORE, self.root)
        self.assertEqual(res.findings, [])
        self.assertEqual(core.pinned_min_verified(self.root / self.CRATE, self.root), 4)

    def test_reference_gate_and_missing_pins(self):
        self.pin()
        per = {"Q04_Library.H2": "verified", "QG_L1_BigNat.BASE": "verified"}
        res = core.apply_count_pin(self.result("dafny", f"Solutions/{self.STD}", count=3, per=per),
                                   self.root / "Solutions" / self.STD, self.root, reference=True)
        self.assertEqual((res.verdict, res.findings), ("verified", []))
        res = core.apply_count_pin(self.result("dafny", f"Solutions/{self.STD}", count=4, per=per),
                                   self.root / "Solutions" / self.STD, self.root, reference=True)
        self.assertEqual([f.kind for f in res.findings], ["count-pin-stale"])
        self.assertEqual(res.verdict, "failed")
        self.pin([(self.CORE, "dafny", 7, ["Q04_ProofCraft.H1"])])
        res = core.apply_count_pin(self.result("dafny", self.STD, count=3, per=per),
                                   self.root / self.STD, self.root)
        self.assertEqual([f.kind for f in res.findings], ["count-pin-missing"])
        core.counts_path(self.root, "Q04").write_text("schema = 1\nmodule = \"Q04\"\n")
        res = core.apply_count_pin(self.result("dafny", self.STD, count=3, per=per),
                                   self.root / self.STD, self.root)
        self.assertEqual([f.kind for f in res.findings], ["count-pin-malformed"])
        core.counts_path(self.root, "Q04").unlink()
        res = core.apply_count_pin(self.result("dafny", self.STD, count=3, per=per),
                                   self.root / self.STD, self.root)
        self.assertEqual([f.kind for f in res.findings], ["count-pin-missing"])
        # a file outside every unit has no pin to meet
        res = core.apply_count_pin(self.result("dafny", "dafny/checks/Q04_checks.dfy", per=per),
                                   self.root / "dafny/checks/Q04_checks.dfy", self.root)
        self.assertEqual((res.verdict, res.findings), ("verified", []))

    def test_read_counts(self):
        self.assertEqual(core.read_counts(self.root, "Q04"), (None, []))
        self.pin()
        table, errs = core.read_counts(self.root, "Q04")
        self.assertEqual(errs, [])
        self.assertEqual(table[self.CRATE]["min_verified"], 4)
        core.counts_path(self.root, "Q04").write_text(
            'schema = 1\nmodule = "Q04"\n[[unit]]\npath = "a"\nlang = "dafny"\n'
            'reference_verified = 1\nmin_verified = 2\nsymbols = ["x", "y"]\n'
            '[[unit]]\npath = "b"\nlang = "coq"\n')
        _, errs = core.read_counts(self.root, "Q04")
        self.assertEqual(len(errs), 2, errs)
        self.assertIn("min_verified exceeds reference_verified", errs[0])

    def test_loose_dafny_dir_targets(self):
        spikes = self.root / "Solutions" / "spikes" / "dafny"
        spikes.mkdir(parents=True)
        (spikes / "A.dfy").write_text("module A {}\n")
        t = core.path_target(self.root, spikes, loose_dir=True)
        self.assertEqual((t.lang, t.path), ("d", spikes.resolve()))
        with self.assertRaises(core.Refusal):
            core.path_target(self.root, spikes)                  # only the reference modes
        twin = self.root / "Solutions" / "dafny" / "Q" / "Q04_ProofCraft" / "exit"
        twin.mkdir(parents=True)
        (twin / "Q04_Exit.dfy").write_text("module X {}\n")
        with self.assertRaises(core.Refusal):                   # mirrors a learner directory
            core.path_target(self.root, twin, loose_dir=True)


# =====================================================================================
# update_rubric_pins.sh
# =====================================================================================

class RubricPins(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="dvl-tools-rubric-", dir=C.TMP_BASE))
        (self.root / "scripts").mkdir()
        shutil.copyfile(C.SCRIPTS / "course_mode.sh", self.root / "scripts" / "course_mode.sh")
        (self.root / "paper" / "rubrics").mkdir(parents=True)
        (self.root / "dafny").mkdir()
        (self.root / "dafny" / "a.dfy").write_text("module A {}\n")
        (self.root / "dafny" / "b.dfy").write_text("module B {}\n")
        self.digest_a = hashlib.sha256(b"module A {}\n").hexdigest()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_(self, *args, ci=True):
        return C.tool("update_rubric_pins.sh", *args, root=self.root,
                      env={"CI": "true"} if ci else {})

    def test_cycle(self):
        r = self.root / "paper" / "rubrics" / "Q04_rubric.md"
        r.write_text("# Q04 rubric\n\nSolution pins (scripts/ci.sh compares on every change; "
                     "stale pins fail):\n"
                     "dafny/a.dfy  sha256 PENDING\n"
                     f"dafny/b.dfy  sha256 {'0' * 64} — see note\n"
                     "dafny/gone.dfy  sha256 PENDING\n"
                     f"- `dafny/a.dfy`  sha256 {self.digest_a}\n")
        (self.root / "paper" / "rubrics" / "README.md").write_text(
            "<reference twin path>  sha256 PENDING\n")
        rc, out, err = self.run_("--check", ci=False)
        self.assertEqual(rc, 3, out + err)
        rc, out, err = self.run_("--check")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("MISSING: paper/rubrics/Q04_rubric.md:6: dafny/gone.dfy", out)
        self.assertIn("PENDING: paper/rubrics/Q04_rubric.md:4: dafny/a.dfy", out)
        self.assertIn("STALE: paper/rubrics/Q04_rubric.md:5: dafny/b.dfy", out)
        self.assertNotIn("module A", out)
        before = r.read_text()
        rc, out, err = self.run_()
        self.assertEqual(rc, 1, out + err)                 # the missing target fails loudly
        after = r.read_text()
        self.assertIn(f"dafny/a.dfy  sha256 {self.digest_a}\n", after)
        self.assertIn(f"dafny/b.dfy  sha256 {hashlib.sha256(b'module B {}' + bytes([10])).hexdigest()}"
                      " — see note\n", after)
        self.assertIn("dafny/gone.dfy  sha256 PENDING", after)
        self.assertNotEqual(before, after)
        r.write_text(after.replace("dafny/gone.dfy  sha256 PENDING\n", ""))
        rc, out, err = self.run_("--check")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("all 3 rubric pins current", out)

    def test_bad_path_and_empty(self):
        for args in (("--check",), ("--check", "--allow-empty"), ()):
            rc, out, err = self.run_(*args)
            self.assertEqual(rc, 0, (args, out, err))
            self.assertIn("no rubric file under paper/rubrics/ yet and no armed module needs "
                          "one: nothing to check (passing loudly)", out)
        rc, out, err = self.run_("--check", ci=False)
        self.assertEqual(rc, 3, out + err)                 # the author gate still applies
        # an armed module's rubric is required; a rubric with no pin line fails
        (self.root / "MODULES.toml").write_text(
            '[[module]]\nid = "Q04"\nstatus = "armed"\nrubric = "paper/rubrics/Q04_rubric.md"\n\n'
            '[[module]]\nid = "Q05"\nstatus = "planned"\nrubric = "paper/rubrics/Q05_rubric.md"\n')
        for args in (("--check",), ()):
            rc, out, err = self.run_(*args)
            self.assertEqual(rc, 1, (args, out, err))
            self.assertIn("MISSING RUBRIC: paper/rubrics/Q04_rubric.md (the rubric of armed "
                          "module Q04)", out)
            self.assertNotIn("Q05_rubric", out)
        (self.root / "paper" / "rubrics" / "Q04_rubric.md").write_text("# Q04 rubric\n")
        rc, out, err = self.run_("--check")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("NO PIN: paper/rubrics/Q04_rubric.md", out)
        self.assertNotIn("MISSING RUBRIC", out)
        (self.root / "MODULES.toml").write_text("x = [\n")
        rc, out, err = self.run_("--check")
        self.assertEqual(rc, 3, out + err)
        self.assertIn("MODULES.toml is unreadable", err)
        (self.root / "MODULES.toml").unlink()
        (self.root / "paper" / "rubrics" / "Q04_rubric.md").write_text(
            "../dafny/a.dfy  sha256 PENDING\n")
        rc, out, err = self.run_("--check")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("BAD PATH", out)
        rc, out, err = self.run_("--bogus")
        self.assertEqual(rc, 2, out + err)


# =====================================================================================
# DV2a fix round: the planted and after markers, salted pins (above), the
# shipped-state file pins, code test-outs, the exit thresholds, the open-body
# freeze, the TRIV body, and the usage of vcheck --shipped and --test
# =====================================================================================

def git_baseline(root):
    """Commit a root on `main` and leave HEAD on a new branch `work`: the files
    as they stand become the shipped baseline (the merge base with main)."""
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "shipped")
    git(root, "switch", "-q", "-c", "work")


def add_strand(root, strand):
    p = root / "MODULES.toml"
    data = tomllib.loads(p.read_text())
    have = next(m for m in data["module"] if m["id"] == "Q04")["strands"]
    p.write_text(C._setf(p.read_text(), "Q04", "strands",
                         "[" + ", ".join(f'"{s}"' for s in have + [strand]) + "]"))


PLANTED = ("// item: Q04.P20d S12 verdict\n"
           "// **P20.** A delivery. Answer form: `<species> <instrument>`, in slots/Q04.slots.\n"
           "// SLOT: CHECK P20d\n"
           "module Q04_P20 {\n"
           "  lemma Step(x: nat)\n"
           "    ensures x + 0 == x\n"
           "  {\n"
           "{above}"
           "    assume {:axiom} x + 0 == x;{trail}\n"
           "  }\n"
           "}\n")


class PlantedMarker(RootCase):
    """`// planted: <item id>`: the shipping lints (lint-hollow, reference_lint)
    drop their findings on the covered line of an S12 delivery specimen; the
    instruments (dvl lint, so vcheck and vaudit) still report it."""

    SPEC = "specimens/Q04/P20d.dfy.specimen"

    def setUp(self):
        super().setUp()
        add_strand(self.root, "S12")
        self.rep("slots/Q04.slots", "P2dv = ???\n", "P2dv = ???\nP20d = ???\n")

    def write(self, above="", trail=""):
        (self.root / self.SPEC).write_text(PLANTED.replace("{above}", above)
                                           .replace("{trail}", trail))

    def lint_hollow(self):
        return C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)

    def test_lint_hollow_honours_a_valid_marker_only(self):
        self.write()
        rc, out, err = self.lint_hollow()
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{self.SPEC}:8: lint: assume-axiom", out)
        for above, trail in (("", "  // planted: Q04.P20d"), ("    // planted: Q04.P20d\n", "")):
            self.write(above, trail)
            rc, out, err = self.lint_hollow()
            self.assertEqual(rc, 0, (above, trail, out + err))
            self.assertIn("Q04 lint-hollow: OK", out)
        # the instruments never honour it: the dvl lint (vaudit's) still reports the line
        self.write("", "  // planted: Q04.P20d")
        found = core.D.lint([self.root / self.SPEC], "learner")
        self.assertIn((8, "assume-axiom"), {(f.line, f.kind) for f in found})
        # a marker naming another item, or outside a delivery specimen, is a problem
        self.write("", "  // planted: Q04.P4d")
        rc, out, err = self.lint_hollow()
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{self.SPEC}:8: the `planted:` marker names Q04.P4d, which is no S10 or "
                      "S12 verdict P item of this file", out)
        self.assertIn(f"{self.SPEC}:8: lint: assume-axiom", out)
        self.write()
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "  function Sum",
                 "  // planted: Q04.P20d\n  function Sum")
        rc, out, err = self.lint_hollow()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("a `planted:` marker lives only in an S12 delivery specimen", out)

    def test_reference_lint_honours_it_in_a_delivery_twin(self):
        shutil.copytree(REFERENCE, self.root / "Solutions")
        (self.root / "Solutions/slots/Q04.slots").write_text(
            (self.root / "Solutions/slots/Q04.slots").read_text() + 'P20d = "vacuous witness"\n')
        twin = self.root / "Solutions" / self.SPEC
        self.write("", "  // planted: Q04.P20d")
        enable = lambda s: s.replace("// SLOT: CHECK P20d", "// CHECK P20d")  # noqa: E731
        twin.write_text(enable((self.root / self.SPEC).read_text()))
        rc, out, err = C.tool("reference_lint.py", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        twin.write_text(enable(PLANTED.replace("{above}", "").replace("{trail}", "")))
        rc, out, err = C.tool("reference_lint.py", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"Solutions/{self.SPEC}:8: assume-axiom", out)
        twin.write_text(enable(PLANTED.replace("{above}", "").replace(
            "{trail}", "  // planted: Q04.P99d")))
        rc, out, err = C.tool("reference_lint.py", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"Solutions/{self.SPEC}:8: planted-marker", out)

    def test_an_s10_pipeline_forensic_delivery_takes_a_marker(self):
        # Q15's pipeline-forensic specimens are S10 verdict items (DV5b Q15 lane); any other
        # strand is still refused
        def strands(*extra):
            p = self.root / "MODULES.toml"
            have = next(m for m in tomllib.loads(p.read_text())["module"] if m["id"] == "Q04")
            got = sorted(set(have["strands"]) | set(extra), key=lambda x: int(x[1:]))
            p.write_text(C._setf(p.read_text(), "Q04", "strands",
                                 "[" + ", ".join(f'"{x}"' for x in got) + "]"))
        strands("S9", "S10")
        for strand, ok in (("S10", True), ("S9", False)):
            text = PLANTED.replace("S12 verdict", f"{strand} verdict").replace("{above}", "")
            (self.root / self.SPEC).write_text(text.replace("{trail}", "  // planted: Q04.P20d"))
            rc, out, err = self.lint_hollow()
            self.assertEqual(rc, 0 if ok else 1, (strand, out + err))
            if not ok:
                self.assertIn("which is no S10 or S12 verdict P item of this file", out)


class R04PlantedMarker(unittest.TestCase):
    def test_agent_marker_validates_placement_without_exempting_a_line(self):
        for iid, home in (("R04.A1d", "dafny/R/R04_Specs/agent/R04_AgentProver.dfy"),
                          ("R04.A1v", "verus/r/r04_specs/src/agent.rs")):
            for rel in (home, "Solutions/" + home):
                lines = ["// item: " + iid, "// planted: " + iid, "assume false;"]
                item = {"id": iid, "file": rel, "kind": "A", "line_start": 1, "line_end": 3}
                self.assertEqual(firsttry.sr_planted(lines, rel, [item]), ({}, []))
                # Moving it outside its A block never grants an exemption.
                item["line_end"] = 1
                covered, problems = firsttry.sr_planted(lines, rel, [item])
                self.assertEqual(covered, {})
                self.assertTrue(problems)

    def test_agent_marker_cannot_move_to_another_file_or_item(self):
        rel = "dafny/R/R04_Specs/core/R04_Specs.dfy"
        item = {"id": "R04.A1d", "file": rel, "kind": "A", "line_start": 1, "line_end": 3}
        self.assertTrue(firsttry.sr_planted(["// planted: R04.A1d"], rel, [item])[1])
        rel = "dafny/R/R04_Specs/agent/R04_AgentProver.dfy"
        item.update(file=rel, kind="H")
        self.assertTrue(firsttry.sr_planted(["// planted: R04.A1d"], rel, [item])[1])

    def test_guarded_runtime_demos_need_both_predictions_and_an_exact_home(self):
        lines = ["// after: R04.P1d", "// after: R04.P5d",
                 "expect x > 0; // planted: R04.P5d"]
        for name in ("chapter-p1-d.dfy.specimen", "card-c3d.dfy.specimen",
                     "card-c5dv-d.dfy.specimen", "audit-expect-d.dfy.specimen",
                     "card-c5dv-v.rs.specimen", "audit-assume-v.rs.specimen"):
            rel = "specimens/R04/" + name
            self.assertEqual(firsttry.sr_planted(lines, rel, []), ({3: "R04.P5d"}, []))
            for removed in (0, 1):
                self.assertTrue(firsttry.sr_planted([x for i,x in enumerate(lines) if i != removed], rel, [])[1])
        self.assertTrue(firsttry.sr_planted(lines, "specimens/R04/unlisted.dfy.specimen", [])[1])

    def test_runtime_delivery_exception_is_exact(self):
        rel = "specimens/R04/P5d.dfy.specimen"
        item = {"id": "R04.P5d", "file": rel, "kind": "P", "format": "verdict", "strand": None}
        lines = ["expect x > 0; // planted: R04.P5d"]
        self.assertEqual(firsttry.sr_planted(lines, rel, [item]), ({1: "R04.P5d"}, []))
        item.update(id="R04.P1d")
        self.assertTrue(firsttry.sr_planted(["// planted: R04.P1d"], rel, [item])[1])


class ClauseFreeDefinition(unittest.TestCase):
    SHIPPED = "verus! { pub mod api { pub uninterp spec fn property(x: int) -> bool; } }"

    def compare(self, body):
        path = "probe.rs"
        original, _, opened = core.statement_table(path, "v", text=self.SHIPPED)
        self.assertEqual(opened, ["api::property"])
        old = core.statement_table(path, "v", opened, text=self.SHIPPED)[0]
        new = core.statement_table(path, "v", opened, text=body)[0]
        return old, new

    def test_definition_completion_changes_only_its_open_body(self):
        for expression in ("x >= 0", "false"):
            text = "verus! { pub mod api { pub open spec fn property(x: int) -> bool { " + expression + " } } }"
            old, new = self.compare(text)
            self.assertEqual(old, new)

    def test_signature_and_preconditions_remain_frozen(self):
        for signature in ("property(x: nat) -> bool { true }",
                          "property(x: int) -> int { x }",
                          "property(x: int) -> bool recommends x >= 0, { true }"):
            text = "verus! { pub mod api { pub open spec fn " + signature + " } }"
            old, new = self.compare(text)
            self.assertNotEqual(old, new)

    def test_unopened_definition_remains_part_of_its_statement(self):
        path = "probe.rs"
        a = "verus! { spec fn closed_value() -> int { 1 } }"
        b = "verus! { spec fn closed_value() -> int { 2 } }"
        self.assertNotEqual(core.statement_table(path, "v", text=a)[0],
                            core.statement_table(path, "v", text=b)[0])


DEMO = ("// Card demo Q04.C9d. Open it only after Q04's predictions are recorded.\n"
        "{after}"
        "module Q04_C9 {\n"
        "  method Fails(x: nat)\n"
        "  {\n"
        "    assert x > 1;\n"
        "  }\n"
        "}\n")


class AfterMarker(RootCase):
    """`// after: <item id>` in a card demo: vcheck, vaudit and vcheck --test
    refuse it until that item's first try is recorded (H5); lint-hollow checks
    the line."""

    DEMO = "specimens/Q04/card-c9d.dfy.specimen"

    def write(self, after):
        (self.root / self.DEMO).write_text(DEMO.replace("{after}", after))

    def test_refused_until_the_item_is_recorded(self):
        self.write("// after: Q04.P4d\n")
        for tool, args in (("vcheck", ()), ("vaudit", ()), ("vcheck", ("--test",))):
            rc, out, err = C.tool(tool, *args, self.DEMO, root=self.root)
            self.assertEqual(rc, 3, (tool, args, out, err))
            self.assertIn(f"{self.DEMO} waits for Q04.P4d, whose first try is not recorded", err)
            self.assertIn("scripts/firsttry.sh Q04 --check", err)
            self.assertEqual(out, "")
        t = core.Target("d", (self.root / self.DEMO).resolve(), self.root)
        calib = self.root / "instructor" / "calib"
        calib.mkdir(parents=True, exist_ok=True)
        (calib / "Q04.tsv").write_text("Q04.P4d\tpredict\tfail\t2026-10-04\tx\n")
        core.h5_guard(self.root, t)                  # recorded: the demo may run now
        self.write("// after: Q04.P4d\n// after: Q04.P5d\n")
        with self.assertRaises(core.Refusal) as e:
            core.h5_guard(self.root, t)
        self.assertIn("waits for Q04.P5d", str(e.exception))
        self.write("// after: nonsense\n")
        with self.assertRaises(core.Refusal):
            core.h5_guard(self.root, t)

    def test_lint_hollow_checks_the_line(self):
        self.write("// after: Q04.P4d\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertEqual(rc, 0, out + err)
        for after, want in (("// after: Q04.H1d\n", "`after:` names Q04.H1d, which is no "
                             "prediction item"),
                            ("// after: P4d\n", "`after:` names 'P4d', which is no item id")):
            self.write(after)
            rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
            self.assertEqual(rc, 1, out + err)
            self.assertIn(f"{self.DEMO}:2: {want}", out)
        self.rep("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "  function Sum",
                 "  // after: Q04.P4d\n  function Sum")
        rc, out, err = C.tool("firsttry.py", "Q04", "--lint-hollow", root=self.root)
        self.assertIn("an `after:` line lives only in a specimen", out)

    def test_seal_key_and_sealed_sidecar_text(self):
        self.write("// after: Q04.P4d\n")
        self.assertEqual(pins.seal_key(self.root, self.DEMO), ("Q04", ["Q04.P4d"]))
        self.assertIsNone(pins.seal_key(self.root, "specimens/Q04/C2d.dfy.specimen"))
        full = ["exit: 4", "verdict: failed", "stage: verify", "verified: 0", "holes: 0",
                "card-c9d.dfy.specimen:6:12: error: assertion might not hold"]
        digest = pins.sealed_hash("Q04", ["Q04.P4d"], self.DEMO, full)
        self.assertEqual(digest, hashlib.sha256(
            ("Q04:Q04.P4d:" + self.DEMO + "\n" + "\n".join(full)).encode()).hexdigest())
        text = pins.render_sidecar(self.DEMO, "verify", full, ("Q04", ["Q04.P4d"], digest))
        # DV2b: no output line at all, the diagnostics included (Δ120 Open)
        for leak in ("exit:", "verdict:", "stage:", "holes:", "card-c9d.dfy.specimen:6",
                     "assertion might not hold", "error"):
            self.assertNotIn(leak, text)
        sc = self.root / "x.expect"
        sc.write_text(text)
        command, body = pins.read_sidecar(sc)
        self.assertEqual(command, "verify")
        self.assertEqual(pins.split_sealed(body), (["Q04.P4d"], digest, []))
        self.assertIsNone(pins.split_sealed(["exit: 4"]))
        # a sidecar sealed in the pre-DV2b form shows its diagnostics: flagged
        # statically, before any run
        sc.write_text(text + full[5] + "\n")
        self.assertEqual(pins.split_sealed(pins.read_sidecar(sc)[1])[2], [full[5]])


class OpenBodyFreeze(unittest.TestCase):
    """QPLAN §6 Q7: a Verus spec-fn hole shipped `uninterp` and delivered
    `open` (or `closed`) keeps its statement hash; a real change does not."""

    def table(self, text, open_bodies=()):
        return core.statement_table("x.rs", "v", open_bodies, text=text)[0]

    def test_open_closed_uninterp(self):
        shipped = ("verus! {\npub uninterp spec fn f(s: Seq<u64>) -> nat\n    decreases s.len();\n"
                   "pub open spec fn g(n: nat) -> nat {\n    n\n}\n}\n")
        hashes, _, bodyless = core.statement_table("x.rs", "v", text=shipped)
        self.assertEqual(bodyless, ["f"])
        pinned = self.table(shipped, {"f"})
        for q in ("open", "closed"):
            filled = shipped.replace(
                "pub uninterp spec fn f(s: Seq<u64>) -> nat\n    decreases s.len();",
                f"pub {q} spec fn f(s: Seq<u64>) -> nat\n    decreases s.len(),\n{{\n"
                "    if s.len() == 0 { 0 } else { 1 }\n}")
            self.assertEqual(self.table(filled, {"f"})["f"], pinned["f"], q)
        changed = shipped.replace("decreases s.len();", "decreases s.len() + 1;")
        self.assertNotEqual(self.table(changed, {"f"})["f"], pinned["f"])
        # g is no open-body symbol: open → closed is a change of its statement
        self.assertNotEqual(self.table(shipped.replace("pub open spec fn g", "pub closed spec fn g"),
                                       {"f"})["g"], pinned["g"])


class ExitThresholds(unittest.TestCase):
    """The orchestrator's Q11 decision beside design §7.1's concept tiers."""

    def th(self, mid, tier, passes):
        return firsttry.threshold({"id": mid, "tier": tier}, passes)

    def test_rules(self):
        self.assertEqual(self.th("Q10", "practice-intro", [("Q10.X1d", True), ("Q10.X1v", False)])
                         [:2], (1, 2))
        self.assertEqual(self.th("Q12", "practice-intro", [("Q12.X1d", False),
                                                            ("Q12.X1v", False)])[:2], (1, 2))
        self.assertEqual(self.th("Q13", "practice-intermediate", [("Q13.X1dv", True)])[:2], (1, 1))
        self.assertIsNone(self.th("Q16", "practice-hard", [("Q16.X1d", True)]))
        self.assertTrue(firsttry.exit_rule({"id": "Q17", "tier": "practice-hard"})["reviews"])
        self.assertIn("verifier part plus the reviews", firsttry.REVIEWS_ONLY)
        four = [("R06.X1d", True), ("R06.X2d", True), ("R06.X1v", True), ("R06.X2v", False)]
        need, total, ftxt, ok = self.th("R06", "", four)
        self.assertEqual((need, total, ok), (3, 4, True))
        self.assertEqual(ftxt, "Dafny 2/2 (≥1), Verus 1/2 (≥1)")
        lopsided = [("R11.X1d", True), ("R11.X2d", True), ("R11.X3d", True), ("R11.X1v", False)]
        self.assertFalse(self.th("R11", "", lopsided)[3])      # 3 of 4, none in Verus
        self.assertIsNone(self.th("R07", "", four))            # no exit threshold pinned
        mod = self.th("Q04", "moderate", four)
        self.assertEqual((mod[0], mod[3], mod[2]), (3, True, "Dafny 2/2 (≥1), Verus 1/2 (≥1)"))
        self.assertEqual(self.th("Q01", "survey", [("Q01.X1d", True)] * 13)[:2], (10, 13))


TOUT = ("  // item: Q04.T1dv S5\n"
        "  // ### T1dv · S5 — Write `function Inc(n: nat): nat`, which adds one. Then uncomment\n"
        "  //    the check below it.\n"
        "\n"
        "  // Uncomment as you go:\n"
        "  // lemma IncCheck()\n"
        "  //   ensures Inc(2) == 3\n"
        "  // {\n"
        "  // }\n")


class CodeTestOuts(unittest.TestCase):
    """A code T item's block: empty until the learner writes code beyond what
    shipped (its checks not counted); complete once that code holds no hole;
    predict while its checks stay commented, observed once one is not."""

    STD = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"

    def setUp(self):
        self.root = C.build_root(git=False)
        C.replace_in(self.root / self.STD, "  // item: Q04.T1dv S5\n  const T1 := 0\n", TOUT)
        git_baseline(self.root)

    def tearDown(self):
        C.remove_root(self.root)

    def state(self):
        ctx = firsttry.Ctx(self.root, "Q04")
        it = next(i for i in ctx.items if i["id"] == "Q04.T1dv")
        sit = firsttry.shipped_state(ctx).get("Q04.T1dv")
        why = firsttry.code_t_open(ctx, it, sit)
        return why, (None if why else firsttry.code_t_kind(ctx, it, sit))

    def test_states(self):
        self.assertEqual(self.state(), ("empty", None))
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn("Q04.T1dv  test-out: empty · unrecorded", out)
        self.assertIn("test-outs unattempted 1", out)
        self.assertIn("unrecorded: ", out)
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=self.root)
        self.assertIn("Q04.T1dv  its block holds no attempt yet", out)
        # uncommenting the checks alone is no attempt
        C.replace_in(self.root / self.STD, "  // lemma IncCheck()\n  //   ensures Inc(2) == 3\n"
                     "  // {\n  // }\n", "  lemma IncCheck()\n    ensures Inc(2) == 3\n  {\n  }\n")
        self.assertEqual(self.state(), ("empty", None))
        C.replace_in(self.root / self.STD, "  lemma IncCheck()\n    ensures Inc(2) == 3\n  {\n  }\n",
                     "  // lemma IncCheck()\n  //   ensures Inc(2) == 3\n  // {\n  // }\n")
        C.replace_in(self.root / self.STD, "  // Uncomment as you go:",
                     "  function Inc(n: nat): nat { n + 1 }\n\n  // Uncomment as you go:")
        self.assertEqual(self.state(), (None, ("predict", None)))
        C.replace_in(self.root / self.STD, "  // lemma IncCheck()", "  lemma IncCheck()")
        self.assertEqual(self.state(), (None, ("observed", None)))
        C.replace_in(self.root / self.STD, "  //   ensures Inc(2) == 3\n", "")
        why, (kind, problem) = self.state()
        self.assertIsNone(kind)
        self.assertIn("1 of its 4 shipped check(s) are gone", problem)
        C.replace_in(self.root / self.STD, "  function Inc(n: nat): nat { n + 1 }",
                     "  function Inc(n: nat): nat\n    ensures Inc(n) > n")
        self.assertEqual(self.state()[0], "hole")


class FilePins(RootCase):
    """Schema 2's [[file]] tables: what --pin-counts writes, what pins.py --ci
    checks statically, and vcheck --shipped's refusals before any run. No
    overlay: its card's EXPECT pin would make pins.py --ci run Dafny."""

    overlay = False

    def counts(self, files):
        units = [("dafny/Q/Q04_ProofCraft/core", "dafny", 5, ["Q04_ProofCraft.SumFormula"]),
                 ("dafny/Q/Q04_ProofCraft/std", "dafny", 2, ["Q04_Library.H2"]),
                 ("verus/q/q04_proof_craft", "verus", 6, ["sum_formula"])]
        (self.root / "expected").mkdir(exist_ok=True)
        (self.root / "expected" / "Q04.counts").write_text(core.render_counts("Q04", units, files))

    def listed(self):
        rec = core.record(self.root, "Q04")
        return [(rel, role, {"verdict": "verified", "holes": 1, "errors": 0})
                for rel, role, _ in core.module_pin_files(self.root, rec)]

    def test_roles_and_hygiene(self):
        rec = core.record(self.root, "Q04")
        roles = {rel: role for rel, role, _ in core.module_pin_files(self.root, rec)}
        self.assertEqual(roles, {
            "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy": "exercise",
            "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy": "exercise",
            "verus/q/q04_proof_craft/src/lib.rs": "exercise",
            "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy": "exit",
            "verus/q/q04_proof_craft/src/exit.rs": "exit",
            "dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy": "agent",
            "verus/q/q04_proof_craft/src/agent.rs": "agent"})
        files = self.listed()
        self.counts(files)
        table, errs = core.read_file_pins(self.root, "Q04")
        self.assertEqual((len(table), errs), (7, []))
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        for clean in ("shipped-state", "is pinned as", "is no exercise", "[[file]]"):
            self.assertNotIn(clean, out)
        bad = [f for f in files if not f[0].endswith("agent.rs")]
        bad = [(r, "check" if r.endswith("Q04_Exit.dfy") else role, st) for r, role, st in bad]
        bad.append(("dafny/Q/Q04_ProofCraft/core/Gone.dfy", "exercise", files[0][2]))
        self.counts(bad)
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        self.assertEqual(rc, 1, out + err)
        for want in ("expected/Q04.counts:0: verus/q/q04_proof_craft/src/agent.rs has no "
                     "shipped-state pin; re-pin with vcheck --ref --pin-counts Q04",
                     "expected/Q04.counts:0: dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy is pinned "
                     "as check, but it is Q04's exit file",
                     "expected/Q04.counts:0: dafny/Q/Q04_ProofCraft/core/Gone.dfy is no exercise, "
                     "check, exit or agent file of Q04"):
            self.assertIn(want, out)
        text = (self.root / "expected" / "Q04.counts").read_text()
        (self.root / "expected" / "Q04.counts").write_text(
            text.replace("schema = 2", "schema = 1").split("[[file]]")[0])
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        self.assertIn("expected/Q04.counts:0: Q04 pins no file's shipped state (a schema-1 pin", out)
        self.assertIsNotNone(core.read_counts(self.root, "Q04")[0])  # its units still read

    def test_shipped_refusals_before_any_run(self):
        for args in (("--shipped",), ("--shipped", "Q04", "d", "--gate"),
                     ("--shipped", "Q04", "--ref"), ("--shipped", "Q04", "Q05")):
            rc, out, err = C.tool("vcheck", *args, root=self.root)
            self.assertEqual(rc, 2, (args, out, err))
        rc, out, err = C.tool("vcheck", "--shipped", "Q05", root=self.root)
        self.assertEqual(rc, 3, out + err)                  # planned
        rc, out, err = C.tool("vcheck", "--shipped", "Q04", "v", root=self.root)
        self.assertEqual(rc, 1, out + err)                  # no pin: fails, runs nothing
        self.assertIn("expected/Q04.counts:0: Q04 has no shipped-state pin", out)
        self.assertIn("vcheck --shipped: Q04 (Verus): 0 file(s) checked", out)


class TestModeUsage(RootCase):
    def test_refusals_before_any_run(self):
        for args in (("--name", "X", "dafny/checks/Q04_checks.dfy"),
                     ("--test", "--gate", "dafny/checks/Q04_checks.dfy"),
                     ("--test", "--symbol", "X", "dafny/checks/Q04_checks.dfy"),
                     ("--test", "dafny/checks/Q04_checks.dfy", "--", "--isolate-assertions")):
            rc, out, err = C.tool("vcheck", *args, root=self.root)
            self.assertEqual(rc, 2, (args, out, err))
        shutil.copytree(REFERENCE, self.root / "Solutions")
        rc, out, err = C.tool("vcheck", "--test", "Solutions/dafny/checks/Q04_checks.dfy",
                              root=self.root)
        self.assertEqual(rc, 3, out + err)
        self.assertIn("is reference material", err)
        rc, out, err = C.tool("vcheck", "--test", "specimens/Q04/P4d.dfy.specimen",
                              root=self.root)
        self.assertEqual(rc, 3, out + err)                  # H5: an unrecorded specimen
        # an enabled value slot whose first try is not recorded: its test would answer it
        self.rep("dafny/checks/Q04_checks.dfy", "// SLOT: expect Twice(21) == ???;",
                 "expect Twice(21) == 42;")
        rc, out, err = C.tool("vcheck", "--test", "dafny/checks/Q04_checks.dfy", root=self.root)
        self.assertEqual(rc, 3, out + err)
        self.assertIn("holds the enabled slot(s) of Q04.P8d, whose first try is not recorded", err)
        self.assertEqual(out, "")


class TrivBody(RootCase):
    """firsttry --empty-body passes the item's declared trivial body (its
    twin's `// triv:` lines) to the Verus TRIV mode."""

    def test_declared_and_passed(self):
        shutil.copytree(REFERENCE, self.root / "Solutions")
        twin = self.root / "Solutions" / "verus/q/q04_proof_craft/src/lib.rs"
        twin.write_text(twin.read_text().replace(
            "// item: Q04.H3v S3\n",
            "// item: Q04.H3v S3\n// triv: {\n// triv:     ()\n// triv: }\n", 1))
        ctx = firsttry.Ctx(self.root, "Q04")
        it = next(i for i in ctx.items if i["id"] == "Q04.H3v")
        self.assertEqual(firsttry.declared_triv_body(ctx, it, it["file"]), ("{\n    ()\n}", None))
        h1 = next(i for i in ctx.items if i["id"] == "Q04.H1v")
        self.assertEqual(firsttry.declared_triv_body(ctx, h1, h1["file"]), (None, None))
        seen = {}

        def fake_v(path, iid, modes=None, seeds=None, triv_body=None):
            seen[iid] = triv_body
            return core.common.Result("verus", path, None, "failed", "verify", 0, [], [], [], {})

        def fake_d(path, iid):
            return core.common.Result("dafny", path, None, "failed", "verify", 0, [], [], [], {})
        with unittest.mock.patch.object(firsttry.V, "empty_body", fake_v), \
                unittest.mock.patch.object(firsttry.D, "empty_body", fake_d), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(firsttry.mode_empty_body(ctx, ["TRIV"], [1]), 0)
        self.assertEqual(seen["Q04.H3v"], "{\n    ()\n}")
        self.assertIsNone(seen["Q04.H1v"])
        self.assertIn("Q04.H3v: TRIV runs the item's declared trivial body", out.getvalue())
        twin.write_text(twin.read_text().replace("// triv: {\n// triv:     ()\n// triv: }\n",
                                                 "// triv: ()\n"))
        ctx = firsttry.Ctx(self.root, "Q04")
        it = next(i for i in ctx.items if i["id"] == "Q04.H3v")
        body, problem = firsttry.declared_triv_body(ctx, it, it["file"])
        self.assertIsNone(body)
        self.assertIn("a `triv:` body is one `{ … }` block", problem)


class EmptyTwin(RootCase):
    """Δ110: a twin unit directory that holds only a project mirror is no twin
    (it would run the learner files in reference mode): refused, never run."""

    def test_refused(self):
        twin = self.root / "Solutions" / "dafny" / "Q" / "Q04_ProofCraft" / "core"
        twin.mkdir(parents=True)
        shutil.copyfile(self.root / "dafny/Q/Q04_ProofCraft/core/dfyconfig.toml",
                        twin / "dfyconfig.toml")
        self.assertFalse(core.twin_has_sources(twin))
        rc, out, err = C.tool("vcheck", "--ref", twin, root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("no reference twin (the directory holds no source file of its own)", err)
        rc, out, err = C.tool("vcheck", "--ref", "--pin-counts", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("Solutions/dafny/Q/Q04_ProofCraft/core: the unit has no reference twin", err)
        (twin / "Q04_ProofCraft.dfy").write_text("module M {}\n")
        self.assertTrue(core.twin_has_sources(twin))


# =====================================================================================
# DV2b: chapter fences (pins.py --chapter / --update --chapter) and chapter_lint.py
# =====================================================================================

CHAPTER = "docs/Q04_ProofCraft.md"
FENCE = "```"
# A tiny invented chapter for the synthetic Q04 (no overlay): every section a
# stub, shaped as spec §2.4.3 asks. Nothing here is course content.
CHAPTER_TEXT = f"""# Q04 — Proof craft, loops and libraries

An invented chapter for the tools suites; every section is a stub.

Three ideas do all the work:

1. One idea.
2. A second idea.
3. A third idea.

**This module's files**

| file | what it is | shipped state |
|---|---|---|
| `dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy` | the Dafny exercise file | verified, 2 holes |
| `dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy` | the library unit | verified, no hole |
| `verus/q/q04_proof_craft/src/lib.rs` | the Verus crate | verified, **2 holes** |
| `dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy`, `verus/q/q04_proof_craft/src/exit.rs` | the exit | 2 holes each |
| `dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy`, `verus/q/q04_proof_craft/src/agent.rs` | the agent files | RED: 3 planted errors, no hole |
| `dafny/given/Q/QG_L3_BigNat.dfy` | the given layer | verified |
| `Solutions/` | the reference | yours to open LAST |

---

## 0. How this module works, pretest, test-out

Take T1dv first.

> **Predict (P1) — commit in the file before reading on.** What does the P1dv scenario report?

> **Predict (P2) — commit in the file before reading on.** And the P2dv scenario?

The loop, before anything else:

{FENCE}mermaid
flowchart LR
  rd["read"] --> pr["predict"]
{FENCE}

Predict, then run.

---

## 1. S1 — Limbs

Text about limbs.

---

## 2. S2 — Specs

Text about specs, and the lint over the shipped files:

<!-- pin: lint -->
{FENCE}
{FENCE}

---

## 3. S3 — Obligations

> **Predict (P3) — commit in the file before reading on.** Which labels of `specimens/Q04/P3d.dfy.specimen` fail?

Until P3d is recorded, the wrapper refuses the specimen:

<!-- pin: p3d-refusal -->
{FENCE}
{FENCE}

A second diagram:

{FENCE}mermaid
flowchart LR
  sp["specimen"] -->|"after the record"| run["vcheck"]
{FENCE}

Record first.

---

## 4. S4 — Loops

H2d and Q04.H2v are the loop holes.

---

## 5. S5 — Library

A third diagram:

{FENCE}mermaid
flowchart LR
  core["core"] --> std["std"]
{FENCE}

Staging matters.

### What the instruments can and cannot see

The gate sees holes; it does not see a weak spec.

---

## 6. On paper, before the keyboard

Two problems.

---

## 7. The exercise file

Fill the holes; record predictions with `scripts/firsttry.sh Q04 --check`. Done: the gate and the audit are clean.

---

## 8. Exercise (agentic): the retriever

> **CONTRACT (for /contract Q04 — run it in a FRESH session):** goal: make it verify.

---

## Exit (closed book)

Score it with `scripts/firsttry.sh Q04 --exit`: at least 3/4.

---

## Instructor touchpoints

- `/discuss` after reading; `/grade-paper` on the pair; `/tutor` when stuck; `/contract Q04`; `/review-code`; `/viva`: not this module; `/review` when the banner says items are due. Solutions last.

---

## What Q04 planted

| seed | harvest |
|---|---|
| a seed | a harvest |
"""

CHAPTER_TOML = """schema = 1

[[entry]]
id = "lint"
cmd = ["scripts/firsttry.sh", "Q04", "--lint-hollow"]

[[entry]]
id = "p3d-refusal"
cmd = ["scripts/vcheck", "specimens/Q04/P3d.dfy.specimen"]
guards = "closed"
note = "the H5 refusal as the learner sees it before recording P3d"
[entry.normalize]
exit = true
"""

COUNT_FILES = [("dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy", "exercise", 2, 0),
               ("dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy", "exercise", 0, 0),
               ("verus/q/q04_proof_craft/src/lib.rs", "exercise", 2, 0),
               ("dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy", "exit", 2, 0),
               ("verus/q/q04_proof_craft/src/exit.rs", "exit", 2, 0),
               ("dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy", "agent", 0, 3),
               ("verus/q/q04_proof_craft/src/agent.rs", "agent", 0, 3)]


class ChapterRoot(RootCase):
    """A root with the invented chapter, its pin file and a schema-2 count pin.
    No overlay: nothing here runs a verifier (the pinned commands are a
    static lint and a refusal)."""

    overlay = False

    def setUp(self):
        super().setUp()
        (self.root / "docs").mkdir()
        (self.root / CHAPTER).write_text(CHAPTER_TEXT)
        exp = self.root / "expected"
        exp.mkdir(exist_ok=True)
        (exp / "Q04.chapter.toml").write_text(CHAPTER_TOML)
        self.write_counts(COUNT_FILES)

    UNITS = [("dafny/Q/Q04_ProofCraft/core", "dafny", 5, ["Q04_ProofCraft.SumFormula"]),
             ("dafny/Q/Q04_ProofCraft/std", "dafny", 2, ["Q04_Library.H2"]),
             ("verus/q/q04_proof_craft", "verus", 6, ["sum_formula"])]

    def write_counts(self, count_files):
        files = [(r, role, {"verdict": "failed" if e or role == "harness" else "verified",
                            "holes": h, "errors": e})
                 for r, role, h, e in count_files]
        (self.root / "expected" / "Q04.counts").write_text(
            core.render_counts("Q04", self.UNITS, files))

    def capture(self, *extra):
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", *extra, root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        return out

    def chapter(self):
        return (self.root / CHAPTER).read_text()

    def edit(self, old, new, rel=CHAPTER):
        C.replace_in(self.root / rel, old, new)


class ChapterPins(ChapterRoot):
    def test_capture_check_and_locations_only(self):
        fl = self.line_of(CHAPTER, "<!-- pin: p3d-refusal -->") + 1     # its fence's line
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CHAPTER}:{fl}: pin p3d-refusal: not captured yet: run scripts/pins.py "
                      "--update --chapter Q04 --entry p3d-refusal", out)
        out = self.capture()
        self.assertIn("pins --update --chapter Q04: p3d-refusal: captured (4 fence line(s), exit "
                      "3)", out)
        self.assertIn("2 entries pinned; wrote docs/Q04_ProofCraft.md and "
                      "expected/Q04.chapter.toml", out)
        text = self.chapter()
        self.assertIn("<!-- pin: lint -->\n```\n$ scripts/firsttry.sh Q04 --lint-hollow\n", text)
        self.assertRegex(text, r"\nQ04 lint-hollow: [^\n]*\(\d+ file\(s\)\)\n```\n")
        self.assertIn("<!-- pin: p3d-refusal -->\n```\n$ scripts/vcheck "
                      "specimens/Q04/P3d.dfy.specimen\nvcheck: refused: specimens/Q04/"
                      "P3d.dfy.specimen holds Q04.P3d, whose first try is not recorded", text)
        self.assertIn("\n$ echo $?\n3\n```\n", text)
        self.assertNotIn(str(self.root), text)                     # paths redacted
        data = tomllib.loads((self.root / "expected" / "Q04.chapter.toml").read_text())
        e = {x["id"]: x for x in data["entry"]}
        # a quoted refusal (guards = "closed") also depends on the calibration
        # file of the prediction it waits for (absent as shipped)
        self.assertEqual(e["p3d-refusal"]["pinned"]["inputs"],
                         {"specimens/Q04/P3d.dfy.specimen": hashlib.sha256(
                             (self.root / "specimens/Q04/P3d.dfy.specimen").read_bytes())
                          .hexdigest(), "instructor/calib/Q04.tsv": "absent"})
        self.assertIn("slots/Q04.slots", e["lint"]["pinned"]["inputs"])     # a module id's files
        self.assertEqual(e["lint"]["pinned"]["inputs"]["instructor/calib/Q04.tsv"], "absent")
        self.assertEqual(e["p3d-refusal"]["note"], "the H5 refusal as the learner sees it before "
                                                   "recording P3d")
        fl = self.line_of(CHAPTER, "<!-- pin: p3d-refusal -->") + 1     # moved by the lint fence
        for env in ({}, {"CI": "true"}):
            rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root, env=env)
            self.assertEqual(rc, 0, out + err)
            self.assertIn("pins --chapter Q04: 2 pin(s) checked; 0 problem(s)", out)
        # a fence edited by hand: both halves report it, by location only
        self.edit("$ echo $?\n3\n", "$ echo $?\n0\n")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CHAPTER}:{fl}: pin p3d-refusal: the fence differs from its capture (an "
                      "edit by hand)", out)
        self.assertIn(f"{CHAPTER}:{fl}: pin p3d-refusal: the fence differs from the captured output "
                      "at fence line 4 (4 line(s) in the fence, 4 captured)", out)
        self.assertNotIn("refused", out)
        self.assertNotIn("echo", out)
        self.capture("--entry", "p3d-refusal")
        # an input changed since the capture: stale for the author, skipped elsewhere
        self.edit("\n", "\n// a learner's note\n", rel="specimens/Q04/P3d.dfy.specimen")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CHAPTER}:{fl}: pin p3d-refusal: stale: 1 input(s) changed since the capture "
                      "(specimens/Q04/P3d.dfy.specimen; spec §3.15 rule 9): re-capture with "
                      "scripts/pins.py --update --chapter Q04 --entry p3d-refusal", out)
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 2 pin(s) skipped: their inputs differ from the files "
                      "they were captured on (your own work", out)
        # --ci covers the chapter, and a pin file of a planned module matches nothing
        (self.root / "expected" / "Q05.chapter.toml").write_text("schema = 1\n")
        rc, out, err = C.tool("pins.py", "--ci", root=self.root)
        self.assertIn("pins --ci: 2 chapter pin(s) skipped", out)
        self.assertIn("expected/Q05.chapter.toml: Q05 is not a non-planned module", out)

    def test_a_recorded_first_try_makes_a_quoted_refusal_stale(self):
        """Once the learner records P3d, the quoted refusal no longer happens:
        the entry is stale (skipped in the learner's checkout), never a
        mismatch."""
        self.capture()
        fl = self.line_of(CHAPTER, "<!-- pin: p3d-refusal -->") + 1
        calib = self.root / "instructor" / "calib"
        calib.mkdir(parents=True)
        (calib / "Q04.tsv").write_text("Q04.P3d\tP\tpass\t2026-10-05\t" + "0" * 64 + "\n")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 2 pin(s) skipped", out)       # the lint reads calib too
        self.assertNotIn("differs", out)
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CHAPTER}:{fl}: pin p3d-refusal: stale: 1 input(s) changed since the "
                      "capture (instructor/calib/Q04.tsv;", out)

    def test_excerpt_of_the_whole_output_is_refused(self):
        self.edit("guards = \"closed\"\n", "guards = \"closed\"\nexcerpt = [1, 1]\n",
                  rel="expected/Q04.chapter.toml")
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)            # the other entries are still captured
        self.assertIn("pins --update --chapter Q04: not captured: entry p3d-refusal: excerpt "
                      "[1, 1] is the whole 1-line output: drop `excerpt`", err)
        self.assertIn("pins --update --chapter Q04: 1 entry pinned;", out)
        self.assertIn("1 entry not captured (above); their fences and pins are unchanged", err)
        data = tomllib.loads((self.root / "expected" / "Q04.chapter.toml").read_text())
        self.assertEqual(["pinned" in x for x in data["entry"]], [True, False])

    def test_guards_open_runs_what_a_recorded_learner_sees(self):
        """guards = "open" (the default) lifts vcheck's H5 refusal for this one
        run: with no toolchain installed the run gets past the guard and stops
        at the toolchain check, which no verifier needs to show."""
        self.edit('guards = "closed"\n', "", rel="expected/Q04.chapter.toml")
        empty = Path(tempfile.mkdtemp(prefix="dvl-tools-notc-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, empty, True)
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", "--entry", "p3d-refusal",
                              root=self.root, env={"CI": "true", "DVL_TOOLCHAIN_DIR": str(empty)})
        self.assertEqual(rc, 0, out + err)
        text = self.chapter()
        self.assertNotIn("whose first try is not recorded", text)
        self.assertIn("the pinned dafny toolchain is missing or altered", text)
        self.assertIn("\n$ echo $?\n3\n", text)
        # outside the author's context the entry is not even run while P3d is
        # unrecorded (H5): counted, never computed
        self.capture("--entry", "lint")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root,
                              env={"DVL_TOOLCHAIN_DIR": str(empty)})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 1 pin(s) not run: their output settles predictions "
                      "whose first try is not recorded (H5)", out)
        self.assertIn("pins --chapter Q04: 1 pin(s) checked; 0 problem(s)", out)
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root,
                              env={"CI": "true", "DVL_TOOLCHAIN_DIR": str(empty)})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("pins --chapter Q04: 2 pin(s) checked; 0 problem(s)", out)
        # the learner's own run is still refused: the guard is lifted in pins.py's run only
        rc, out, err = C.tool("vcheck", "specimens/Q04/P3d.dfy.specimen", root=self.root,
                              env={"DVL_TOOLCHAIN_DIR": str(empty)})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("whose first try is not recorded", err)

    def test_schema_and_pin_line_problems(self):
        exp = self.root / "expected" / "Q04.chapter.toml"
        exp.write_text(CHAPTER_TOML + """
[[entry]]
id = "Bad Id"
cmd = ["cat", "x"]
colour = "red"

[[entry]]
id = "ft"
cmd = ["scripts/firsttry.sh", "Q04", "--check"]

[[entry]]
id = "refpin"
cmd = ["scripts/vcheck", "--ref", "Solutions/x.dfy"]

[[entry]]
id = "raw"
cmd = ["dafny", "verify", "probe.dfy"]

[[entry]]
id = "probe"
cmd = ["scripts/vcheck", "probe.dfy"]
cwd = "scratch"
excerpt = [3, 1]
[entry.scratch."probe.dfy"]
fence = "below"

[[entry]]
id = "rec"
kind = "recorded"
cmd = ["scripts/vcheck", "x"]
""")
        self.edit("<!-- pin: lint -->\n```\n```\n",
                  "<!-- pin: lint -->\n```text\n```\n\n<!-- pin: nobody -->\n```\n```\n\n"
                  "<!-- pin: lint -->\n```\n```\n\n<!-- pin: dangling -->\n\nprose\n")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 1, out + err)
        ln = {k: self.line_of(CHAPTER, f"<!-- pin: {k} -->") for k in ("nobody", "dangling")}
        lint1 = self.line_of(CHAPTER, "```text")
        lint2 = ln["nobody"] + 4
        t = "expected/Q04.chapter.toml: entry"
        for want in (f"{t} Bad Id: unknown key(s) colour",
                     f"{t} Bad Id: `id` is lower-case letters",
                     f"{t} Bad Id: `cmd` starts with 'cat': a chapter quotes the course tools",
                     f"{t} ft: scripts/firsttry.sh --check is author-only or writes state",
                     f"{t} ft: scripts/firsttry.sh is quoted with --report or --lint-hollow only",
                     f"{t} refpin: scripts/vcheck --ref is author-only or writes state",
                     f"{t} refpin: `cmd` names reference material",
                     f"{t} raw: a toolchain binary runs on scratch files: cwd = \"scratch\"",
                     f"{t} raw: a toolchain binary runs on the entry's scratch files only",
                     f"{t} probe: `excerpt` is [first line, last line]",
                     f"{t} probe: scratch file 'probe.dfy': fence = \"above\"",
                     f"{t} probe: a scratch probe runs with its module's pinned flags",
                     f"{t} rec: a recorded quote takes no `cmd`",
                     f"{t} rec: a recorded quote names its `source`",
                     f"{CHAPTER}:{lint1 - 1}: pin lint: an output fence is bare (drop its 'text' "
                     "tag",
                     f"{CHAPTER}:{ln['nobody']}: pin nobody names no entry of "
                     "expected/Q04.chapter.toml",
                     f"{CHAPTER}:{lint2}: pin lint is quoted twice (also at line {lint1 - 1})",
                     f"{CHAPTER}:{ln['dangling']}: the pin line 'dangling' is not followed by a "
                     "fence"):
            self.assertIn(want, out)
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)                    # never captures a broken file
        self.assertIn("schema problem(s)", err)

    def test_update_refusals_and_usage(self):
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", root=self.root)
        self.assertEqual(rc, 3, out + err)
        self.assertIn("author-only", err)
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", "--entry", "nope",
                              root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 2, out + err)
        self.assertIn("--entry nope: no such entry", err)
        for args in (("--entry", "lint"), ("--ci", "--chapter", "Q04"),
                     ("--chapter", "Q04", "--module", "Q04")):
            rc, out, err = C.tool("pins.py", *args, root=self.root)
            self.assertEqual(rc, 2, (args, out, err))
        self.edit("<!-- pin: lint -->\n", "")
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", root=self.root,
                              env={"CI": "true"})
        self.assertEqual(rc, 3, out + err)
        self.assertIn("entry lint is quoted nowhere: add `<!-- pin: lint -->`", err)

    def test_recorded_quote(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-rec-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, tmp, True)
        rec = tmp / "refusals.json"
        rec.write_text(json.dumps([{"door": "a", "text": "guard: blocked (rule 1) at /tmp/x/clone/"
                                                          "Solutions/a.dfy\n"}]))
        with (self.root / "expected" / "Q04.chapter.toml").open("a") as f:
            f.write(f'\n[[entry]]\nid = "door-a"\nkind = "recorded"\nsource = "{rec}"\n'
                    '[entry.normalize]\nreplace = [["/tmp/x/clone/", ""]]\n')
        self.edit("Text about limbs.\n", "Text about limbs.\n\n<!-- pin: door-a -->\n```\n"
                                         "guard: blocked (rule 1) at Solutions/a.dfy\n...\n```\n")
        self.capture()
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.edit("at Solutions/a.dfy\n", "at Solutions/b.dfy\n")
        rc, out, err = C.tool("pins.py", "--chapter", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("pin door-a: fence line 1 is not verbatim in its record", out)
        self.assertIn("pin door-a: the fence differs from its capture", out)
        rc, out, err = C.tool("pins.py", "--update", "--chapter", "Q04", "--entry", "door-a",
                              root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        self.assertIn("pin door-a: this line is not verbatim in its record", err)

    def test_render_and_parse_units(self):
        e = {"id": "x", "cmd": ["scripts/vcheck", "a b.dfy"], "excerpt": [2, 3],
             "normalize": {"exit": True}}
        self.assertEqual(pins.render_entry_body(e, ["l1", "l2", "l3", "l4"], 1),
                         ["$ scripts/vcheck 'a b.dfy'", "l2", "l3", "...", "$ echo $?", "1"])
        with self.assertRaises(ValueError):
            pins.render_entry_body({**e, "excerpt": [2, 9]}, ["l1"], 0)
        self.assertEqual(pins.render_entry_body({"id": "x", "cmd": ["dafny", "verify", "p.dfy"],
                                                 "normalize": {"prompt": False}}, ["o"], 4),
                         ["o"])
        sr = pins.common.scratch_root()
        work = sr / "runs" / "chapter-Q04-x-1"
        got = pins.normalize_chapter_output(
            f"\x1b[31m{work}/p.dfy(3,4): Error\x1b[0m  \n{self.root}/dafny/x.dfy\nraw output: "
            f"{sr}/runs/vcheck-123/x\n\n", self.root, work,
            {"replace": [[r"\d+ ms", "N ms"]], "drop": ["^drop"]})
        self.assertEqual(got, ["p.dfy(3,4): Error", "dafny/x.dfy", "raw output: <scratch>/…"])
        lines = ["<!-- pin: a -->", "", "```", "x", "```", "```dafny", "y", "```",
                 "<!-- pin: b -->", "text", "  ~~~~", "  z", "  ~~~~"]
        fences, dangling = pins.parse_chapter(lines)
        self.assertEqual([(f.open, f.close, f.info, f.pin, f.body) for f in fences],
                         [(2, 4, "", "a", ["x"]), (5, 7, "dafny", None, ["y"]),
                          (10, 12, "", None, ["z"])])
        self.assertEqual(dangling, [(8, "b")])
        self.assertEqual(pins.source_fence_above(fences, 9), "y\n")
        self.assertEqual(pins._fence_lines(["```inner"]), ["````", "```inner", "````"])
        entries = [{"id": "a", "cmd": ["scripts/vcheck", "x"], "cwd": "scratch",
                    "normalize": {"exit": True, "replace": [["a", "b"]]},
                    "scratch": {"p.dfy": {"text": "line\n\"q\"\n"}},
                    "pinned": {"body": "0" * 64, "inputs": {"scratch:p.dfy": "1" * 64}}},
                   {"id": "r", "kind": "recorded", "source": "~/r.json", "note": "ünï"}]
        data = tomllib.loads(pins.render_chapter_toml("Q04", entries))
        self.assertEqual(data, {"schema": 1, "entry": entries})


class ChapterLint(ChapterRoot):
    """scripts/chapter_lint.py on the invented chapter, then one mutation per
    rule."""

    cl = None

    def setUp(self):
        super().setUp()
        self.capture()
        if ChapterLint.cl is None:
            ChapterLint.cl = C.load_script("chapter_lint")

    def lint(self):
        rec = core.record(self.root, "Q04")
        problems, summary = self.cl.lint(self.root, rec, True)
        return problems, summary

    def assert_flags(self, old, new, want, rel=CHAPTER):
        saved = (self.root / rel).read_text()
        self.edit(old, new, rel)
        try:
            problems, _ = self.lint()
            self.assertTrue(any(want in p for p in problems), (want, problems))
        finally:
            (self.root / rel).write_text(saved)

    def test_clean_chapter_and_cli(self):
        problems, summary = self.lint()
        self.assertEqual(problems, [])
        self.assertIn("5 strand section(s), 3 predict box(es), 3 diagram(s), 2 pinned fence(s)",
                      summary)
        rc, out, err = C.tool("chapter_lint.py", "Q04", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        self.assertIn("chapter_lint Q04: docs/Q04_ProofCraft.md: 5 strand section(s)", out)
        rc, out, err = C.tool("chapter_lint.py", "--all", root=self.root, env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        for args in ((), ("--all", "Q04")):
            rc, out, err = C.tool("chapter_lint.py", *args, root=self.root)
            self.assertEqual(rc, 2, (args, out, err))
        rc, out, err = C.tool("chapter_lint.py", "Q05", root=self.root)
        self.assertEqual(rc, 3, out + err)                            # planned
        (self.root / CHAPTER).unlink()
        rc, out, err = C.tool("chapter_lint.py", "--all", root=self.root)
        self.assertEqual(rc, 1, out + err)
        self.assertIn(f"{CHAPTER}:0: Q04 is armed and its chapter does not exist", out)
        self.assertIn(f"expected/Q04.chapter.toml: pins a chapter that does not exist", out)

    def test_nothing_armed_passes_loudly(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-tools-idle-", dir=C.TMP_BASE))
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "MODULES.toml").write_text(C.plan_real_modules((C.ROOT / "MODULES.toml")
                                                              .read_text()))
        rc, out, err = C.tool("chapter_lint.py", "--all", root=tmp)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("no armed module: nothing to check", out)
        self.assertIn("passing loudly", out)

    def test_hand_written_list_has_one_source(self):
        """Δ114's list of hand-written agentic exercises is one data file beside
        the contract skill: the skill points at it and the lint reads it, and
        neither holds a copy of an entry (DV2b-2)."""
        rel = self.cl.HAND_WRITTEN_FILE
        hand = self.cl.hand_written(C.ROOT)
        self.assertTrue(hand)
        skill = (C.ROOT / ".claude/skills/contract/SKILL.md").read_text(encoding="utf-8")
        lint_src = (C.SCRIPTS / "chapter_lint.py").read_text(encoding="utf-8")
        self.assertIn(f"`{rel}`", skill)
        for mid, ent in hand.items():
            for text in (skill, lint_src):
                self.assertNotIn(ent["refusal"], text, mid)
                self.assertNotIn(f'"{ent["exercise"]}"', text, mid)
            rec = core.record(C.ROOT, mid, allow_planned=True)
            self.assertEqual(rec["agentic"], [], mid)

    def test_hand_written_loader_refuses_a_broken_list(self):
        rel = self.cl.HAND_WRITTEN_FILE
        good = (C.ROOT / rel).read_text(encoding="utf-8")
        path = self.root / rel
        for text, want in (
                (None, "is missing"),
                ("[Q03\n", "unreadable"),
                ('Q03 = "contract v0"\n', "every entry is a table named by a module id"),
                ('[Q3]\nexercise = "e"\nwhere = "w"\nrefusal = "Q3 e"\n',
                 "every entry is a table named by a module id"),
                ('[Q04]\nexercise = "e"\nrefusal = "Q04 e"\n', "needs exactly the keys"),
                ('[Q04]\nexercise = "e"\nwhere = ""\nrefusal = "Q04 e"\n',
                 "needs exactly the keys"),
                ('[Q04]\nexercise = "e"\nwhere = "w"\nrefusal = "Q04 e"\nextra = "x"\n',
                 "needs exactly the keys"),
                ('[Q04]\nexercise = "e"\nwhere = "w"\nrefusal = "closed for it"\n',
                 "its refusal line names the module and the exercise")):
            with self.subTest(want=want, text=text):
                if text is None:
                    path.unlink()
                else:
                    path.write_text(text, encoding="utf-8")
                with self.assertRaises(core.Refusal) as cm:
                    self.cl.hand_written(self.root)
                self.assertIn(want, str(cm.exception))
                rc, out, err = C.tool("chapter_lint.py", "Q04", root=self.root)
                self.assertEqual(rc, 3, out + err)
                self.assertIn(want, err)
                path.write_text(good, encoding="utf-8")

    def test_hand_written_rules(self):
        rel = self.cl.HAND_WRITTEN_FILE
        # an entry for a module with agentic files is stale: /contract runs for it
        (self.root / rel).write_text('[Q04]\nexercise = "the retriever"\nwhere = "w"\n'
                                     'refusal = "Q04\'s agentic exercise is the retriever."\n',
                                     encoding="utf-8")
        problems, _ = self.lint()
        self.assertIn(f"{CHAPTER}:1: {rel} lists Q04, whose registry `agentic` is not empty: "
                      "/contract Q04 runs, so the entry is stale (Δ114)", problems)
        # the agentic section of a hand-written exercise: its name and the refusal, quoted
        hwp = self.cl.hand_written_problems
        ent = {"exercise": "contract v0", "where": "w",
               "refusal": "Q03's agentic exercise is contract v0, so /contract is closed for it."}
        quoted = ("Write contract v0 by hand. The refusal:\n\n> Q03's agentic exercise is "
                  "contract v0,\n> so /contract is closed for it.\n")
        self.assertEqual(hwp(ent, quoted), [])
        self.assertEqual(len(hwp(ent, quoted.replace("so /contract", "and /contract"))), 1)
        self.assertIn("quotes the /contract refusal line", hwp(ent, "contract v0, by hand")[0])
        got = hwp(ent, "nothing here")
        self.assertEqual(len(got), 2, got)
        self.assertTrue(got[0].startswith("the agentic section gives the contract v0 instructions"))
        self.assertTrue(got[1].startswith("the agentic section quotes the /contract refusal line"))

    def test_skeleton_rules(self):
        A = self.assert_flags
        A("# Q04 — Proof craft", "# Q04 - Proof craft", "line 1 is the title `# Q04 — Proof "
          "craft, loops and libraries`")
        A("Three ideas do all the work:", "Ideas:", "\"Three ideas do all the work\"")
        A("## 0. How this module works", "## 0. Setup", "`## 0. How this module works, pretest, "
          "test-out` opens a depth chapter")
        A("## 3. S3 — Obligations", "## 3. S3 - Obligations", "a strand section is `## <n>. S<k> "
          "— <title>`")
        A("## 4. S4 — Loops", "## 4. S5 — Loops", "one strand section per strand of Q04, in "
          "strand order: S1 S2 S3 S4 S5 (found S1 S2 S3 S5 S5)")
        A("## 7. The exercise file", "## 9. The exercise file", "sections are numbered "
          "consecutively from 0 or 1 (found 0, 1, 2, 3, 4, 5, 6, 9, 8)")
        A("---\n\n## 2. S2", "## 2. S2", "`---` separates top sections")
        A("## 6. On paper, before the keyboard", "## 6. Paper", "paper = true: `## <k>. On paper, "
          "before the keyboard` is required")
        A("record predictions with `scripts/firsttry.sh Q04 --check`", "record predictions",
          "The exercise file states the slot protocol (`scripts/firsttry.sh Q04 --check`)")
        A("> **CONTRACT (for /contract Q04 — run it in a FRESH session):**", "> **CONTRACT:**",
          "the agentic section holds the CONTRACT blockquote")
        A("### What the instruments can and cannot see", "### What the tools see",
          "a heading \"What the instruments can and cannot see\" is required")
        A("at least 3/4", "at least three", "the Exit section states the threshold (3/4)")
        A("`/viva`: not this module; ", "", "Instructor touchpoints names every skill, as a "
          "touchpoint or as \"not this module\" (missing: /viva)")
        A("## What Q04 planted", "## What it planted", "`## What Q04 planted` (a seed → harvest "
          "table) is required")
        A("## Exit (closed book)", "## Exitt", "`## Exit (closed book)` is required")
        A("## 8. Exercise (agentic): the retriever\n\n> **CONTRACT (for /contract Q04 — run it in "
          "a FRESH session):** goal: make it verify.\n\n---\n\n## Exit (closed book)\n\nScore it "
          "with `scripts/firsttry.sh Q04 --exit`: at least 3/4.",
          "## Exit (closed book)\n\nScore it with `scripts/firsttry.sh Q04 --exit`: at least "
          "3/4.\n\n---\n\n## 8. Exercise (agentic): the retriever\n\n> **CONTRACT (for /contract "
          "Q04 — run it in a FRESH session):** goal: make it verify.",
          "Exit comes after Exercise (agentic)")

    def test_files_table_rules(self):
        A = self.assert_flags
        A("| verified, 2 holes |", "| verified, 3 holes |", "dafny/Q/Q04_ProofCraft/core/"
          "Q04_ProofCraft.dfy: its row states the shipped hole count, 2")
        A("RED: 3 planted errors, no hole", "RED, no hole", "verus/q/q04_proof_craft/src/agent.rs:"
          " its row states the agent file's shipped errors, 3")
        A("| `dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy` | the library unit | verified, no hole "
          "|\n", "", "the files table names dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy (its "
          "exercise file)")
        A("yours to open LAST", "the reference", "the files table names the reference")
        A("`dafny/given/Q/QG_L3_BigNat.dfy`", "the L3 layer", "the files table names the given "
          "layer(s)")
        # a row of two files: `a + b holes` in the files' order
        A("| 2 holes each |", "| 3 + 2 holes |", "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy: its row "
          "states the shipped hole count, 2")
        A("| 2 holes each |", "| 2 + 3 holes |", "verus/q/q04_proof_craft/src/exit.rs: its row "
          "states the shipped hole count, 2")
        for ok in ("| **2 + 2 holes** |", "| two holes each |", "| 2 holes; 2 holes |"):
            saved = self.chapter()
            self.edit("| 2 holes each |", ok)
            try:
                self.assertEqual(self.lint()[0], [], ok)
            finally:
                (self.root / CHAPTER).write_text(saved)

    def test_harness_row_states_its_holes(self):
        """DV3a follow-up: a harness (learner Python) file's row states its
        shipped hole count, as an exercise's row does."""
        py = "harness/q/fvh_q/q04_toy.py"
        self.write_counts(COUNT_FILES + [(py, "harness", 3, 0)])
        self.assertIn(f"{CHAPTER}:{self.line_of(CHAPTER, '| file |')}: the files table names "
                      f"{py} (its harness file)", self.lint()[0])
        reference = "| `Solutions/` | the reference | yours to open LAST |\n"
        A = self.assert_flags
        A(reference, f"| `{py}` | the Python exercise | failed, 2 holes |\n" + reference,
          f"{py}: its row states the shipped hole count, 3")
        A(reference, f"| `{py}` | the Python exercise | failed |\n" + reference,
          f"{py}: its row states the shipped hole count, 3")
        self.edit(reference,
                  f"| `{py}` | the Python exercise | failed, **3 holes** |\n" + reference)
        self.assertEqual(self.lint()[0], [])

    def test_a_module_without_a_spine_layer_needs_no_given_file(self):
        text = self.chapter().replace("`dafny/given/Q/QG_L3_BigNat.dfy`", "no given layer")
        chapter = self.cl.Chapter(text.splitlines())
        rec = core.record(self.root, "Q04")
        problems = self.cl.files_table(self.root, rec, chapter, CHAPTER)
        self.assertTrue(any("given layer" in p for p in problems), problems)
        rec = dict(rec, layer="")
        self.assertEqual(self.cl.files_table(self.root, rec, chapter, CHAPTER), [])

    def test_stated_counts(self):
        sc = self.cl.stated_counts
        self.assertEqual(sc("RED: **3 holes, 6 errors**; **6 holes, 1 error**", "hole"), [3, 6])
        self.assertEqual(sc("RED: **3 holes, 6 errors**; **6 holes, 1 error**", "error"), [6, 1])
        self.assertEqual(sc("RED: 4 errors and 0 holes each", "hole"), [0])
        self.assertEqual(sc("**1 hole** and two empty blocks; **3 holes**", "hole"), [1, 3])
        self.assertEqual(sc("verifies with exactly **3 holes**", "hole"), [3])
        self.assertEqual(sc("complete, no hole", "hole"), [0])
        self.assertEqual(sc("the closed-book exit, 9 + 4 blocks", "hole"), [])

    def test_predict_rules(self):
        A = self.assert_flags
        A("> **Predict (P2) — commit in the file before reading on.** And the P2dv scenario?\n",
          "", "no predict callout for Q04.P2dv")
        A("> **Predict (P2) — commit", "> **Predict (P9) — commit", "Predict (P9) names no "
          "prediction item of Q04")
        A("> **Predict (P2) — commit in the file before reading on.**",
          "> **Predict (P2)** — commit first.", "a predict callout is `> **Predict (P<n>) — "
          "commit in the file before reading on.** <question>`")
        A("> **Predict (P1) — commit", "> **Predict (P1dv, P2) — commit", "Predict (P2) appears "
          "twice")
        # `answers` names predictions only: never a hole, exit or test-out
        toml = "expected/Q04.chapter.toml"
        A('id = "lint"\n', 'id = "lint"\nanswers = ["Q04.H2d"]\n', "pin lint: its `answers` names "
          "Q04.H2d, which is no prediction", rel=toml)
        A('id = "lint"\n', 'id = "lint"\nanswers = ["Q04.P9d"]\n', "pin lint: its `answers` names "
          "Q04.P9d, no item of Q04", rel=toml)
        A('id = "lint"\n', 'id = "lint"\nanswers = ["Q05.P1d"]\n', "pin lint: its `answers` names "
          "Q05.P1d, whose module is unknown or planned", rel=toml)
        A('id = "lint"\n', 'id = "lint"\nanswers = ["Q04.P3d"]\n', "pin lint settles Q04.P3d, "
          "whose predict box comes later", rel=toml)
        # an output that settles P3d sits before P3d's box
        box = ("> **Predict (P3) — commit in the file before reading on.** Which labels of "
               "`specimens/Q04/P3d.dfy.specimen` fail?\n")
        saved = self.chapter()
        self.edit(box, "")
        A("Record first.\n", "Record first.\n\n" + box, "pin p3d-refusal settles Q04.P3d, whose "
          "predict box comes later")
        (self.root / CHAPTER).write_text(saved)

    def test_fence_diagram_and_item_rules(self):
        A = self.assert_flags
        A("Text about limbs.\n", "Text about limbs.\n\n```\nout\n```\n", "a bare fence is "
          "output: pin it")
        A("Text about limbs.\n", "Text about limbs.\n\n```console\nout\n```\n", "fence tag "
          "'console': a source fence carries its language")
        A("| a seed | a harvest |\n", "| a seed | a harvest |\n\n```dafny\nlemma L()\n",
          "this fence is never closed")
        A("  rd[\"read\"] --> pr[\"predict\"]", "  rd[read] --> pr[\"predict\"]", "flowchart node "
          "labels are quoted")
        A("  core[\"core\"] --> std[\"std\"]", "  Q04[\"core\"] --> std[\"std\"]", "a mermaid node "
          "id looks like a module id")
        A("Staging matters.\n", "\n## not prose\n", "frame each diagram with a takeaway after it")
        A("A third diagram:\n\n```mermaid\nflowchart LR\n  core[\"core\"] --> std[\"std\"]\n"
          "```\n\nStaging matters.\n", "", "2 mermaid diagram(s): a chapter has 3 to 5")
        A("H2d and Q04.H2v", "H9d and Q04.H2v", "H9d is no item of Q04")
        A("H2d and Q04.H2v", "H2d and Q04.H9v", "Q04.H9v is no item of Q04")
        A("H2d and Q04.H2v", "H2d and Q05.H1d", "Q05.H1d names an item of Q05, which is planned")
        A("<!-- pin: lint -->\n```\n$ scripts", "<!-- pin: lint -->\n```text\n$ scripts",
          "pin lint: an output fence is bare")
        A("<!-- pin: lint -->\n", "<!-- pin: nolint -->\n", "pin nolint names no entry")


if __name__ == "__main__":
    unittest.main()
