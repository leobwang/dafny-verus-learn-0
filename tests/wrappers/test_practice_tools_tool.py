"""Tool tests for the practice tiers' tool requests against the pinned Dafny
4.11.0 and Verus 0.2026.09.27.3cf1832 (QPLAN §30 Q63, Q65; R05.P3dv):

  * Q65  dvl.verus.empty_body: an impl method named by its type (`A::three`,
         `<B as Probe>::three`) is resolved and verified alone, a bare name the
         trait and two impls share is refused; a value-returning proof fn's
         empty body `{ arbitrary() }` reaches verification and fails; an exec
         fn whose code consumes a `let tracked` permission keeps it in E0 and
         fails there (no longer no-verify); firsttry's per-method gate of a
         trait-impl item (impl_methods_gate) with a named `triv:` body;
  * Q63  vcheck --gate --lab-task: the gate passes a delivery that keeps its
         task form's levers and fails one that switches automation back on,
         which the plain gate passes; with the user's decision D24, it also
         applies vaudit's assumption rules: a delivery equal to a task form
         that ships `assume {:axiom}`, or an `{:axiom}` lemma the lever check
         allows, fails although the plain gate passes it; a Verus task form's
         shipped `external_body` fails (the gate counts it); a clean delivery
         passes in both languages;
  * R05.P3dv  vcheck --json --measures in the learner loop carries
         `resource_count` and `wall_s` (both languages); the plain document and
         the gate's record carry neither.

Every job runs through the dvl libraries, under the CLAUDE.md §Resources caps
(Dafny 8G, Verus 16G), one at a time unless DVL_DAFNY_JOBS / DVL_VERUS_JOBS
say otherwise. Every expectation was observed on a real run of these invented
fixtures (2026-10-07). The suite fails, never skips, without the toolchains.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_practice_tools_tool.py'
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

core = C.load_script("vcheck")
firsttry = C.load_script("firsttry")
V = core.V

FX = "tests/wrappers/fixtures"
VFX = C.ROOT / FX / "verus"
LAB_D, LAB_V = f"{FX}/dafny/lab", f"{FX}/verus/lab"


def vf_of(res):
    return res.cmd[res.cmd.index("--verify-function") + 1] if "--verify-function" in res.cmd \
        else None


class VerusEmptyBody(unittest.TestCase):
    def test_qualified_impl_methods(self):
        r = V.empty_body(VFX / "eb_trait.rs", "three", modes=["E0"], seeds=[1])
        self.assertEqual(r.verdict, "refused")
        self.assertIn("name an impl method by its type", r.findings[0].message)
        for sym, vf in (("A::three", "A::three"), ("<B as Probe>::three", "B::three")):
            r = V.empty_body(VFX / "eb_trait.rs", sym, modes=["E0"], seeds=[1])
            self.assertEqual((r.verdict, r.per_symbol), ("failed", {"E0 seed=1": "fails(error)"}),
                             sym)
            self.assertEqual(vf_of(r), vf)
        r = V.empty_body(VFX / "eb_trait.rs", "three_plain", modes=["E0"], seeds=[1])
        self.assertEqual((r.verdict, vf_of(r)), ("verified", "*::three_plain"))

    def test_named_return_proof_fn(self):
        r = V.empty_body(VFX / "eb_named.rs", "witness_three", modes=["E0", "E0H", "E1"],
                         seeds=[1])
        self.assertEqual(r.verdict, "failed")
        self.assertEqual(set(r.per_symbol.values()), {"fails(error)"})

    def test_exec_fn_with_let_tracked(self):
        r = V.empty_body(VFX / "eb_tracked.rs", "read_slot", modes=["E0", "TRIV"], seeds=[1])
        self.assertEqual(r.verdict, "failed")
        self.assertEqual(r.per_symbol, {"E0 seed=1": "fails(error)", "TRIV seed=1": "fails(error)"})


class TraitImplItemGate(unittest.TestCase):
    def test_one_gate_per_hole_method(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl-q65t-"))
        try:
            rel = "verus/q/x/src/lib.rs"
            text = (VFX / "eb_trait_item.rs").read_text()
            (tmp / rel).parent.mkdir(parents=True)
            (tmp / "Solutions" / rel).parent.mkdir(parents=True)
            (tmp / rel).write_text(text)
            (tmp / "Solutions" / rel).write_text(text.replace(
                "// item: Q98.H2v S9\n", "// item: Q98.H2v S9\n// triv: read: { 0 }\n"))
            items, _ = firsttry.ci.parse_items(rel, text)
            it = next(x for x in items if x["id"] == "Q98.H2v")
            methods = firsttry.impl_hole_methods(text, rel, it)
            self.assertEqual(methods, [("<Pair as Acc>::add_one", "add_one"),
                                       ("<Pair as Acc>::read", "read")])
            ok, lines = firsttry.impl_methods_gate(SimpleNamespace(root=tmp), it, rel,
                                                   str(tmp / rel), methods, None, [1])
            self.assertTrue(ok, "\n".join(lines))
            out = "\n".join(lines)
            self.assertIn("the empty body of add_one fails in every run", out)
            self.assertIn("the empty body of read fails in every run", out)
            self.assertIn("TRIV runs read's declared trivial body", out)
        finally:
            shutil.rmtree(tmp)


class JsonMeasures(unittest.TestCase):
    def doc(self, *args):
        rc, out, err = C.tool("vcheck", "--json", *args)
        return rc, json.loads(out)

    def test_learner_loop_carries_both(self):
        for target in (f"{FX}/dafny/ok.dfy", f"{FX}/verus/clean.rs"):
            rc, d = self.doc("--measures", target)
            self.assertEqual((rc, d["verdict"]), (0, "verified"), target)
            self.assertIsInstance(d["resource_count"], int, target)
            self.assertGreater(d["resource_count"], 0, target)
            self.assertIsInstance(d["wall_s"], float, target)
        rc, d = self.doc("--measures", f"{FX}/verus/holes.rs")  # a run that met a hole: no count
        self.assertIsNone(d["resource_count"])
        # without --measures the document is the one the chapters quote (DV5a integration)
        rc, d = self.doc(f"{FX}/dafny/ok.dfy")
        self.assertNotIn("resource_count", d)
        self.assertNotIn("wall_s", d)

    def test_the_gate_carries_neither(self):
        rc, d = self.doc("--gate", f"{FX}/dafny/ok.dfy")
        self.assertEqual(rc, 0)
        self.assertNotIn("resource_count", d)
        self.assertNotIn("wall_s", d)
        rc, out, err = C.tool("vcheck", "--json", "--measures", "--gate", f"{FX}/dafny/ok.dfy")
        self.assertEqual(rc, 2, err)
        rc, out, err = C.tool("vcheck", "--measures", f"{FX}/dafny/ok.dfy")
        self.assertEqual(rc, 2, err)


class LabGate(unittest.TestCase):
    def test_dafny(self):
        rc, out, err = C.tool("vcheck", "--gate", "--lab-task", f"{LAB_D}/task.dfy",
                              f"{LAB_D}/kept.dfy")
        self.assertEqual(rc, 0, out + err)
        rc, out, err = C.tool("vcheck", "--gate", f"{LAB_D}/levered.dfy")
        self.assertEqual(rc, 0, out + err)            # automation closes it: the plain gate passes
        rc, out, err = C.tool("vcheck", "--gate", "--lab-task", f"{LAB_D}/task.dfy",
                              f"{LAB_D}/levered.dfy")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("[dafny, gate]: failed — 2 verified, 0 holes, 0 errors, 2 findings", out)
        self.assertIn(f"{LAB_D}/levered.dfy:7: lab-lever-added: {{:vcs_split_on_every_assert}} "
                      "on LabTask.CountIsN", out)
        self.assertIn("lab-lever-removed: {:induction false} on LabTask.CountIsN", out)

    def test_verus_json(self):
        rc, out, err = C.tool("vcheck", "--gate", "--json", "--lab-task", f"{LAB_V}/task.rs",
                              f"{LAB_V}/levered.rs")
        self.assertEqual(rc, 1, out + err)
        d = json.loads(out)
        self.assertEqual(d["verdict"], "failed")
        self.assertEqual([(f["kind"], f["line"]) for f in d["findings"]],
                         [("lab-lever-added", 13)])
        rc, out, err = C.tool("vcheck", "--gate", f"{LAB_V}/levered.rs")
        self.assertEqual(rc, 0, out + err)

    # The user's decision D24: the lab gate applies vaudit's assumption rules to a delivery.
    def test_dafny_shipped_assumption_fails(self):
        for form, line, kinds in (("axiom_task.dfy", 12, ("assume-axiom", "audit-assume-axiom")),
                                  ("axiom_lemma_task.dfy", 9, ("audit-axiom", "axiom-attribute"))):
            rc, out, err = C.tool("vcheck", "--gate", f"{LAB_D}/{form}")
            self.assertEqual(rc, 0, out + err)        # the plain gate counts no hole
            rc, out, err = C.tool("vcheck", "--gate", "--lab-task", f"{LAB_D}/{form}",
                                  f"{LAB_D}/{form}")  # delivered unchanged: no lever finding
            self.assertEqual(rc, 1, out + err)
            self.assertIn("[dafny, gate]: failed — 2 verified, 0 holes, 0 errors, 2 findings", out)
            for k in kinds:
                self.assertIn(f"{LAB_D}/{form}:{line}: lab-audit: the assumption audit (vaudit) "
                              f"reports {k}: ", out)

    def test_dafny_clean_delivery_passes(self):
        rc, out, err = C.tool("vcheck", "--gate", "--json", "--lab-task", f"{LAB_D}/task.dfy",
                              f"{LAB_D}/kept.dfy")
        self.assertEqual(rc, 0, out + err)
        d = json.loads(out)
        self.assertEqual((d["verdict"], d["findings"]), ("verified", []))

    def test_verus_clean_delivery_passes(self):
        rc, out, err = C.tool("vcheck", "--gate", "--json", "--lab-task", f"{LAB_V}/task.rs",
                              f"{LAB_V}/kept.rs")
        self.assertEqual(rc, 0, out + err)
        d = json.loads(out)
        self.assertEqual((d["verdict"], d["findings"]), ("verified", []))

    def test_verus_shipped_trusted_fn_fails(self):
        rc, out, err = C.tool("vcheck", "--gate", "--json", "--lab-task",
                              f"{LAB_V}/external_task.rs", f"{LAB_V}/external_task.rs")
        self.assertEqual(rc, 1, out + err)
        d = json.loads(out)
        self.assertEqual(d["verdict"], "failed")
        self.assertEqual([(h["kind"], h["line"]) for h in d["holes"]], [("external_body", 16)])


if __name__ == "__main__":
    unittest.main()
