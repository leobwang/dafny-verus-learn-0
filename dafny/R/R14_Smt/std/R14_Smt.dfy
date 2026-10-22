/*!
# R14 — SMT mechanics (Exercises)

Imports: the given regex spine A1 (`RG_A1_Re`: the `Re` datatype and `NodeCount`),
A1b and A2 (`RG_A2_Deriv`: `Deriv`); nothing else: no earlier exercise file.
R14 states its own copy of the regex semantics, `MatchesV`, with triggers chosen
here, so that every trigger question in this module is about a definition you can
read in this file.

How to work this file:
1. Predictions first: fill the slots of the prediction block below (verdicts in
   slots/R14.slots) and of specimens/R14/P*.specimen, then record the first tries
   with `scripts/firsttry.sh R14 --check`.
2. Replace each hole, H1 to H4, in order.
3. Done = `scripts/vcheck --gate dafny/R/R14_Smt/std` prints only the summary line
   and exits 0, `scripts/vaudit dafny/R/R14_Smt/std` reports no finding, AND
   `scripts/firsttry.sh R14 --report --strict` exits 0. The levers printed on the
   lemmas (`{:induction false}`) are part of the task: keep them.

This file ships with exactly 4 holes: H1–H4.
*/
// =============================================================================
// Predictions (commit before you run anything they are about)
// =============================================================================

// item: R14.P1dv verdict
// specimens/R14/P1-d.dfy.specimen and P1-v.rs.specimen: a lemma whose
// hypothesis is a quantifier that feeds its own trigger, and a false goal.
// Answer form in slots/R14.slots: `D:<verdict> V:<verdict>`.
// SLOT: CHECK P1dv

// item: R14.P2dv verdict
// specimens/R14/P2-d.dfy.specimen and P2-v.rs.specimen: `(x + y) * (x + y)
// >= x * x + y * y` for naturals, empty body. Answer form: `D:<verdict> V:<verdict>`.
// SLOT: CHECK P2dv

// item: R14.P5dv verdict
// specimens/R14/P5-d.dfy.specimen and P5-v.rs.specimen: the size of three
// nested Stars, empty body, default settings. Answer form: `D:<verdict> V:<verdict>`.
// SLOT: CHECK P5dv

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

  // item: R14.W1d
  /** **W1.** (worked) A word of `a` followed by a word of `b` matches `Cat(a, b)`.
      The Cat existential is triggered by `MatchesV(a, s[..i])`: with `s = u + v`,
      the two equations put `u` and `v` in the equivalence classes of the split's
      slices, so `MatchesV(a, u)` is a trigger term at `i = |u|`. */
  lemma CatIntroV(a: Re, b: Re, u: seq<char>, v: seq<char>)
    requires MatchesV(a, u) && MatchesV(b, v)
    ensures MatchesV(Cat(a, b), u + v)
  {
    var s := u + v;
    assert s[..|u|] == u;
    assert s[|u|..] == v;
  }

  // item: R14.H1d
  // uses: trigger
  // pair: R14.H1v
  /** **H1.** Two non-empty words of `a`, one after the other, match `Star(a)`.
      The Star case of MatchesV is an existential triggered by `MatchesV(a, s[..i])`,
      and it recurses on the rest. Which terms must the solver see for the outer
      split of `u + v`, and which for `v` alone as a one-chunk word of `Star(a)`? */
  lemma TwoChunksV(a: Re, u: seq<char>, v: seq<char>)
    requires MatchesV(a, u) && MatchesV(a, v) && u != [] && v != []
    ensures MatchesV(Star(a), u + v)
  // Hint(1): no induction: two levels of the same existential, each waiting for its term.
  // Hint(2): first make `MatchesV(Star(a), v)` hold through the split of `v` at `|v|`;
  //          then split `u + v` at `|u|` with two equations between sequences.

  // item: R14.H2d
  // uses: trigger
  // pair: R14.H2v
  /** **H2.** Every power of `c` matches `Star(Chr(c))`. Why can `{:fuel}`
      prove this for `n = 3` but not for every `n`, and which term must the
      Star case's trigger see once you have the induction hypothesis? */
  lemma {:induction false} StarPowV(c: char, n: nat)
    ensures MatchesV(Star(Chr(c)), PowerWord(c, n))
  // Hint(1): induction on n (the lemma has {:induction false}).
  // Hint(2): the first chunk of `PowerWord(c, n)` is `[c]`: the Star case must see
  //          it as a term `s[..1]`, together with a match of that chunk.


  // item: R14.H3d
  // uses: nonlinear-arith
  // pair: R14.H3v
  /** **H3.** The Cat case of H4 on its own: from the two bounds on the operands'
      derivatives, the bound on the Cat's derivative. What is left after `NodeCount`
      and `Deriv` unfold is an inequality between products of `NodeCount(a)` and
      `NodeCount(b)`: which one, and how do you get the solver to multiply it out? */
  lemma CatCaseV(a: Re, b: Re, c: char)
    requires NodeCount(A2.Deriv(a, c)) <= 2 * NodeCount(a) * NodeCount(a)
    requires NodeCount(A2.Deriv(b, c)) <= 2 * NodeCount(b) * NodeCount(b)
    ensures NodeCount(A2.Deriv(Cat(a, b), c)) <= 2 * NodeCount(Cat(a, b)) * NodeCount(Cat(a, b))
  {
    assume false;
  }
  // Hint(1): write `x` for `NodeCount(a)` and `y` for `NodeCount(b)`; the nullable case needs `2 + 2x^2 + y + 2y^2 <= 2(1 + x + y)^2`.
  // Hint(2): a lemma of your own over two naturals, whose body states each square in expanded form.

  // item: R14.H4d
  // uses: nonlinear-arith
  // pair: R14.H4v
  /** **H4.** A derivative is at most twice the square of its regex's size.
      The induction is structural; what is left in the Alt, Cat and Star
      cases is an inequality between products of the subterms' sizes; H3 is the
      Cat case. Which inequality do the Alt and Star cases need? */
  lemma {:induction false} DerivSizeV(r: Re, c: char)
    ensures NodeCount(A2.Deriv(r, c)) <= 2 * NodeCount(r) * NodeCount(r)
  // Hint(1): one induction call per subterm; the Cat case is then H3.
  // Hint(2): the Alt and Star cases need inequalities of H3's shape at the subterms' sizes.

}
