"""Tool tests for the DV3b tools items against the real pinned Dafny 4.11.0 and
Verus 0.2026.09.27.3cf1832: vcheck's other bundled solver and its sweep
(QPLAN §6 Q29: --solver, --brittleness --solvers, --ref --brittleness), and
the construct forms in firsttry (§6 Q43: a test-out's first try, the exit,
the strict report's `stable` sweep, and the forms gate of --empty-body with
its `// cfree:` answers).

Every job runs through the dvl libraries, so it runs under the CLAUDE.md
§Resources memory cap (Dafny 8G, Verus 16G) one at a time unless
DVL_DAFNY_JOBS / DVL_VERUS_JOBS say otherwise. The suite fails, never skips,
without the pinned toolchains. Every program is an invented toy (neutral test
material for the gates; none is course content or an answer), and every
expectation was observed on a real run.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_forms_tool.py'
"""

import json
import shutil
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
from dvl import common  # noqa: E402

FX = "tests/wrappers/fixtures"
REFERENCE = C.ROOT / "tests" / "wrappers" / "fixtures" / "tools" / "reference"
CORE = "dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy"
STD = "dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy"
LIB_RS = "verus/q/q04_proof_craft/src/lib.rs"
EXIT_D = "dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy"
EXIT_RS = "verus/q/q04_proof_craft/src/exit.rs"
P_ITEMS = tuple(f"Q04.P{n}" for n in ("1dv", "2dv", "3d", "4d", "5d", "6v", "7v", "8d", "9d",
                                      "10v", "11v"))


def calib(root, *ids):
    d = root / "instructor" / "calib"
    d.mkdir(parents=True, exist_ok=True)
    with (d / "Q04.tsv").open("a") as f:
        for iid in ids:
            f.write(f"{iid}\tpredict\tpass\t2026-10-04\tx\n")


def commit_baseline(root):
    g = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True,  # noqa: E731
                                  capture_output=True, text=True)
    g("init", "-q", "-b", "main")
    g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
    g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m", "shipped")
    g("switch", "-q", "-c", "work")


def line_of(path, needle):
    return next(i for i, x in enumerate(Path(path).read_text().split("\n"), 1) if needle in x)


# =====================================================================================
# vcheck: the other bundled solver and the sweep (QPLAN §6 Q29)
# =====================================================================================

class VcheckSolvers(unittest.TestCase):
    OK = f"{FX}/dafny/ok.dfy"

    def test_solver_and_sweeps(self):
        rc, out, err = C.tool("vcheck", "--solver", "4.14.1", self.OK)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out.splitlines()[0], f"vcheck: {self.OK} [dafny, learner loop, solver "
                                              "4.14.1]: verified — 2 verified, 0 holes, 0 errors")
        rc, out, err = C.tool("vcheck", "--json", "--solver", "4.14.1", "--seed", "2", self.OK)
        d = json.loads(out)
        self.assertEqual((d["verdict"], d["count_unit"]), ("verified", "passed-tasks"))
        self.assertTrue(d["cmd"][d["cmd"].index("--solver-path") + 1].endswith("z3-4.14.1"))
        rc, out, err = C.tool("vcheck", "--brittleness", "--solvers", self.OK)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out.splitlines()[0], (
            f"vcheck --brittleness: {self.OK} [dafny]: 4.12.1 seed 1: verified · 4.12.1 seed 2: "
            "verified · 4.12.1 seed 3: verified · 4.14.1 seed 1: verified · 4.14.1 seed 2: "
            "verified · 4.14.1 seed 3: verified — stable"))
        rc, out, err = C.tool("vcheck", "--brittleness", "--solver", "4.14.1", "--json", self.OK)
        d = json.loads(out)
        self.assertEqual(sorted(d["verdicts"]), ["4.14.1 seed 1", "4.14.1 seed 2",
                                                 "4.14.1 seed 3"])
        self.assertTrue(d["stable"])
        rc, out, err = C.tool("vcheck", "--brittleness", "--solvers", f"{FX}/dafny/fails.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertTrue(out.splitlines()[0].endswith("4.14.1 seed 3: failed — NOT stable"), out)
        # the plain sweep keeps its form (seeds only)
        rc, out, err = C.tool("vcheck", "--brittleness", self.OK)
        self.assertIn("seed 1: verified · seed 2: verified · seed 3: verified — stable", out)

    def test_solver_hash_is_checked(self):
        """D79: a solver whose sha256 is not the pinned one for this platform warns
        and marks the run untrusted; it is never refused (DELTAS Δ503). The check
        is common.toolchain("dafny")'s, which solver_path() and --versions share."""
        D = core.D
        real = common.load_pins
        def bad():
            p = real()
            p["dafny"]["solvers"]["4.14.1"]["sha256"] = {common.plat.current(): "0" * 64}
            return p
        saved = {k: list(v) for k, v in common._MISMATCH.items()}
        warned = set(common._WARNED)
        try:
            with unittest.mock.patch.object(common, "load_pins", bad):
                common.toolchain("dafny", fresh=True)
                self.assertTrue(str(D.solver_path("4.14.1")).endswith("dafny/z3/bin/z3-4.14.1"))
                notes = common.untrusted("dafny").get("dafny", [])
                self.assertTrue(any("4.14.1" in m and "sha256" in m for m in notes), notes)
                self.assertTrue(common.trust_note("dafny").startswith("UNTRUSTED"))
        finally:
            common._MISMATCH.clear()
            common._MISMATCH.update(saved)
            common._WARNED.clear()
            common._WARNED.update(warned)
            common.toolchain("dafny", fresh=True)
        self.assertEqual(common.untrusted("dafny"), {})
        self.assertTrue(str(D.solver_path("4.14.1")).endswith("dafny/z3/bin/z3-4.14.1"))

class VcheckRefBrittleness(unittest.TestCase):
    def test_twin_sweep_names_locations_only(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        shutil.copytree(REFERENCE, root / "Solutions")
        twin = "Solutions/dafny/Q/Q04_ProofCraft/core"
        rc, out, err = C.tool("vcheck", "--ref", "--brittleness", root / twin, root=root,
                              env={"CI": "true"})
        self.assertEqual(rc, 0, out + err)
        lines = out.splitlines()
        self.assertEqual(lines[0], f"vcheck --brittleness: {twin} [dafny, reference]: seed 1: "
                                   "verified · seed 2: verified · seed 3: verified — stable")
        self.assertIn(f"widest spread {twin}/Q04_ProofCraft.dfy:", out)
        self.assertNotIn("SumFormula", out)            # locations, never a symbol name
        self.assertFalse(any((root / "Solutions").rglob("*.csv")))


# =====================================================================================
# firsttry: construct forms (QPLAN §6 Q43)
# =====================================================================================

TOUT = ("  // item: Q04.T1dv S5\n"
        "  // form: trigger, stable\n"
        "  // ### T1dv · S5 — Write `function Inc(n: nat): nat`, which adds one, and a lemma\n"
        "  //    whose quantified fact about it carries an explicit trigger.\n"
        "\n"
        "  // Uncomment as you go:\n"
        "  // lemma IncCheck()\n"
        "  //   ensures Inc(2) == 3\n"
        "  // {\n"
        "  // }\n")


class FormsAtTheTestOut(unittest.TestCase):
    def root_(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        C.replace_in(root / STD, "  // item: Q04.T1dv S5\n  const T1 := 0\n", TOUT)
        commit_baseline(root)
        calib(root, *P_ITEMS)
        return root

    def test_first_try_fails_a_form_and_passes_with_it(self):
        root = self.root_()
        C.replace_in(root / STD, "  // Uncomment as you go:",
                     "  function Inc(n: nat): nat { n + 1 }\n\n  // Uncomment as you go:")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("✗ Q04.T1dv  first try fails (test-out: its checks enabled in a scratch "
                      "copy): form trigger not met (no explicit trigger (`{:trigger …}`) in the "
                      "block)", out)
        rows = (root / "instructor/calib/Q04.tsv").read_text().splitlines()
        self.assertEqual(rows[-1].split("\t")[:3], ["Q04.T1dv", "predict", "fail"])
        root2 = self.root_()
        C.replace_in(root2 / STD, "  // Uncomment as you go:",
                     "  function Inc(n: nat): nat { n + 1 }\n\n  lemma IncAll()\n"
                     "    ensures forall k: nat {:trigger Inc(k)} :: Inc(k) > k\n  {\n  }\n\n"
                     "  // Uncomment as you go:")
        rc, out, err = C.tool("firsttry.py", "Q04", "--check", root=root2)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("✓ Q04.T1dv  first try passes (test-out: its checks enabled in a scratch "
                      "copy)\n", out)


class FormsAtTheExit(unittest.TestCase):
    def test_exit(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        C.replace_in(root / EXIT_D, "  // need: lemma DoubleIsTwice(n: nat)\n",
                     "  // need: lemma DoubleIsTwice(n: nat)\n  // form: trigger, stable\n")
        C.replace_in(root / EXIT_RS, "// need: pub proof fn double_is_twice(n: nat)\n",
                     "// need: pub proof fn double_is_twice(n: nat)\n// form: nl-steps:2\n")
        C.replace_in(root / EXIT_RS, "// uses: lemma-call\npub proof fn double_mono",
                     "// uses: lemma-call\n// form: stable\npub proof fn double_mono")
        commit_baseline(root)
        C.replace_in(root / EXIT_D, "    ensures Double(n) == 2 * n\n",
                     "    ensures Double(n) == 2 * n\n  {\n"
                     "    forall k: nat {:trigger Double(k)} | k == n\n"
                     "      ensures Double(k) == 2 * k\n    {\n    }\n  }\n")
        C.replace_in(root / EXIT_D, "    ensures Double(a) <= Double(b)\n",
                     "    ensures Double(a) <= Double(b)\n  {\n  }\n")
        C.replace_in(root / EXIT_RS, '    #[verifier::proof_note("Q04.X1v")] assume(false);\n',
                     "    assert(n + n == 2 * n) by (nonlinear_arith) requires n >= 0;\n")
        C.replace_in(root / EXIT_RS, '    #[verifier::proof_note("Q04.X2v")] assume(false);\n', "")
        rc, out, err = C.tool("firsttry.py", "Q04", "--exit", root=root)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("Q04.X1d  now ✓ · first run: recorded now", out)
        self.assertIn("Q04.X2d  now ✓ · first run: recorded now", out)
        self.assertIn("Q04.X1v  now ✗ form nl-steps:2 not met (1 scoped `nonlinear_arith` "
                      "step(s) in the block (`assert(…) by (nonlinear_arith) requires …`), 2 "
                      "needed) · first run: recorded now", out)
        self.assertIn("Q04.X2v  now ✓ · first run: recorded now", out)
        self.assertIn("Q04 exit: 3/4 (threshold 3; per language Dafny 2/2 (≥1), Verus 1/2 (≥1)) "
                      "PASS", out)
        # a second step meets the form now; the first run stays the record
        C.replace_in(root / EXIT_RS, "requires n >= 0;\n", "requires n >= 0;\n"
                     "    assert(2 * n >= n) by (nonlinear_arith) requires n >= 0;\n")
        # and the trigger gone from the Dafny answer fails its form now
        C.replace_in(root / EXIT_D, "forall k: nat {:trigger Double(k)} | k == n",
                     "forall k: nat | k == n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--exit", root=root)
        self.assertIn("Q04.X1v  now ✓ · first run ✗", out)
        self.assertIn("Q04.X1d  now ✗ form trigger not met (no explicit trigger (`{:trigger …}`) "
                      "in the block) · first run ✓", out)


class FormsInTheStrictReport(unittest.TestCase):
    def test_stable_sweep(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        C.replace_in(root / CORE, "  // uses: calc\n  lemma SumFormula",
                     "  // uses: calc\n  // form: stable\n  lemma SumFormula")
        commit_baseline(root)
        C.replace_in(root / CORE, "    ensures 2 * Sum(n) == n * (n + 1)\n",
                     "    ensures 2 * Sum(n) == n * (n + 1)\n  {\n  }\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=root)
        self.assertEqual(rc, 1, out + err)
        item = line_of(root / CORE, "// item: Q04.H3d")
        self.assertRegex(out, rf"{CORE}:{item}: form: Q04.H3d: form stable not met \(an error at "
                              r"line \d+ under 4\.12\.1 seed 1\)")
        self.assertIn("forms not met 1,", out)
        C.replace_in(root / CORE, "    ensures 2 * Sum(n) == n * (n + 1)\n  {\n  }\n",
                     "    ensures 2 * Sum(n) == n * (n + 1)\n  {\n    if n > 0 {\n"
                     "      SumFormula(n - 1);\n    }\n  }\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--report", "--strict", root=root)
        self.assertIn("forms not met 0,", out)
        self.assertNotIn(": form: ", out)


class FormsGate(unittest.TestCase):
    """--empty-body's forms gate: the twin's forms equal the learner's, the twin
    meets them, and each `// cfree:` answer fails verification or a form."""

    def test_gate(self):
        root = C.build_root()
        self.addCleanup(C.remove_root, root)
        shutil.copytree(REFERENCE, root / "Solutions")
        both = lambda rel, old, new: [C.replace_in(p / rel, old, new)  # noqa: E731
                                      for p in (root, root / "Solutions")]
        both(CORE, "  // uses: calc\n  lemma SumFormula", "  // uses: calc\n  // form: stable\n"
                                                         "  lemma SumFormula")
        C.replace_in(root / "Solutions" / CORE, "  // form: stable\n",
                     "  // form: stable\n  // cfree: { }\n")
        C.replace_in(root / CORE, "  // pair: Q04.H1v\n", "  // pair: Q04.H1v\n"
                                                          "  // form: trigger\n")
        both(LIB_RS, "// pair: Q04.H1d\n", "// pair: Q04.H1d\n// form: no-nl\n")
        C.replace_in(root / "Solutions" / LIB_RS, "// form: no-nl\n",
                     "// form: no-nl\n// cfree: { }\n"
                     "// cfree: { assert(x + 0 == x) by (nonlinear_arith); }\n"
                     "// cfree: { assert(x + 1 == x); }\n")
        both(LIB_RS, "// item: Q04.H3v S3\n// uses: lemma-call\n",
             "// item: Q04.H3v S3\n// uses: lemma-call\n// form: nl-steps:2\n")
        rc, out, err = C.tool("firsttry.py", "Q04", "--empty-body", "--eb-modes", "FORMS",
                              "--eb-seeds", "1", root=root, env={"CI": "true"})
        self.assertEqual(rc, 1, out + err)
        for want in (
                f"✓ Q04.H3d  the twin meets its forms (stable) ({CORE})",
                f"✓ Q04.H3d  construct-free answer 1 fails verification ({CORE})",
                f"✗ Q04.H1d  the twin's form lines (none) differ from the learner's (trigger) "
                f"({CORE})",
                f"✓ Q04.H1v  the twin meets its forms (no-nl) ({LIB_RS})",
                f"✗ Q04.H1v  CONSTRUCT NOT REQUIRED: construct-free answer 1 verifies and meets "
                f"every form ({LIB_RS})",
                f"✓ Q04.H1v  construct-free answer 2 fails its forms: form no-nl not met "
                f"(`nonlinear_arith` at line ",
                f"✓ Q04.H1v  construct-free answer 3 fails verification ({LIB_RS})",
                f"✗ Q04.H3v  the twin fails its forms: form nl-steps:2 not met (1 scoped "
                f"`nonlinear_arith` step(s) in the block",
                "? Q04.X1v  no gate run: --eb-modes names only RGN or FORMS and the item has "
                "no such gate",
                "Q04 empty-body: 1/9 hole(s) pass the gate"):
            self.assertIn(want, out)
        # the twins are untouched and no shadow remains in the reference tree
        self.assertIn("// cfree: { }\n", (root / "Solutions" / LIB_RS).read_text())
        self.assertNotIn("assert(x + 1 == x);\n}", (root / "Solutions" / LIB_RS).read_text())


if __name__ == "__main__":
    unittest.main()
