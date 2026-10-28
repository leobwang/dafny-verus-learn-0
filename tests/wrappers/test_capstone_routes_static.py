"""Tool-free tests for the capstone's two routes (the user's decisions of 2026-10-12):

  * D9   firsttry --empty-body's statement route: an admitted statement item that
         ships no hole (Q18.H2d/H2v) is checked on its reference statements and the
         reference delivery (contract_header, statements_path, statement_items,
         new_statements, statement_route);
  * D16  the binary route: scripts/gen_units.py renders the capstone crate's [[bin]]
         target, dvl.verus.bin_targets reads it, dvl.verus.run_bin refuses what it
         cannot build, and vcheck --bin's argument policy.

Nothing here runs Dafny or Verus: the gate and the binary run are mocked or never
reached, and the statement tables are the static parsers'. The real runs are in
test_capstone_routes_tool.py.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_capstone_routes_static.py'
"""

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
firsttry = C.load_script("firsttry")
import gen_units as gu  # noqa: E402
V, common = core.V, core.common

AGENT = "dafny/Q/Q98_Fx/agent/Q98_Agent.dfy"
STMTS = "research/q98_statements.dfy"
CONTRACT = ("/* CONTRACT\n"
            "goal: prove every statement of the STATEMENTS section, changing no statement\n"
            "allowed-files:\n"
            f"  - {AGENT}\n"
            "acceptance:\n"
            f"  - `scripts/vcheck --gate {AGENT}` exits 0 with zero tool-counted holes\n"
            f"  - `scripts/specfreeze --against {STMTS} {AGENT}` reports no change\n"
            "*/\n")
SHIPPED = (CONTRACT + "module Q98_Agent {\n"
           "  // item: Q98.H1d S12\n"
           "  // ### STATEMENTS (learner-owned)\n"
           "}\n")
REF_STMTS = (CONTRACT + "module Q98_Agent {\n"
             "  // item: Q98.H1d S12\n"
             "  // ### STATEMENTS (learner-owned)\n"
             "  function Twice(x: nat): nat { x + x }\n"
             "  lemma TwiceEven(x: nat)\n"
             "    ensures Twice(x) % 2 == 0\n"
             "}\n")
DELIVERY = REF_STMTS.replace("    ensures Twice(x) % 2 == 0\n",
                             "    ensures Twice(x) % 2 == 0\n  {\n  }\n")


class StatementRoute(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="stmt-route-"))
        for rel, text in ((AGENT, SHIPPED), (f"Solutions/{STMTS}", REF_STMTS),
                          (f"Solutions/{AGENT}", DELIVERY)):
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        item = {"id": "Q98.H1d", "kind": "H", "file": AGENT, "line_start": 9, "line_end": 11}
        rec = {"admissible": {"Q98.H1d": {"admitted": True, "minutes": 10, "fallback": "x",
                                          "exception": "statement-item: the learner states"}}}
        self.item = item
        self.ctx = SimpleNamespace(root=self.root, rec=rec, items=[item], mid="Q98",
                                   text=lambda rel: (self.root / rel).read_text(encoding="utf-8"))

    def tearDown(self):
        shutil.rmtree(self.root)

    def route(self, gate=None):
        gate = gate or common.Result("dafny", "x", 0, "verified", "verify", 3)
        with mock.patch.object(firsttry, "delivery_gate", return_value=gate), \
                mock.patch.object(firsttry, "shipped_text", return_value=None):
            return firsttry.statement_route(self.ctx, self.item, AGENT)

    def test_contract_line(self):
        self.assertEqual(firsttry.statements_path(SHIPPED, AGENT), STMTS)
        self.assertIsNone(firsttry.statements_path(SHIPPED, "other.dfy"))
        self.assertIsNone(firsttry.statements_path("module M {}\n" + CONTRACT, AGENT))
        self.assertEqual(firsttry.contract_header("/* CONTRACT\nunclosed\n"), "")

    def test_statement_items(self):
        self.assertEqual([it["id"] for it, _ in firsttry.statement_items(self.ctx, set())],
                         ["Q98.H1d"])
        self.assertEqual(firsttry.statement_items(self.ctx, {"Q98.H1d"}), [])  # holds a hole
        self.ctx.rec["admissible"]["Q98.H1d"]["exception"] = "short-format band: why"
        self.assertEqual(firsttry.statement_items(self.ctx, set()), [])
        self.ctx.rec["admissible"]["Q98.H1d"] = {"admitted": False, "minutes": 0,
                                                 "fallback": "x"}
        self.assertEqual(firsttry.statement_items(self.ctx, set()), [])

    def test_an_admitted_item_with_no_hole_and_no_route_is_ungated(self):
        # the exception deleted or retyped: the item keeps its minutes and no gate
        # runs, which --empty-body reports as a failure (DV5d review fix)
        self.assertEqual(firsttry.ungated_items(self.ctx, {"Q98.H1d"}), [])
        self.assertEqual(firsttry.ungated_items(self.ctx, set()), ["Q98.H1d"])
        self.ctx.rec["admissible"]["Q98.H1d"].pop("exception")
        self.assertEqual(firsttry.statement_items(self.ctx, set()), [])
        self.assertEqual(firsttry.ungated_items(self.ctx, set()), ["Q98.H1d"])
        self.ctx.rec["admissible"]["Q98.H1d"]["admitted"] = False
        self.assertEqual(firsttry.ungated_items(self.ctx, set()), [])

    def test_empty_body_fails_on_an_ungated_admission(self):
        self.ctx.rec["admissible"]["Q98.H1d"]["exception"] = "short-format band: retyped"
        out = io.StringIO()
        with mock.patch.object(firsttry, "hole_items", return_value=[({"id": "Q98.X"}, "x")]), \
                mock.patch.object(firsttry, "_empty_body_items", return_value=0), \
                mock.patch.object(firsttry, "TwinShadows"), contextlib.redirect_stdout(out):
            rc = firsttry.mode_empty_body(self.ctx, None, None)
        self.assertNotEqual(rc, core.EXIT_OK)
        self.assertIn("? Q98.H1d  admitted with no hole and no statement-item exception",
                      out.getvalue())

    def test_passes_on_a_frozen_delivery(self):
        ok, lines = self.route()
        self.assertTrue(ok, lines)
        self.assertIn("✓ Q98.H1d  the statement route", lines[0])
        self.assertIn("2 statement(s) the shipped file lacks", lines[0])

    def test_a_changed_statement_fails(self):
        p = self.root / "Solutions" / AGENT
        p.write_text(DELIVERY.replace("% 2 == 0", "% 2 <= 1"), encoding="utf-8")
        ok, lines = self.route()
        self.assertFalse(ok)
        self.assertTrue(any("specfreeze --against" in x for x in lines), lines)
        self.assertTrue(any("freeze-changed" in x for x in lines), lines)

    def test_a_failing_or_holed_delivery_fails(self):
        for res in (common.Result("dafny", "x", 1, "failed", "verify", 2),
                    common.Result("dafny", "x", 0, "verified", "verify", 3,
                                  holes=[common.Hole("f", 1, 1, "assume", "Q98.H1d")])):
            ok, lines = self.route(res)
            self.assertFalse(ok)
            self.assertIn("does not pass the reference gate", lines[0])

    def test_reference_statements_that_add_nothing_fail(self):
        (self.root / "Solutions" / STMTS).write_text(SHIPPED, encoding="utf-8")
        ok, lines = self.route()
        self.assertFalse(ok)
        self.assertIn("add no statement", lines[0])

    def test_missing_pieces_are_named(self):
        (self.root / "Solutions" / STMTS).unlink()
        ok, lines = self.route()
        self.assertFalse(ok)
        self.assertIn("no reference statements", lines[0])
        (self.root / AGENT).write_text(SHIPPED.replace("--against", "--check"),
                                       encoding="utf-8")
        ok, lines = self.route()
        self.assertFalse(ok)
        self.assertIn("names no single `scripts/specfreeze --against", lines[0])


def quiet_main(args):
    """(exit code, stdout, stderr) of vcheck's main() in-process."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = core.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class BinTarget(unittest.TestCase):
    def test_rendered_only_for_the_capstone(self):
        q18 = gu.render_crate("Q18", "q18_practice_iiic", "L7")
        self.assertIn('[[bin]]\nname = "bignat"\npath = "src/main.rs"\n', q18)
        self.assertLess(q18.index("[lib]"), q18.index("[[bin]]"))
        self.assertLess(q18.index("[[bin]]"), q18.index("[dependencies]"))
        self.assertNotIn("[[bin]]", gu.render_crate("Q17", "q17_practice_iiib", "L7"))
        r16 = gu.render_crate("R16", "r16_capstone", "A5")
        self.assertIn('[[bin]]\nname = "rexc"\npath = "src/main.rs"\n', r16)
        self.assertNotIn("[[bin]]", gu.render_crate("R15", "r15_verifier_loop", "A4"))

    def test_bin_targets(self):
        d = Path(tempfile.mkdtemp(prefix="bin-targets-"))
        try:
            (d / "Cargo.toml").write_text('[package]\nname = "a"\n[[bin]]\nname = "t"\n'
                                          'path = "src/main.rs"\n', encoding="utf-8")
            self.assertEqual(V.bin_targets(d), [("t", (d / "src/main.rs").resolve())])
            (d / "Cargo.toml").write_text('[package]\nname = "a"\n[[bin]]\nname = "t"\n',
                                          encoding="utf-8")
            with self.assertRaises(V.Refused):
                V.bin_targets(d)
        finally:
            shutil.rmtree(d)

    def test_run_bin_refusals(self):
        d = Path(tempfile.mkdtemp(prefix="bin-refuse-"))
        try:
            with mock.patch.object(V, "verus_bin", return_value="/nonexistent/verus"):
                res, out = V.run_bin(str(d))
                self.assertEqual((res.verdict, out), ("refused", None))
                self.assertIn("takes a crate directory", res.findings[0].message)
                (d / "Cargo.toml").write_text('[package]\nname = "a"\n', encoding="utf-8")
                res, out = V.run_bin(str(d))
                self.assertIn("has no [[bin]] target", res.findings[0].message)
                (d / "Cargo.toml").write_text('[package]\nname = "a"\n[[bin]]\nname = "t"\n'
                                              'path = "src/main.rs"\n', encoding="utf-8")
                res, out = V.run_bin(str(d))
                self.assertIn("does not exist", res.findings[0].message)
        finally:
            shutil.rmtree(d)

    def test_vcheck_bin_usage(self):
        crate = "tests/wrappers/fixtures/verus/cli"
        for args in (("--bin",), ("--bin", "--gate", crate), ("--bin", "--json", crate),
                     ("--bin", crate, crate), ("--bin", "--test", crate)):
            with mock.patch.object(V, "run_bin") as rb:
                rc, _, err = quiet_main(args)
            self.assertEqual(rc, core.EXIT_USAGE, args)
            self.assertIn("usage: vcheck --bin", err)
            rb.assert_not_called()

    def test_vcheck_bin_passes_the_arguments_after_the_separator(self):
        crate = str(C.ROOT / "tests/wrappers/fixtures/verus/cli")
        res = common.Result("verus", crate, 0, "verified", "run", 2)
        run = V.BinRun("tally", ["sum", "2", "40"], 0, "42\n", "")
        with mock.patch.object(V, "run_bin", return_value=(res, run)) as rb:
            rc, out, _ = quiet_main(["--bin", crate, "--", "sum", "2", "40"])
        self.assertEqual(rc, core.EXIT_OK)
        self.assertEqual(list(rb.call_args.args[1]), ["sum", "2", "40"])
        self.assertEqual(out, "vcheck: tests/wrappers/fixtures/verus/cli [verus, bin tally]: "
                              "built — 2 verified; ran `tally sum 2 40`: exit 0\n42\n")
        res = common.Result("verus", crate, 2, "failed", "run", 2)
        run = V.BinRun("tally", ["x"], 2, "", "usage\n")
        with mock.patch.object(V, "run_bin", return_value=(res, run)):
            rc, _, err = quiet_main(["--bin", crate, "--", "x"])
        self.assertEqual((rc, err), (core.EXIT_FAIL, "usage\n"))


if __name__ == "__main__":
    unittest.main()
