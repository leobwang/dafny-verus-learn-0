"""scripts/dvl/reach.py (QPLAN §31.1 item 6, Δ402): denied names and modules in both
languages, required roots, reference reach through include forms, the manifest table.
Tool-free.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_reach_static.py'
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from dvl import reach as R  # noqa: E402

POLICY = {"deny_names": ["LemmaMulComm", "vstd::arithmetic::mul::lemma_mul_is_commutative"],
          "deny_modules": ["Std.Arithmetic.LittleEndianNat", "vstd::arithmetic::mul"],
          "require": ["Sorted", "heapsort"]}


def found(text, lang, policy=POLICY):
    return R.scan_text(text, lang, "f", policy)


class Dafny(unittest.TestCase):
    def test_clean(self):
        f, defs = found("module M {\n  predicate Sorted(s: seq<int>) { true }\n"
                        "  // LemmaMulComm in a comment\n  const s := \"LemmaMulComm\"\n}\n", "dafny")
        self.assertEqual(f, [])
        self.assertIn("Sorted", defs)

    def test_denied_name_and_module(self):
        f, _ = found("module M {\n  import opened Std.Arithmetic.LittleEndianNat\n"
                     "  lemma L() { LemmaMulComm(1, 2); }\n}\n", "dafny")
        self.assertEqual(len(f), 2)
        self.assertIn("f:3: names the denied declaration LemmaMulComm", f)
        self.assertIn("f:2: reaches the denied module Std.Arithmetic.LittleEndianNat", f)

    def test_qualified_and_alias_reach(self):
        f, _ = found("module M {\n  import A = Std . Arithmetic . LittleEndianNat\n}\n", "dafny")
        self.assertEqual(len(f), 1)
        f, _ = found("module M { lemma L() { Std.Arithmetic.LittleEndianNat.X(); } }\n", "dafny")
        self.assertEqual(len(f), 1)
        f, _ = found("module M { import opened Std.Arithmetic.Power }\n", "dafny")
        self.assertEqual(f, [])

    def test_reference_include(self):
        f, _ = found('include "../../Solutions/x.dfy"\nmodule M {}\n', "dafny")
        self.assertEqual(f, ["f:1: reaches a reference or held-out path through an include form"])


class Verus(unittest.TestCase):
    def test_denied(self):
        f, defs = found("use vstd::prelude::*;\nuse vstd::arithmetic::mul::*;\nverus! {\n"
                        "fn heapsort() {}\nproof fn p() { lemma_mul_is_commutative(1, 2); }\n}\n",
                        "verus")
        self.assertEqual(len(f), 2)
        self.assertIn("heapsort", defs)
        f, _ = found("verus! { proof fn p() { vstd::arithmetic::mul::lemma_mul_basics(1); } }\n",
                     "verus")
        self.assertEqual(f, ["f:1: reaches the denied module vstd::arithmetic::mul"])

    def test_path_and_include(self):
        f, _ = found('#[path = "../Hidden/a.rs"]\nmod a;\n', "verus")
        self.assertEqual(len(f), 1)
        f, _ = found('const X: &str = include_str!("../Solutions/x.rs");\n', "verus")
        self.assertEqual(len(f), 1)


class Files(unittest.TestCase):
    def test_required_roots_and_cargo(self):
        with tempfile.TemporaryDirectory(prefix="dvl-reach-") as d:
            d = Path(d)
            (d / "a.dfy").write_text("module M { predicate Sorted(s: seq<int>) { true } }\n")
            (d / "Cargo.toml").write_text('[dependencies]\nx = { path = "../Solutions/x" }\n')
            got = R.scan(["a.dfy", "Cargo.toml"], POLICY, d)
            self.assertIn("the required declaration heapsort is not defined in the delivery", got)
            self.assertTrue(any("include form" in g for g in got))
            self.assertEqual(len(got), 2)

    def test_manifest(self):
        with tempfile.TemporaryDirectory(prefix="dvl-reach-") as d:
            m = Path(d) / "Q31_Statement.toml"
            m.write_text('[reach]\ndeny_names = ["X"]\n')
            self.assertEqual(R.load_policy(m), {"deny_names": ["X"], "deny_modules": [], "require": []})
            m.write_text('[reach]\ndeny = ["X"]\n')
            with self.assertRaises(R.PolicyError):
                R.load_policy(m)
            m.write_text('[reach]\ndeny_names = ["X"]\n')
            (Path(d) / "a.dfy").write_text("module M { lemma X() {} }\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(R.main(["--manifest", str(m), "--root", d, "a.dfy"]), 1)
            m.write_text("not toml [")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(R.main(["--manifest", str(m), "--root", d, "a.dfy"]), 3)


if __name__ == "__main__":
    unittest.main()
