// item: R13.P3dv verdict
// Predict exact proof verdict/stage in each language.
// SLOT: CHECK P3dv
// item: R13.P6dv verdict
// Selected then full scope, exact D/V verdict and stage pairs.
// SLOT: CHECK P6dv
/*!
# R13 — Pipelines and trust (Exercises)

Imports: the given regex spine A1–A4 (`RG_A1_Re`, `RG_A1b_Facts`, `RG_A2_Deriv`, …);
nothing else: no earlier exercise file.

Each item below comes with a fake delivery, shown and run in the chapter (§8): a
version of the same task that some instrument reports as fine (a learner-loop
summary, a gate that does not read statements) while it is not. For each item:
1. Run the fake delivery's instruments, name the stage or the instrument that
   exposes it, and write that attribution in `research/r13_forensics.md`.
2. Then replace the hole with the honest proof. The statement stays as shipped.

Done = `scripts/vcheck --gate dafny/R/R13_Pipelines/std` prints only the summary
line and exits 0, `scripts/vaudit dafny/R/R13_Pipelines/std` reports no finding,
`scripts/specfreeze --check R13` reports none, AND
`scripts/firsttry.sh R13 --report --strict` exits 0.

This file ships with exactly 4 holes: T1 (closed-book test-out) and H1–H3.
*/
module R13_Repairs {
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv
  // specfreeze: frozen-imports

  // Given: the derivative by every character of u, in order.
  function Derivs(r: Re, u: seq<char>): Re
    decreases |u|
  {
    if u == [] then r else Derivs(A2.Deriv(r, u[0]), u[1..])
  }

  // item: R13.T1d
  // pair: R13.T1v
  /** **T1.** (closed book) An executable matcher with the regex semantics as its
      contract. `Matches` is ghost: what may a compiled method call instead, and
      which layer supplies a compiled matcher with this postcondition? */
  method AcceptsR13(r: Re, s: seq<char>) returns (b: bool)
    ensures b == Matches(r, s)
  {
    assume false;
  }
  // Hint(1): the chapter's fake delivery for T1 (§8) shows the call that
  //          does not compile, and the stage that stops it.
  // Hint(2): A2 re-supplies the derivative matcher.


  // item: R13.H1d
  // pair: R13.H1v
  /** **H1.** Taking derivatives by `u + v` is taking them by `u`, then by `v`.
      The fake delivery states this as an axiom. What are the first character
      and the rest of `u + v` when `u` is not empty, and which call is the
      induction hypothesis? */
  lemma {:induction false} DerivsCatR13(r: Re, u: seq<char>, v: seq<char>)
    ensures Derivs(r, u + v) == Derivs(Derivs(r, u), v)
    decreases |u|
  // Hint(1): induction on |u| (the lemma has {:induction false}); the base
  //          case needs `[] + v == v`.
  // Hint(2): state `(u + v)[0] == u[0]` and `(u + v)[1..] == u[1..] + v`, then
  //          call the lemma on the derivative by u[0].


  // item: R13.H2d
  // pair: R13.H2v
  /** **H2.** Every character of `s` lies in the class `cc`: a verified loop over
      A2's class API, where the fake delivery trusts a bodiless method. What
      does the loop know about the prefix it has read, and what ends it early? */
  method ClassCoversR13(cc: A2.CharClass, s: seq<char>) returns (b: bool)
    ensures b == (forall i | 0 <= i < |s| :: A2.InClass(cc, s[i]))
  {
    assume false;
  }
  // Hint(1): a `while` loop with an invariant over the prefix `s[..k]`.
  // Hint(2): A2.ClassMember is executable and promises A2.InClass.


  // item: R13.H3d
  // pair: R13.H3v
  /** **H3.** A word matches exactly when its derivatives end in a nullable
      regex. The fake delivery proves it only for the empty word. Which A1b fact
      is the base case, and which A2 fact moves one character from the word into
      the regex? */
  lemma {:induction false} NullableDerivsR13(r: Re, u: seq<char>)
    ensures Nullable(Derivs(r, u)) <==> Matches(r, u)
    decreases |u|
  // Hint(1): induction on |u|; the base case is RG_A1b_Facts.NullableCorrect.
  // Hint(2): A2.DerivCorrect on (r, u[0], u[1..]), and `[u[0]] + u[1..] == u`.

}
