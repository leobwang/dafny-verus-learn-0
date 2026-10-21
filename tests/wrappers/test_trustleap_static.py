"""scripts/dvl/trustleap.py (QPLAN §31.1 item 4, Δ402): the leap scan per language, the
blanking of comments and literals, the TRUST.md table and the two-way diff. Tool-free.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_trustleap_static.py'
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from dvl import trustleap as T  # noqa: E402

DAFNY = '''module M {
  // {:extern} in a comment is not a leap; nor is /* {:axiom} */ this
  method {:extern "Sys", "Now"} Now() returns (t: int)
  lemma {:axiom} Big(x: int) ensures x < x + 1
  method Loop() decreases * { var s := "{:axiom}"; }
  function F(x: int): int { assume {:axiom} x > 0; x }
  method {:verify false} Skip() {}
  method Fine(x: int) returns (y: int) ensures y == x { y := x; }
}
'''

VERUS = '''use vstd::prelude::*;
fn main() {}
verus! {
#[verifier::external_body]
fn f(x: u64) -> u64 { unimplemented!() }
pub assume_specification[ std::mem::swap::<u64> ](a: &mut u64, b: &mut u64);
#[verifier::external]
fn g() { let s = "unsafe /* not */"; let c = 'u'; unsafe { } }
fn h<'a>(x: u64) -> u8 { (#[verifier::truncate] (x as u8)) }
#[verifier::exec_allows_no_decreases_clause]
pub fn spin() { loop {} }
// #[verifier::external_body] in a comment
fn ok(x: u64) -> (r: u64) ensures r == x { x }
}
'''


def kinds(leaps):
    return sorted((lp.construct, lp.symbol) for lp in leaps)


class Scan(unittest.TestCase):
    def test_dafny(self):
        self.assertEqual(kinds(T.scan_text(DAFNY, "dafny", "a.dfy")), sorted([
            ("extern", "Now"), ("axiom", "Big"), ("decreases-star", "Loop"),
            ("assume-axiom", "F"), ("verify-false", "Skip")]))

    def test_verus(self):
        self.assertEqual(kinds(T.scan_text(VERUS, "verus", "b.rs")), sorted([
            ("outside-verus", "main"), ("external-body", "f"),
            ("assume-spec", "std::mem::swap::<u64>"), ("external", "g"), ("unsafe", "g"),
            ("truncate", "h"), ("no-decreases", "spin")]))

    def test_lines_and_no_leap_in_clean_code(self):
        self.assertEqual([lp.line for lp in T.scan_text(DAFNY, "dafny", "a.dfy")
                          if lp.construct == "extern"], [3])
        self.assertEqual(T.scan_text("module N { lemma L() ensures true {} }\n", "dafny", "c.dfy"), [])
        self.assertEqual(T.scan_text("verus! { fn k() {} }\n", "verus", "c.rs"), [])

    def test_blank_keeps_lines_and_offsets(self):
        text = 'a // x\n"s\\"t" /* /* nested */ */ b\n'
        b = T.blank(text, "verus")
        self.assertEqual(len(b), len(text))
        self.assertEqual(b.count("\n"), text.count("\n"))
        self.assertTrue(b.strip().startswith("a") and b.rstrip().endswith("b"))
        self.assertNotIn("x", b)
        self.assertEqual(T.blank('r#"unsafe"#;', "verus").strip(), ";")


TRUST = """# TRUST

## Q30 — another module

| file | symbol | construct | why |
|---|---|---|---|
| x.dfy | X | extern | other |

## Q31 — the gate

Prose before the table.

| file | symbol | construct | why | notes |
|---|---|---|---|---|
| `a.dfy` | Now | extern | the clock is the OS's | |
| a.dfy | Big | axiom |  | |
| a.dfy | Gone | axiom | a stale row | |

### Q31 detail (a lower heading stays in the section)

## Q32

| file | symbol | construct | why |
|---|---|---|---|
| a.dfy | F | assume-axiom | not Q31's |
"""


class Trust(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory(prefix="dvl-trustleap-")
        self.addCleanup(d.cleanup)
        self.path = Path(d.name) / "TRUST.md"
        self.path.write_text(TRUST, encoding="utf-8")

    def test_read_the_module_section_only(self):
        es = T.read_trust(self.path, "Q31")
        self.assertEqual([(e.file, e.symbol, e.construct) for e in es],
                         [("a.dfy", "Now", "extern"), ("a.dfy", "Big", "axiom"),
                          ("a.dfy", "Gone", "axiom")])
        self.assertEqual(T.read_trust(self.path, "Q99"), [])

    def test_diff_both_ways(self):
        leaps = [lp for lp in T.scan_text(DAFNY, "dafny", "a.dfy")]
        found = T.diff(leaps, T.read_trust(self.path, "Q31"))
        text = "\n".join(found)
        self.assertIn("decreases-star on Loop is not listed", text)
        self.assertIn("assume-axiom on F is not listed", text)
        self.assertIn("verify-false on Skip is not listed", text)
        self.assertIn("axiom on Big: its TRUST.md row (line 16) gives no reason", text)
        self.assertIn("axiom on Gone in a.dfy matches no leap", text)
        self.assertNotIn("on Now", text)
        self.assertEqual(len(found), 5)

    def test_a_clean_diff(self):
        lp = [T.Leap("a.dfy", 3, "extern", "Now")]
        self.assertEqual(T.diff(lp, [T.Entry("a.dfy", "Now", "extern", "the OS clock", 1)]), [])

    def test_a_bad_construct_name_is_refused(self):
        self.path.write_text("## Q31\n\n| file | symbol | construct | why |\n|---|---|---|---|\n"
                             "| a.dfy | X | assume | no |\n", encoding="utf-8")
        with self.assertRaises(T.TrustError):
            T.read_trust(self.path, "Q31")

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self._cli()

    def _cli(self):
        src = Path(self.path.parent) / "a.dfy"
        src.write_text(DAFNY, encoding="utf-8")
        self.assertEqual(T.main(["check", "--root", str(self.path.parent), "--module", "Q31",
                                 "--trust", str(self.path), "a.dfy"]), 1)
        self.assertEqual(T.main(["scan", "--root", str(self.path.parent), "a.dfy"]), 0)
        self.path.write_text("## Q31\n\n| file | symbol |\n", encoding="utf-8")
        self.assertEqual(T.main(["check", "--root", str(self.path.parent), "--module", "Q31",
                                 "--trust", str(self.path), "a.dfy"]), 1)


if __name__ == "__main__":
    unittest.main()
