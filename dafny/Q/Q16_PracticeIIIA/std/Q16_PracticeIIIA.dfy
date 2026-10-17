/*!
# Q16 — Practice III-A (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L7
(`QG_L7_BigNat`), and Dafny's `Std.Arithmetic.Mul`, all opened; nothing else:
no earlier exercise file. The layers are frozen and complete; read them, never
edit them. Nonlinear arithmetic is off in this module (the attribute on its
`module` line), the only module in the file: every product step is a named
lemma.

How to work this file (the hard practice tier):
1. The blueprint first: problem B1 of paper/Q16_problems.tex, for H1, H2
   and H3, graded by `/grade-paper Q16` (at least 3 on every dimension)
   before you write any proof here.
2. Each problem ships its plain statement and nothing else, and the plain
   statement is known not to go through as it stands: the statements you
   generalize, the lemmas you invent (two to four per problem) and their
   order are yours. They go in the `HELPERS` area below, statement and proof.
3. Done = `scripts/vcheck --gate dafny/Q/Q16_PracticeIIIA/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q16_PracticeIIIA/std`
   reports no finding, AND `scripts/firsttry.sh Q16 --report --strict` exits
   0; then `/review-code Q16` and `/grade-paper Q16 --post`.
4. Stuck for 20 minutes? /tutor Q16.

This file ships with exactly 2 holes (H1 and H3's Dafny half), each counted
by `scripts/vcheck`. Q16 as a whole ships 4 holes (2 here and 2 in the Verus
crate verus/q/q16_practice_iiia/src/lib.rs); no prediction and no exit file:
the module's exit is its verifier part with the two reviews.

Item kinds: H one-hole item. Each item's commented checks sit under
`Uncomment as you go:`; uncomment them once the item is done.
*/
module {:disableNonlinearArithmetic} Q16_PracticeIIIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat
  import opened QG_L7_BigNat
  import opened Std.Arithmetic.Mul

  // ===========================================================================
  // HELPERS: the lemmas of your blueprint, here (statements and proofs).
  // ===========================================================================

  // ===========================================================================
  // H1: full multiplication over the schoolbook definition
  // ===========================================================================

  // item: Q16.H1d S4
  // uses: lemma-recursion, library-call
  /** **H1.** The schoolbook product of layer L7 is a valid sequence whose
      value is the product of the two values. This is the plain statement,
      and an induction on it alone does not go through. Generalize first: what
      does the recursion of `MulAcc` carry from one row to the next, and what
      must a statement about it leave free? Your blueprint (B1) names the
      generalized statement and the lemmas under it before you write them in
      the `HELPERS` area above. Nonlinear arithmetic is off: every product
      step is a named lemma of `Std.Arithmetic.Mul` (opened). */
  lemma MulCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Times(a, b)) && ToNat(Times(a, b)) == ToNat(a) * ToNat(b)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.

  method MulCorrectCheck()
  {
    // Uncomment as you go:
    // MulCorrect([2], [3]);
    // assert ToNat(Times([2], [3])) == 6;
  }

  // ===========================================================================
  // H3, the Dafny half (the Verus half is mul, in the crate)
  // ===========================================================================

  // item: Q16.H3d S4
  // uses: invariant
  // pair: Q16.H3v
  // form: loop-dir:up
  /** **H3 (the Dafny half).** A compiled loop that computes layer L7's
      schoolbook product exactly: the `ensures` pins the very sequence `Times`
      defines, not only its value. `Times` and `MulAcc` are ghost: the
      `ensures` and your proof may name them, your code cannot call them.
      Write a loop over the limbs of `b`, from the low limb up; your proof may
      call H1's lemma. What must the invariant say for its last instance to
      give the `ensures`? */
  method MulLoop(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Times(a, b) && Valid(r) && ToNat(r) == ToNat(a) * ToNat(b)
  {
    assume false;  // HOLE: replace this line with the loop and its proof
  }

  method MulLoopCheck()
  {
    // Uncomment as you go:
    // var r := MulLoop([2], [3]);
    // assert ToNat(r) == 6;
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 10 · blueprint 30 · full multiplication (D) 45 · division by one
  limb (V) 50 · in-place schoolbook (V + D) 55 · /review-code 15 · paper 15 ·
  ledger 5 · total 225
Then run `scripts/firsttry.sh Q16 --record`.
*/
