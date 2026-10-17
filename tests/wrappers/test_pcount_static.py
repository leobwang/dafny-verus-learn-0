"""Tool-free tests for scripts/pcount.py, the proof-line counter of QPLAN §19.0
(Δ53, Δ173) with the layout rule of the user's decision D1 (DV5c): a proof
block that holds one statement counts as one proof line, however it is laid
out.

Every program below is an invented toy (neutral test material for the
counter): none is course content, an exercise, an answer or text from the
reference tree. Nothing here runs a verifier.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_pcount_static.py'
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

pc = C.load_script("pcount")

# One exec fn, its two one-statement proof blocks on one line each.
ONE_LINE = """verus! {
fn tally(v: &Vec<u8>) -> (r: u64)
    ensures r <= 1000,
{
    let mut r: u64 = 0;
    let mut k: usize = 0;
    while k < v.len()
        invariant k <= v.len(),
        decreases v.len() - k,
    {
        proof { lemma_step(k); }
        r = 0;
        k = k + 1;
    }
    proof { lemma_done(r); }
    r
}
}
"""

# The same fn with both blocks laid over three lines.
THREE_LINES = ONE_LINE.replace("        proof { lemma_step(k); }\n",
                               "        proof {\n            lemma_step(k);\n        }\n").replace(
    "    proof { lemma_done(r); }\n", "    proof {\n        lemma_done(r);\n    }\n")

# A two-statement block is not collapsed.
TWO_STATEMENTS = THREE_LINES.replace("            lemma_step(k);\n",
                                     "            lemma_step(k);\n            lemma_step(r);\n")

DAFNY = """module T {
  lemma Twice(n: nat)
    ensures n + n == 2 * n
  {
    assert n + n == 2 * n by {
      assert n * 2 == 2 * n;
    }
    assert true by {
      assert 1 == 1;
      assert 2 == 2;
    }
  }

  method Count(s: seq<nat>) returns (c: nat)
    ensures c <= |s|
  {
    c := 0;
    var i := 0;
    while i < |s|
      invariant 0 <= i <= |s| && c <= i
    {
      assert i < |s| by {
        assert 0 <= i;
      }
      if s[i] == 0 {
        c := c + 1;
      }
      i := i + 1;
    }
  }
}
"""


def counted(text, name, rule=True):
    got = pc.count(text.split("\n"), name, layout_rule=rule)
    return got[0], got[1]


class LayoutRule(unittest.TestCase):
    def test_one_statement_proof_blocks_count_one_line_in_either_layout(self):
        self.assertEqual(counted(ONE_LINE, "tally"), counted(THREE_LINES, "tally"))
        p, c = counted(ONE_LINE, "tally")
        # invariant, decreases and two proof lines; six code lines
        self.assertEqual((p, c), (4, 6))
        # before D1 the three-line layout counted each block twice (opener + statement)
        self.assertEqual(counted(THREE_LINES, "tally", rule=False), (6, 6))
        self.assertEqual(counted(ONE_LINE, "tally", rule=False), (4, 6))

    def test_a_block_of_two_statements_is_not_collapsed(self):
        self.assertEqual(counted(TWO_STATEMENTS, "tally"), (6, 6))
        self.assertEqual(counted(TWO_STATEMENTS, "tally", rule=False), (7, 6))

    def test_dafny_by_blocks(self):
        # a lemma body counts as proof throughout; the one-statement `by` block is one
        # line, the two-statement one is not collapsed
        self.assertEqual(counted(DAFNY, "Twice"), (4, 0))
        self.assertEqual(counted(DAFNY, "Twice", rule=False), (5, 0))
        # in a method: the invariant, the one-line assertion; code lines as before
        self.assertEqual(counted(DAFNY, "Count"), (2, 6))
        self.assertEqual(counted(DAFNY, "Count", rule=False), (3, 6))

    def test_statement_ends(self):
        self.assertEqual(pc._statement_ends("lemma_step(k);"), (1, False))
        self.assertEqual(pc._statement_ends("a(); b();"), (2, False))
        self.assertEqual(pc._statement_ends("if c { a(); } else { b(); }"), (1, False))
        self.assertEqual(pc._statement_ends("if c { a(); } if d { b(); }"), (2, False))
        self.assertEqual(pc._statement_ends("assert(x) by { a(); }"), (1, False))
        self.assertEqual(pc._statement_ends("a(); b"), (1, True))
        self.assertEqual(pc._statement_ends('s("x;y");'), (1, False))

    def test_a_one_line_block_does_not_leave_the_counter_inside_it(self):
        text = """verus! {
fn walk(n: u64) -> (r: u64)
{
    proof { lemma_a(n); }
    if n > 0 {
        let x = n;
    }
    0
}
}
"""
        # with the fix the nested `let x = n;` is code; C.8's counter tagged it P
        self.assertEqual(counted(text, "walk"), (1, 3))
        self.assertEqual(counted(text, "walk", rule=False), (2, 2))


    def test_a_requires_clause_ends_with_its_statement(self):
        """DV5c fix round: an `assert(…) by (…) requires …;` statement (no brace
        body) at the end of a proof block leaves the exec lines after it code."""
        text = """verus! {
fn stack(n: u64) -> (r: u64)
{
    let mut k: u64 = 0;
    while k < n
        decreases n - k,
    {
        proof {
            lemma_twice(k);
            assert(k * 2 <= n * 2) by (nonlinear_arith)
                requires
                    k <= n,
            ;
        }
        k = k + 1;
    }
    k
}
}
"""
        # proof: `decreases`, the block's opener, the call, the assert, `requires`,
        # `k <= n,` and `;`; code: the rest, `k = k + 1;` and the final `k` among
        # them (the counter tagged both P before the fix)
        self.assertEqual(counted(text, "stack"), (7, 4))


class HandCorrections(unittest.TestCase):
    """DV5d: the four counter gaps the Q14 and Q17 notes corrected by hand, on
    invented toys (a counter class, a tally crate)."""

    DAFNY_CLASS = """module T {
  class Counter {
    var k: nat
    ghost var Hist: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Ok()
      reads this
    {
      this in Repr &&
      |Hist| == k
    }

    constructor ()
      ensures Ok()
    {
      k := 0;
      Hist := [];
      Repr := {this};
    }

    method Room()
      modifies this
    {
      k := k;
    }

    method Tick()
      requires Ok()
      modifies this
      ensures Ok()
    {
      Room();
      ghost var h := Hist;
      Step(k);
      k := k + 1;
      Hist := Hist + [k];
      h := Hist;
      assert |Hist| == k
        && k > 0;
    }
  }

  lemma Step(n: nat)
    ensures n + 1 > n
  {
  }
}
"""

    VERUS_CELL = """verus! {
fn bump(&mut self)
{
    let ghost before = self@;
    let (c, Tracked(p)) = PCell::empty();
    self.size = Ghost(self.size@ + 2);
    self.perms = Tracked(p);
    self.slots[0] = Tracked(p);
    self.n = 0;
    assert forall|j: int| 0 <= j < 3 implies #[trigger] f(j)
        == g(j) by { lemma_fg(j); }
    assert(self.size@ > 0
        && before.len() >= 0);
    self.n = 1;
}
}
"""

    def test_a_ghost_predicate_body_is_proof(self):
        self.assertEqual(counted(self.DAFNY_CLASS, "Ok"), (2, 0))

    def test_ghost_field_updates_are_proof_and_exec_assignments_code(self):
        rows = pc.count(self.DAFNY_CLASS.split("\n"), "constructor")[2]
        self.assertEqual(rows, [("C", "k := 0;"), ("P", "Hist := [];"),
                                ("P", "Repr := {this};")])

    def test_an_exec_method_call_is_code_and_a_lemma_call_proof(self):
        rows = dict((s, t) for t, s in pc.count(self.DAFNY_CLASS.split("\n"), "Tick")[2])
        self.assertEqual(rows["Room();"], "C")
        self.assertEqual(rows["Step(k);"], "P")
        self.assertEqual(rows["ghost var h := Hist;"], "P")
        self.assertEqual(rows["h := Hist;"], "P")          # a local ghost's update
        self.assertEqual(rows["Hist := Hist + [k];"], "P")
        self.assertEqual(rows["k := k + 1;"], "C")
        # the assertion's continuation line is proof like its first line
        self.assertEqual(rows["&& k > 0;"], "P")
        self.assertEqual(counted(self.DAFNY_CLASS, "Tick"), (6, 2))

    def test_verus_tracked_and_ghost_updates_and_assertion_continuations(self):
        rows = pc.count(self.VERUS_CELL.split("\n"), "bump")[2]
        tags = [t for t, _ in rows]
        self.assertEqual([s for _, s in rows][1], "let (c, Tracked(p)) = PCell::empty();")
        self.assertEqual(tags, ["P", "C", "P", "P", "P", "C", "P", "P", "P", "P", "C"])
        self.assertEqual(counted(self.VERUS_CELL, "bump"), (8, 3))


class Layout(unittest.TestCase):
    """DV5e review fix: attributes between the keyword and the name, and block
    comments (a brace inside one, comment-only lines), on invented toys."""
    TOY = """function Total(s: seq<nat>): nat { if |s| == 0 then 0 else s[0] + Total(s[1..]) }

lemma {:induction false} TotalAtLeast(s: seq<nat>)
  ensures Total(s) >= 0
{
  assert Total(s) >= 0;
}

lemma Braced(s: seq<nat>)
  ensures Total(s) >= 0
{
  /* a remark with a brace { that never closes */
  assert Total(s) >= 0;
}

lemma Spread(s: seq<nat>)
  ensures Total(s) >= 0
{
  /* a remark
     over lines } with a brace
     /* and a nested one */ */
  assert Total(s) >= 0;
}

method Tail(s: seq<nat>) returns (r: nat)
  ensures r == 0
{
  r := 0;
  var t := "{";
  var c := '{';
}
"""

    def test_an_attribute_before_the_name(self):
        src = self.TOY.split("\n")
        self.assertEqual(pc.count(src, "TotalAtLeast")[:2], (1, 0))
        self.assertEqual(pc.stmt_lines(src, "TotalAtLeast"), 2)

    def test_block_comments_are_neither_counted_nor_scanned(self):
        src = self.TOY.split("\n")
        self.assertEqual(pc.count(src, "Braced")[:2], (1, 0))
        self.assertEqual(pc.count(src, "Spread")[:2], (1, 0))
        self.assertEqual(pc.count(src, "Tail")[:2], (0, 3))   # braces in literals move nothing

    def test_strip_keeps_the_line_count(self):
        src = self.TOY.split("\n")
        self.assertEqual(len(pc.strip_comments(src)), len(src))


class Lookup(unittest.TestCase):
    def test_nth_declaration_and_statement_lines(self):
        text = """verus! {
pub trait Acc { fn get(&self) -> u64; }
impl Acc for u64 {
    fn get(&self) -> u64 {
        proof { lemma_a(1); }
        *self
    }
}
pub open spec fn twice(x: nat) -> nat {  // a comment after the brace
    x + x
}
proof fn lemma_b(x: nat)
    requires
        x > 0,
    ensures
        twice(x) > x,
{
}
}
"""
        src = text.split("\n")
        self.assertEqual(pc.count(src, "get@2")[:2], (1, 1))
        self.assertEqual(pc.count(src, "twice")[:2], (0, 1))   # the comment hides no brace
        self.assertIsNone(pc.count(src, "missing"))
        self.assertEqual(pc.stmt_lines(src, "lemma_b"), 5)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "toy.rs"
            f.write_text(THREE_LINES, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(pc.main([f"{f}:tally"]), 0)
                self.assertEqual(pc.main(["--no-layout-rule", f"{f}:tally"]), 0)
                self.assertEqual(pc.main([f"{f}:nothing"]), 2)
                self.assertEqual(pc.main(["--show", f"{f}:tally"]), 0)
            lines = out.getvalue().split("\n")
            self.assertEqual(lines[0], "tally: proof 4, code 6, total 10")
            self.assertEqual(lines[1], "tally: proof 6, code 6, total 12")
            self.assertEqual(lines[2], "nothing: not found")
            self.assertIn("   P proof { lemma_step(k); }", lines)


if __name__ == "__main__":
    unittest.main()
