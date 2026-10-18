/*!
# R14 — SMT mechanics (Reference Solution)

Imports: the given regex spine A1 (`RG_A1_Re`: the `Re` datatype and `NodeCount`),
A1b and A2 (`RG_A2_Deriv`: `Deriv`); nothing else: no earlier exercise file.
R14 states its own copy of the regex semantics, `MatchesV`, with triggers chosen
here, so that every trigger question in this module is about a definition you can
read in this file.

How to work this file:
1. Predictions first: fill the slots of the prediction block below (verdicts in
   slots/R14.slots) and of specimens/R14/P*.specimen, then record the first tries
   with `scripts/firsttry.sh R14 --check`.
2. Replace each hole, H1 to H3, in order.
3. Done = `scripts/vcheck --gate dafny/R/R14_Smt/std` prints only the summary line
   and exits 0, `scripts/vaudit dafny/R/R14_Smt/std` reports no finding, AND
   `scripts/firsttry.sh R14 --report --strict` exits 0. The levers printed on the
   lemmas (`{:induction false}`) are part of the task: keep them.

This file ships with exactly 3 holes: H1–H3.
*/
// =============================================================================
// Predictions (commit before you run anything they are about)
// =============================================================================

// item: R14.P1dv verdict
// specimens/R14/P1-d.dfy.specimen and P1-v.rs.specimen: a lemma whose
// hypothesis is a quantifier that feeds its own trigger, and a false goal.
// Answer form in slots/R14.slots: `D:<verdict> V:<verdict>`.
// CHECK P1dv

// item: R14.P2dv verdict
// specimens/R14/P2-d.dfy.specimen and P2-v.rs.specimen: `(x + y) * (x + y)
// >= x * x + y * y` for naturals, empty body. Answer form: `D:<verdict> V:<verdict>`.
// CHECK P2dv

// item: R14.P5dv verdict
// specimens/R14/P5-d.dfy.specimen and P5-v.rs.specimen: the size of three
// nested Stars, empty body, default settings. Answer form: `D:<verdict> V:<verdict>`.
// CHECK P5dv

// item: R14.C5dv diverge:nonlinear-arith
// Dafny lets Z3 try nonlinear arithmetic on every query; Verus turns it off and
// proves a product fact `by (nonlinear_arith)`, a separate query that sees only
// the facts its `requires` lists (P2, H3).

module R14_Mechanics {
  import opened RG_A1_Re
  import A2 = RG_A2_Deriv

  // R14's own semantics: A1's Matches, with the triggers stated. A split is
  // found only through a term MatchesV(a, s[..i]) for the left part.
  ghost predicate MatchesV(r: Re, s: seq<char>)
    decreases r, |s|
  {
    match r
    case Empty => false
    case Eps => s == []
    case Chr(c) => s == [c]
    case Alt(a, b) => MatchesV(a, s) || MatchesV(b, s)
    case Cat(a, b) =>
      exists i {:trigger MatchesV(a, s[..i])} | 0 <= i <= |s| :: MatchesV(a, s[..i]) && MatchesV(b, s[i..])
    case Star(a) =>
      s == [] || exists i {:trigger MatchesV(a, s[..i])} | 0 < i <= |s| :: MatchesV(a, s[..i]) && MatchesV(Star(a), s[i..])
  }

  // Given: n copies of c.
  function PowerWord(c: char, n: nat): seq<char>
  {
    if n == 0 then [] else [c] + PowerWord(c, n - 1)
  }

  // item: R14.H1d
  // uses: trigger
  // pair: R14.H1v
  /** **H1.** A word of `a` followed by a word of `b` matches `Cat(a, b)`.

      Reference: the Cat existential is triggered by `MatchesV(a, s[..i])`.
      With `s = u + v`, stating `s[..|u|] == u` and `s[|u|..] == v` puts the
      split's terms in the solver's equivalence classes: `MatchesV(a, u)` is now
      a `MatchesV(a, s[..|u|])` term, which instantiates the existential at
      `i = |u|`. Without the two equations no term matches the trigger. */
  lemma CatIntroV(a: Re, b: Re, u: seq<char>, v: seq<char>)
    requires MatchesV(a, u) && MatchesV(b, v)
    ensures MatchesV(Cat(a, b), u + v)
  {
    var s := u + v;
    assert s[..|u|] == u;
    assert s[|u|..] == v;
  }

  // item: R14.H2d
  // uses: trigger
  // pair: R14.H2v
  /** **H2.** Every power of `c` matches `Star(Chr(c))`.

      Reference: induction on `n`. The first chunk is `[c]`, the rest is
      `PowerWord(c, n - 1)`, which the induction hypothesis matches; the Star case's
      trigger needs the term `MatchesV(Chr(c), s[..1])`, so the proof states it.
      Fuel cannot replace the induction: it unfolds `MatchesV` a fixed number of
      times, which covers one `n`, never every `n`. */
  lemma {:induction false} StarPowV(c: char, n: nat)
    ensures MatchesV(Star(Chr(c)), PowerWord(c, n))
  {
    if n > 0 {
      StarPowV(c, n - 1);
      var s := PowerWord(c, n);
      assert s[..1] == [c] && s[1..] == PowerWord(c, n - 1);
      assert MatchesV(Chr(c), s[..1]);
    }
  }

  // item: R14.H3d
  // uses: nonlinear-arith
  // pair: R14.H3v
  /** **H3.** A derivative is at most twice the square of its regex's size.

      Reference: structural induction. In the Alt, Cat and Star cases the
      induction hypotheses bound each derivative by `2 x^2`, and what is left is
      a product inequality, `2a^2 + b + 2b^2 + 2 <= 2(1 + a + b)^2` in the
      nullable Cat case. The solver does not expand squares of unknowns; the
      proof states each expansion as an assertion about the products. */
  lemma {:induction false} DerivSizeV(r: Re, c: char)
    ensures NodeCount(A2.Deriv(r, c)) <= 2 * NodeCount(r) * NodeCount(r)
  {
    match r
    case Empty =>
    case Eps =>
    case Chr(d) =>
    case Alt(a, b) =>
      DerivSizeV(a, c);
      DerivSizeV(b, c);
      SquareGrowth(NodeCount(a), NodeCount(b));
    case Cat(a, b) =>
      DerivSizeV(a, c);
      DerivSizeV(b, c);
      SquareGrowth(NodeCount(a), NodeCount(b));
    case Star(a) =>
      DerivSizeV(a, c);
      SquareGrowth(NodeCount(a), 0);
  }

  // reference-only: the learner's own helper, the product inequality every case needs.
  lemma SquareGrowth(x: nat, y: nat)
    ensures 2 + 2 * x * x + y + 2 * y * y <= 2 * (1 + x + y) * (1 + x + y)
    ensures 2 + 2 * x * x + x <= 2 * (1 + x) * (1 + x)
  {
    assert 2 * (1 + x + y) * (1 + x + y) == 2 + 4 * x + 4 * y + 2 * x * x + 4 * x * y + 2 * y * y;
    assert 2 * (1 + x) * (1 + x) == 2 + 4 * x + 2 * x * x;
    assert x * y >= 0;
  }
}
