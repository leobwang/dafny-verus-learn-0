"""scripts/dvl/python.py with real pytest runs (uv, the pinned lock, offline):
the learner loop and the gate, named tests, the reference gate on an overlay,
the Python TRIV mode, the author-only CLI commands, and a tree left clean.
Each run is one small pytest process under dvl's memory cap (pool `python`);
no solver runs. Needs uv's cache to hold the locked packages
(`uv sync --directory harness` once, online); skipped without uv.

Run: python3 -B -m unittest discover -s tests/harness_adapter -p 'test_python_tool.py'
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter_common as A  # noqa: E402
from adapter_common import P  # noqa: E402

FILLED = A.TWIN.replace("(Reference Solution)", "(filled)")
UNTESTED_HOLE = FILLED + '''

# item: Q98.H3py S13
def later() -> int:
    """Not tested yet."""
    raise NotImplementedError("Q98.H3py")
'''


@unittest.skipUnless(A.has_uv(), "uv is not installed")
class Runs(unittest.TestCase):
    def setUp(self):
        self.base = A.tmpdir("py-tool-")
        self.root = A.build_root(self.base)
        self.learner = self.root / A.LEARNER_REL
        self.twin = self.root / A.TWIN_REL

    def tearDown(self):
        A.remove(self.base)

    def assert_tree_clean(self):
        junk = [p for p in (self.root / "harness").rglob("*")
                if p.name in ("__pycache__", ".pytest_cache", ".venv") or p.suffix == ".pyc"]
        self.assertEqual(junk, [])

    def test_the_hollow_file_fails_its_tests_and_shows_its_holes(self):
        res = P.check(self.learner, root=self.root)
        self.assertEqual((res.verdict, res.stage, len(res.holes)), ("failed", "test", 2))
        self.assertEqual(sorted(res.per_symbol.values()), ["failed"] * 3)
        self.assertEqual(sorted(res.per_symbol), [
            "tests/q/test_q98_demo.py::test_double", "tests/q/test_q98_demo.py::test_double_zero",
            "tests/q/test_q98_demo.py::test_significant"])
        self.assertEqual(len([d for d in res.diagnostics if d.severity == "error"]), 3)
        self.assertTrue(all(d.file == str(self.root / A.TESTS_REL) and d.line > 0
                            for d in res.diagnostics))
        self.assertEqual(res.verified_count, 0)
        self.assertTrue((Path(res.raw_dir) / "junit.xml").is_file())
        self.assert_tree_clean()

    def test_a_filled_file_passes_the_loop_and_the_gate(self):
        self.learner.write_text(FILLED, encoding="utf-8")
        for gate in (False, True):
            res = P.check(self.learner, gate, root=self.root)
            self.assertEqual((res.verdict, res.holes, res.verified_count), ("verified", [], 3))
        self.assertEqual(P.summary_line(res, "f.py", "gate"),
                         "vcheck: f.py [python, gate]: verified — 3 passed, 0 failed, 0 holes")
        self.assert_tree_clean()

    def test_the_gate_needs_zero_holes(self):
        self.learner.write_text(UNTESTED_HOLE, encoding="utf-8")
        loop, gate = P.check(self.learner, root=self.root), P.check(self.learner, True,
                                                                     root=self.root)
        self.assertEqual((loop.verdict, len(loop.holes)), ("verified", 1))
        self.assertEqual((gate.verdict, len(gate.holes)), ("failed", 1))

    def test_a_file_that_does_not_parse(self):
        self.learner.write_text("def broken(:\n", encoding="utf-8")
        res = P.check(self.learner, root=self.root)
        self.assertEqual((res.verdict, res.stage), ("failed", "parse"))

    def test_named_tests(self):
        self.learner.write_text(A.LEARNER.replace(
            'raise NotImplementedError("Q98.H1py")', "return 2 * x"), encoding="utf-8")
        res = P.test(self.learner, ["test_double", "test_double_zero"], root=self.root)
        self.assertEqual((res.verdict, len(res.per_symbol)), ("verified", 2))
        res = P.test(self.learner, ["test_significant"], root=self.root)
        self.assertEqual(res.verdict, "failed")
        res = P.test(self.learner, ["test_nope"], root=self.root)
        self.assertEqual(res.verdict, "failed")
        self.assertEqual([f.kind for f in res.findings], ["test-not-run", "no-tests"])

    def test_a_test_file_with_no_test_is_no_pass(self):
        (self.root / A.TESTS_REL).write_text("x = 1\n", encoding="utf-8")
        res = P.test(self.learner, root=self.root)
        self.assertEqual(res.verdict, "failed")
        self.assertIn("no-tests", [f.kind for f in res.findings])

    def test_the_reference_gate_runs_the_twin_on_an_overlay(self):
        res = P.ref_check(self.twin, root=self.root)
        self.assertEqual((res.verdict, res.holes, res.findings), ("verified", [], []))
        self.assertEqual(res.target, str(self.twin))
        # the learner file is untouched and no overlay is left behind
        self.assertEqual(self.learner.read_text(encoding="utf-8"), A.LEARNER)
        self.assert_tree_clean()

    def test_a_twin_with_a_hole_or_a_lint_finding_fails_the_reference_gate(self):
        self.twin.write_text(UNTESTED_HOLE, encoding="utf-8")
        res = P.ref_check(self.twin, root=self.root)
        self.assertEqual((res.verdict, len(res.holes)), ("failed", 1))
        self.assertIn("hole", [f.kind for f in res.findings])

    def test_triv_bodies_that_fail_admit_the_holes(self):
        for item in ("Q98.H1py", "Q98.H2py"):
            res = P.empty_body(self.twin, item, root=self.root)
            self.assertEqual((res.verdict, res.per_symbol), ("failed", {"TRIV": "failed"}), item)
        self.assert_tree_clean()

    def test_a_triv_body_that_passes_rejects_the_hole(self):
        self.twin.write_text(A.TWIN.replace("# triv: return 0", "# triv: return x * 2"),
                             encoding="utf-8")
        res = P.empty_body(self.twin, "Q98.H1py", root=self.root)
        self.assertEqual(res.verdict, "verified")

    def test_an_item_without_a_triv_body_is_refused(self):
        self.twin.write_text(A.TWIN.replace("# triv: return 0\n", ""), encoding="utf-8")
        res = P.empty_body(self.twin, "Q98.H1py", root=self.root)
        self.assertEqual(res.verdict, "refused")

    def run_cli(self, *args, ci=False):
        e = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
             "GIT_CEILING_DIRECTORIES": str(self.root.parent)}
        e.pop("CI", None)
        if ci:
            e["CI"] = "true"
        p = subprocess.run([sys.executable, "-B", str(A.SCRIPTS / "dvl" / "python.py"), *args],
                           capture_output=True, text=True, env=e, cwd=str(self.root),
                           timeout=600)
        return p.returncode, p.stdout, p.stderr

    def test_cli_check_ref_and_triv(self):
        rc, out, _ = self.run_cli("check", "--root", str(self.root), A.LEARNER_REL)
        self.assertEqual(rc, 1)
        self.assertEqual(out.splitlines()[0], f"vcheck: {A.LEARNER_REL} [python, learner loop]: "
                         "failed — 0 passed, 3 failed, 2 holes")
        rc, out, err = self.run_cli("ref", "--root", str(self.root), A.TWIN_REL, ci=True)
        self.assertEqual((rc, out), (0, f"vcheck: {A.TWIN_REL} [python, reference gate]: "
                                        "verified — 3 passed, 0 failed, 0 holes\n"), err)
        rc, out, err = self.run_cli("triv", "--root", str(self.root), A.TWIN_REL, ci=True)
        self.assertEqual(rc, 0, (out, err))
        self.assertEqual(out.splitlines()[-1], "python.py triv: 2/2 hole(s) pass the gate")
        rc, out, _ = self.run_cli("check", "--json", "--root", str(self.root), A.LEARNER_REL)
        self.assertEqual(rc, 1)
        self.assertIn('"verdict": "failed"', out)


@unittest.skipUnless(A.has_uv() and A.vcheck_has_python(),
                     "uv is not installed, or scripts/vcheck has no Python branch yet")
class VcheckBranch(unittest.TestCase):
    """scripts/vcheck and scripts/vaudit on a learner Python file (QPLAN §11.8
    item 2), once the tools carry the Python branch."""

    def setUp(self):
        self.base = A.tmpdir("py-vcheck-")
        self.root = A.build_root(self.base)

    def tearDown(self):
        A.remove(self.base)

    def tool(self, name, *args, ci=False):
        e = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
             "GIT_CEILING_DIRECTORIES": str(self.root.parent)}
        e.pop("CI", None)
        if ci:
            e["CI"] = "true"
        p = subprocess.run([sys.executable, "-B", str(A.TOOL_SCRIPTS / name), *args,
                            f"--root={self.root}"], capture_output=True, text=True, env=e,
                           cwd=str(self.root), timeout=600)
        return p.returncode, p.stdout, p.stderr

    def test_learner_loop_gate_json_and_test(self):
        rc, out, err = self.tool("vcheck", A.LEARNER_REL)
        self.assertEqual(rc, 1, err)
        self.assertEqual(out.splitlines()[0], f"vcheck: {A.LEARNER_REL} [python, learner loop]: "
                         "failed — 0 passed, 3 failed, 2 holes")
        rc, out, _ = self.tool("vcheck", "--gate", A.LEARNER_REL)
        self.assertEqual(rc, 1)
        rc, out, _ = self.tool("vcheck", "--json", A.LEARNER_REL)
        import json
        d = json.loads(out)
        self.assertEqual((d["lang"], d["verdict"], d["count_unit"], len(d["holes"])),
                         ("python", "failed", "tests", 2))
        rc, out, _ = self.tool("vcheck", "--test", A.LEARNER_REL)
        self.assertEqual(rc, 1)
        self.assertIn("FAILED tests/q/test_q98_demo.py::test_double", out)
        (self.root / A.LEARNER_REL).write_text(FILLED, encoding="utf-8")
        rc, out, err = self.tool("vcheck", "--gate", A.LEARNER_REL)
        self.assertEqual((rc, out), (0, f"vcheck: {A.LEARNER_REL} [python, gate]: verified — "
                                        "3 passed, 0 failed, 0 holes\n"), err)

    def test_reference_gate_and_audit(self):
        rc, out, err = self.tool("vcheck", "--ref", A.TWIN_REL, ci=True)
        self.assertEqual((rc, out.splitlines()[0]),
                         (0, f"vcheck: {A.TWIN_REL} [python, reference gate]: verified — "
                             "3 passed, 0 failed, 0 holes"), err)
        rc, out, err = self.tool("vcheck", A.TWIN_REL)
        self.assertEqual(rc, 3, (out, err))
        rc, out, err = self.tool("vaudit", A.LEARNER_REL)
        self.assertEqual(rc, 0, (out, err))
        self.assertIn("[python, learner]: 0 finding(s)", out)

    def test_python_takes_no_verifier_option(self):
        rc, out, _ = self.tool("vcheck", "--symbol", "double", A.LEARNER_REL)
        self.assertEqual(rc, 3)
        self.assertIn("refused", out)
        rc, _, _ = self.tool("vcheck", "--brittleness", A.LEARNER_REL)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
