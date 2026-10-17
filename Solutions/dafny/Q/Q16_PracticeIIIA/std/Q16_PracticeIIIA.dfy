/*!
# Q16 — Practice III-A (Reference Solution)

Hole-free reference for `dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled and every check is live. The lemmas the learner invents (the
blueprint's) are in the file's `HELPERS` area, each marked reference-only.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Nonlinear arithmetic is off in the module (the attribute on its
`module` line), the only module in the file.
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

  // reference-only: the learner's generalization of H1 (the accumulator and the shift free)
  lemma MulAccCorrect(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat)
    requires Valid(a) && Valid(b) && Valid(acc)
    ensures Valid(MulAcc(a, b, acc, k))
    ensures ToNat(MulAcc(a, b, acc, k)) == ToNat(acc) + Pow(k) * (ToNat(a) * ToNat(b))
    decreases |b|
  {
    if |b| == 0 {
      MulZero(ToNat(a), ToNat(b));
      MulZero(Pow(k), ToNat(a) * ToNat(b));
    } else {
      ValidTail(b);
      MulLimbCorrect(a, b[0]);
      ShiftCorrect(MulLimb(a, b[0]), k);
      var row := Shift(MulLimb(a, b[0]), k);
      AddCorrect(acc, row);
      MulAccCorrect(a, b[1..], Add(acc, row), k + 1);
      var A := ToNat(a);
      var B1 := ToNat(b[1..]);
      var P := Pow(k);
      MulNonneg(A, B1);
      MulNonneg(A, b[0]);
      ToNatHeadTail(b);
      assert ToNat(b) == b[0] + BASE * B1;
      assert Pow(k + 1) == BASE * P;
      LemmaMulIsDistributive(A, b[0], BASE * B1);
      LemmaMulIsAssociative(A, BASE, B1);
      LemmaMulIsCommutative(A, BASE);
      LemmaMulIsAssociative(BASE, A, B1);
      LemmaMulIsAssociative(P, BASE, A * B1);
      LemmaMulIsCommutative(P, BASE);
      LemmaMulIsAssociative(BASE, P, A * B1);
      LemmaMulIsDistributive(P, A * b[0], BASE * (A * B1));
    }
  }

  // reference-only: the learner's shift lemma (the value of a shifted row)
  lemma ShiftCorrect(s: seq<nat>, k: nat)
    requires Valid(s)
    ensures Valid(Shift(s, k)) && ToNat(Shift(s, k)) == Pow(k) * ToNat(s)
    decreases k
  {
    if k == 0 {
      assert Shift(s, 0) == s;
      LemmaMulBasics(ToNat(s));
    } else {
      ShiftCorrect(s, k - 1);
      assert Shift(s, k) == [0] + Shift(s, k - 1);
      ToNatCons(0, Shift(s, k - 1));
      ValidCons(0, Shift(s, k - 1));
      LemmaMulIsAssociative(BASE, Pow(k - 1), ToNat(s));
    }
  }

  // reference-only: support of H3d's `cfree:` line (a compiled recursion in place of the loop)
  function MulRec(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat): seq<nat>
    decreases |b|
  {
    if |b| == 0 then acc else MulRec(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)), k + 1)
  }

  // reference-only: support of H3d's `cfree:` line
  lemma MulRecIsMulAcc(a: seq<nat>, b: seq<nat>, acc: seq<nat>, k: nat)
    ensures MulRec(a, b, acc, k) == MulAcc(a, b, acc, k)
    decreases |b|
  {
    if |b| > 0 {
      MulRecIsMulAcc(a, b[1..], Add(acc, Shift(MulLimb(a, b[0]), k)), k + 1);
    }
  }

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
  {
    MulAccCorrect(a, b, [], 0);
    LemmaMulBasics(ToNat(a) * ToNat(b));
    LemmaMulIsAssociative(1, ToNat(a), ToNat(b));
  }

  method MulCorrectCheck()
  {
    MulCorrect([2], [3]);
    assert ToNat(Times([2], [3])) == 6;
  }

  // ===========================================================================
  // H3, the Dafny half (the Verus half is mul, in the crate)
  // ===========================================================================

  // item: Q16.H3d S4
  // uses: invariant
  // pair: Q16.H3v
  // form: loop-dir:up
  // cfree: { r := MulRec(a, b, [], 0); MulRecIsMulAcc(a, b, [], 0); MulCorrect(a, b); }
  // cfree: { r := MulRec(a, b, [], 0); MulRecIsMulAcc(a, b, [], 0); MulCorrect(a, b); var j := 0; while j < 1 { j := j + 1; } }
  // cfree: { r := []; var j := 0; while j < 1 invariant 0 <= j <= 1 && (j == 1 ==> r == MulRec(a, b, [], 0)) { r := MulRec(a, b, [], 0); j := j + 1; } MulRecIsMulAcc(a, b, [], 0); MulCorrect(a, b); }
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
    r := [];
    var k := 0;
    assert b[0..] == b;
    while k < |b|
      invariant 0 <= k <= |b|
      invariant MulAcc(a, b[k..], r, k) == Times(a, b)
      decreases |b| - k
    {
      assert b[k..][1..] == b[k + 1..];
      r := Add(r, Shift(MulLimb(a, b[k]), k));
      k := k + 1;
    }
    MulCorrect(a, b);
  }

  method MulLoopCheck()
  {
    var r := MulLoop([2], [3]);
    assert ToNat(r) == 6;
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
