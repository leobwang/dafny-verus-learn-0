/*!
# Q08 — Internals II: two refinements of QG_L4_Spec (Reference Solution)

Hole-free reference for `dafny/Q/Q08_InternalsII/std/Q08_Canon.dfy`
(author-only; never learner-visible). Same modules, imports, names, statements,
item markers and order as the exercise file. Every refined lemma that is a
hole there is proved here; the helper lemmas each proof adds are marked
`reference-only` (the learner may add helpers of their own to the refining
module). Silent under `scripts/vcheck --ref`.
*/

// A refinement whose well-formedness is canonical form, and whose addition
// normalizes L4's sum.
module {:disableNonlinearArithmetic} Q08_Canon refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L2.Normalize(L4.Add(a, b)) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }

  // item: Q08.H1d S6
  // uses: refines
  /** **H1d.** The inherited statement of `AddCorrect`, for this refinement:
          requires Wf(a) && Wf(b)
          ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)

      Reference: L4's `AddCorrect` gives the value of the raw sum (and its
      validity, from canonical, hence valid, arguments); L3's
      `NormalizeToNat` keeps that value through `Normalize`, and L3's
      `NormalizeCanonical` makes the normalized sum canonical, which is this
      refinement's `Wf`. */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
    L3.NormalizeToNat(L4.Add(a, b));
    L3.NormalizeCanonical(L4.Add(a, b));
  }

  // item: Q08.H2d S6
  // uses: refines
  /** **H2d.** The inherited statement of `FromNatCorrect`, for this
      refinement:
          ensures Wf(FromNat(n)) && Val(FromNat(n)) == n

      Reference: L3's `FromNatCorrect` gives validity and the value; what is
      left is canonical form, which needs an induction on `n / BASE`. A
      refined lemma inherits its statement and cannot carry a termination
      measure of its own, so the induction goes into a helper lemma of this
      module, `FromNatCanonical`, and the refined lemma calls it. The helper's
      step: for `n > 0`, `FromNat(n)` is `[n % BASE] + FromNat(n / BASE)`;
      the tail is canonical by the recursive call, and its value (L3 again) is
      positive exactly when it is non-empty, so the top limb is not 0. */
  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    FromNatCanonical(n);
  }

  // reference-only: a helper lemma the learner may add to this module
  lemma FromNatCanonical(n: nat)
    ensures L2.Canonical(L2.FromNat(n))
    decreases n
  {
    L3.FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / L1.BASE);
      L3.FromNatCorrect(n / L1.BASE);
    }
  }
}

// A second refinement: the same well-formedness, and L4's addition itself,
// with no normalization.
module {:disableNonlinearArithmetic} Q08_CanonRaw refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.Normalize(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { L4.Add(a, b) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L3.NormalizeToNat(L2.FromNat(n));
    L3.NormalizeCanonical(L2.FromNat(n));
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }

  // item: Q08.H7d S6
  // uses: refines
  /** **H7d.** The inherited statement of `AddCorrect`, for this refinement:
          requires Wf(a) && Wf(b)
          ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)

      Reference: L4's `AddCorrect` gives the value; what is left is that
      schoolbook addition of canonical numerals is canonical with no
      normalization. That needs an induction over `AddC`, the carry-passing
      addition `Add` is built on, at every carry `c <= 1`: the helper
      `AddCCanonical`. Its step reveals `AddC` (it is opaque), states the
      one-step unfolding `AddC(a, b, c) == [d] + r` (the low limb, then the
      sum of the tails with the next carry), and takes L4's `AddCCorrect` at
      the current level and at the tails: the tails of canonical numerals are
      canonical, and when they are not both empty, their sum is canonical by the
      recursive call, so its top limb is the result's; when both are empty,
      the result is the one-limb or two-limb sum of the heads and the carry,
      whose top limb is not 0 because the value of a canonical numeral with
      limbs is positive. */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
    AddCCanonical(a, b, 0);
  }

  // reference-only: a helper lemma the learner may add to this module
  lemma {:induction false} AddCCanonical(a: seq<nat>, b: seq<nat>, c: nat)
    requires L2.Canonical(a) && L2.Canonical(b) && c <= 1
    ensures L2.Canonical(L4.AddC(a, b, c))
    decreases |a| + |b|
  {
    reveal L4.AddC();  // did: unfolds the opaque AddC, for this proof only
    L4.AddCCorrect(a, b, c);
    if |a| != 0 || |b| != 0 {
      var t := L1.Head(a) + L1.Head(b) + c;
      var c' := if t < L1.BASE then 0 else 1;
      var d := if t < L1.BASE then t else t - L1.BASE;
      var r := L4.AddC(L1.Tail(a), L1.Tail(b), c');
      assert L4.AddC(a, b, c) == [d] + r;
      L2.ValidTail(a);
      L2.ValidTail(b);
      L4.AddCCorrect(L1.Tail(a), L1.Tail(b), c');
      if |L1.Tail(a)| != 0 || |L1.Tail(b)| != 0 {
        assert L2.Canonical(L1.Tail(a)) && L2.Canonical(L1.Tail(b));
        AddCCanonical(L1.Tail(a), L1.Tail(b), c');
      }
    }
  }
}
