/*!
# Q13 — Practice II-A (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L6
(`QG_L6_BigNat`), in the module `Q13_PracticeIIA`; layers L1, L2, L4 and L5
and Dafny's `Std.Arithmetic.Mul` in the module `Q13_Library`, all opened;
nothing else: no earlier exercise file. The layers are frozen and complete;
read them, never edit them. Nonlinear arithmetic is off in `Q13_Library`
(the attribute on its `module` line), which comes last in this file; it is on
in `Q13_PracticeIIA`.

How to work this file (the intermediate practice tier):
1. Predictions first: fill the slot of the prediction block below (its answer
   goes in slots/Q13.slots), then record the first try with
   `scripts/firsttry.sh Q13 --check`, before you run anything it is about.
2. Each item ships its statement and nothing else: no skeleton. You choose
   the induction, the loop and the shape of the proof. Each item allows at
   most one lemma of your own: write it in the item's `HELPERS` area, above
   the item, with a statement of your own and its proof.
3. Done = `scripts/vcheck --gate dafny/Q/Q13_PracticeIIA/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q13_PracticeIIA/std`
   reports no finding, AND `scripts/firsttry.sh Q13 --report --strict` exits
   0.
4. Stuck for 20 minutes? /tutor Q13.

This file ships with exactly 3 holes (H2, H4 and H5), each counted by
`scripts/vcheck`. Q13 as a whole ships 6 holes (3 here and 3 in the Verus
crate verus/q/q13_practice_iia/src/lib.rs); 1 prediction (a verdict, in the
block below); and 1 exit item (the Verus exit file ships 1 hole; the Dafny
exit file ships none). Commit the prediction BEFORE you run anything it is
about, open later files, or read CI, the registry or the plan: their checks
and headers give some predictions away.

Item kinds: P prediction (a slot) · H one-hole item · X exit item (the exit
files). Slots: a verdict switch `// SLOT: CHECK <item>` here takes its answer
in slots/Q13.slots (`P1dv = ???` → `P1dv = "<answer>"`). Fill the slot,
record the first try, and only then enable it: `// SLOT: CHECK P1dv` becomes
`// CHECK P1dv`.

Exit (closed book, timed): verus/q/q13_practice_iia/src/exit.rs, scored once
by `scripts/firsttry.sh Q13 --exit` (threshold: the 1 item must pass).
*/
module Q13_PracticeIIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ===========================================================================
  // The prediction block. Commit the prediction of this module before you
  // read past this block, and record the first try:
  //     scripts/firsttry.sh Q13 --check
  // The verdict answer goes in slots/Q13.slots. The Verus crate has no
  // prediction block of its own.
  // ===========================================================================

  // item: Q13.P1dv S2 verdict
  /** **P1.** Warm-up: two specifications of one method, and a client of each.
      Dafny, in a module of this unit's options, with layers L1 and L2 opened:

          method TopA(s: seq<nat>) returns (t: nat)
            requires Canonical(s) && |s| > 0
            ensures t < BASE
          { t := s[|s| - 1]; }

          method TopB(s: seq<nat>) returns (t: nat)
            requires Canonical(s) && |s| > 0
            ensures t != 0 ==> t == s[|s| - 1]
          { t := s[|s| - 1]; }

          method ClientA(s: seq<nat>) requires Canonical(s) && |s| > 0
          { var t := TopA(s); assert t == s[|s| - 1]; }

          method ClientB(s: seq<nat>) requires Canonical(s) && |s| > 0
          { var t := TopB(s); assert t == s[|s| - 1]; }

      Verus, in a crate of its own over layer L1's `BigNat`: `top_a` and
      `top_b` return `a.limbs[a.limbs.len() - 1]` under `requires a.wf(),
      a@.len() > 0`, with `ensures t < BASE` and `ensures t != 0 ==> t ==
      a@[a@.len() - 1]`; `client_a` and `client_b` call them and
      `assert(t == a@[a@.len() - 1])`.

      Which clients verify? Answer form: `D:<labels> V:<labels>`, the labels
      `a` and `b` of the clients that verify, in label order (`D:a b`), or
      `none`. */
  // SLOT: CHECK P1dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // HELPERS (Q13.H2d): at most one lemma of your own, here.

  // item: Q13.H2d S4
  // uses: lemma-recursion
  /** **H2.** Normalizing twice changes nothing, and normalizing a
      concatenation keeps the low part whole unless the high part normalizes
      away. No skeleton: the induction is yours. Which of the two
      postconditions does the other one need, and on which argument does the
      recursion shrink? */
  lemma NormalizeConcat(a: seq<nat>, b: seq<nat>)
    ensures Normalize(Normalize(a + b)) == Normalize(a + b) &&
            Normalize(a + b) == (if Normalize(b) == [] then Normalize(a) else a + Normalize(b))
    decreases |b|
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint: `Normalize` strips the top limb only when it is zero; which limb
  //    of `a + b` is the top one when `b` is not empty?

  method NormalizeConcatCheck()
  {
    // Uncomment as you go:
    // NormalizeConcat([3], [0, 0]);
    // assert Normalize([3] + [0, 0]) == Normalize([3]);
  }
}

// =============================================================================
// The library goals. Nonlinear arithmetic is off in this module (the
// attribute on its `module` line), which comes last in the file: a product
// step comes from a named lemma of `Std.Arithmetic.Mul` (opened).
// =============================================================================
module {:disableNonlinearArithmetic} Q13_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.Mul

  // HELPERS (Q13.H4d): at most one lemma of your own, here.

  // item: Q13.H4d S5
  // uses: library-call, calc
  // pair: Q13.H4v
  /** **H4.** The value of `n` equal non-zero limbs. `seq(n, _ => d)` is the
      sequence of `n` copies of `d`. With nonlinear arithmetic off, every
      product step is a library lemma: which steps need one, and in which
      order do they turn `ToNat` of the sequence into the right-hand side? */
  lemma RepeatValue(d: nat, n: nat)
    requires 0 < d < BASE
    ensures ToNat(seq(n, _ => d)) * (BASE - 1) == d * (Pow(n) - 1)
    decreases n
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint: `BASE` is a named constant here, so `BASE * x` is a product the
  //    solver does not expand: distributivity and associativity are calls.

  // HELPERS (Q13.H5d): at most one lemma of your own, here.

  // item: Q13.H5d S4
  // uses: invariant, decreases, library-call
  // form: loop-dir:up, no-call:ToNat
  /** **H5.** The value of a limb sequence, by a loop from the LOW limb: keep
      the place value of the next limb in a variable and add one product per
      step. The loop computes the value: `ToNat` may appear in your
      invariants, assertions and lemma calls, never in compiled code. No
      skeleton: the loop, its invariant and every product step are yours
      (nonlinear arithmetic is off). What does the loop know about the limbs
      it has not read yet? */
  method ValueLoop(s: seq<nat>) returns (v: nat)
    ensures v == ToNat(s)
  {
    assume false;  // HOLE: replace this line with the loop and its proof
  }
  // Hint: the invariant relates `v`, the place value and `ToNat` of the
  //    suffix that is still to come.

  method ValueLoopCheck()
  {
    // Uncomment as you go:
    // var v := ValueLoop([2, 1]);
    // assert v == 2 + BASE;
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · warm-up 5 · sub with borrow (V) 35 · normalize idempotent (D) 30 ·
  prose statement (V) 25 · library goal (pair) 30 · accumulator (D) 20 ·
  exit 20 · paper 15 · ledger 5 · total 200
Then run `scripts/firsttry.sh Q13 --record`.
*/
