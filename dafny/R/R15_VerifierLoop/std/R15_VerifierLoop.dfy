/*!
# R15 — Verifier loop (Exercises)

Standalone R track. Import only the frozen layers A1 to A4; no earlier learner
file is needed. The paired exercise is verus/r/r15_verifier_loop/src/lib.rs.

This file is rung 4 of the escalation ladder (the chapter's §1): a proof of the
same matcher that rungs 1 to 3 only ran, checked and tested. Record the
predictions first (scripts/firsttry.sh R15 --check), then attempt T1 closed
book. Two typed holes ship in this language; the two predictions are switched
on by the CHECK lines of the prediction block below and answered in
slots/R15.slots.

File order: the test-out T1 (a prefix search), then H1 (a search anywhere in
the string), each followed by its use-site checks, commented under
`Uncomment as you go:`.

Done: scripts/vcheck --gate dafny/R/R15_VerifierLoop/std exits 0 with zero holes,
scripts/vaudit dafny/R/R15_VerifierLoop/std reports no finding,
scripts/specfreeze --check R15 reports none, and
scripts/firsttry.sh R15 --report --strict exits 0.
*/

// =============================================================================
// Prediction block: do not run the subjects until these slots are recorded
// =============================================================================

// item: R15.P1dv verdict
/** weak-d and weak-v state one candidate statement from the chapter's
    review (§4) and return false for every input. Predict both verdict and
    stage pairs. Answer form: D:<verdict>,<stage> V:<verdict>,<stage>. */
// SLOT: CHECK P1dv
// item: R15.P2dv verdict
/** anchor-d and anchor-v state the faithful search and answer it with A2's
    whole-string matcher. Predict both verdict and stage pairs.
    Answer form: D:<verdict>,<stage> V:<verdict>,<stage>. */
// SLOT: CHECK P2dv

module R15_VerifierLoop {
  // specfreeze: frozen-imports
  import opened RG_A1_Re
  import B = RG_A1b_Facts
  import A2 = RG_A2_Deriv

  // ===========================================================================
  // Test-out (closed book)
  // ===========================================================================

  // item: R15.T1d
  // uses: invariant
  // pair: R15.T1v
  /** **T1.** Closed book: does some prefix of `s` match `r`? One derivative per
      character, as A2's `DerivMatch` does, but the answer may come early. What
      does the loop's regex `d` promise about the slices `s[j..k]` that are still
      ahead, and what does the loop know about the prefixes it has passed? */
  method PrefixMatchR15(r: Re, s: seq<char>) returns (b: bool)
    ensures b == exists j | 0 <= j <= |s| :: Matches(r, s[..j])
  {
    assume false;
  }
  // Hint(1): a loop over `j` with two invariants: one relating `d` on the slices ahead to `r` on the prefixes, one ruling out the prefixes already passed.
  // Hint(2): A1b's `NullableCorrect` reads `Nullable(d)` as a match of the empty slice; A2's `DerivCorrect(d, s[j], s[j + 1..k])` moves the first invariant one character on.
  // Uncomment as you go:
  // method PrefixCheckR15()
  // {
  //   var b := PrefixMatchR15(Chr('a'), ['a', 'b']);
  //   assert ['a', 'b'][..1] == ['a'];
  //   assert b;
  //   var c := PrefixMatchR15(Empty, ['a']);
  //   assert !c;
  // }

  // ===========================================================================
  // The search anywhere
  // ===========================================================================

  // item: R15.H1d
  // uses: invariant
  // pair: R15.H1v
  /** **H1.** Does some slice `s[i..j]` match `r` (an unanchored search)? The
      chapter's rungs 1 to 3 ran, checked and tested this matcher; here you prove
      it. The empty slices count. What must the outer loop know about the start
      positions it has passed, and what does the inner loop's regex promise about
      the slices that begin at `i`? */
  method ContainsMatchR15(r: Re, s: seq<char>) returns (b: bool)
    ensures b == exists i, j | 0 <= i <= j <= |s| :: Matches(r, s[i..j])
  {
    assume false;
  }
  // Hint(1): nested loops: restart the derivative at every start `i`; the inner loop is T1's loop on the slices that begin at `i`.
  // Hint(2): the outer invariant rules out every slice that starts before `i`; T1 is in this file and may be called on `s[i..]`, if you prefer one loop and a slice fact `s[i..][..k] == s[i..i + k]`.
  // Uncomment as you go:
  // method ContainsCheckR15()
  // {
  //   var b := ContainsMatchR15(Chr('a'), ['b', 'a']);
  //   assert ['b', 'a'][1..2] == ['a'];
  //   assert b;
  //   var c := ContainsMatchR15(Empty, ['a']);
  //   assert !c;
  //   var empty: seq<char> := [];
  //   var e := ContainsMatchR15(Eps, empty);
  //   assert empty[0..0] == [];
  //   assert e;
  // }
}
