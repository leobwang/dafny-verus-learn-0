/*!
# Q12 — Lab 1: the hand part, Dafny (Reference Solution)

Hole-free reference for `dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file; every hole is
filled. The file is silent: `scripts/vcheck --ref` on its unit prints only
the summary line.

H4, H6 and H7 need the unit's manual lemma induction: under maximal
automation H4's and H7's empty bodies verify (a hole plus a lever, the
empty-body gate's `lever-needed`), so as lab tasks they rely on the lab
gate's lever check (QPLAN §30 Q63). H6 (`CmpTrailingZero`, which replaces
the plan's `CmpSelf`: Q09's learner-visible specimen P9d proves that
statement's recursion) fails under maximal automation too. H5 fails under
both.
*/
module Q12_Lab1Hand {
  // specfreeze: frozen-imports
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q12.H4d S12
  // uses: lemma-recursion
  // pair: Q12.H4v
  /** **H4.** The value is monotone in each limb: a limb sequence that is
      limb by limb at most another of the same length has at most its
      value. */
  lemma ToNatMono(a: seq<nat>, b: seq<nat>)
    requires |a| == |b| && forall i | 0 <= i < |a| :: a[i] <= b[i]
    ensures ToNat(a) <= ToNat(b)
    decreases |a|
  {
    if |a| > 0 {
      ToNatMono(a[1..], b[1..]);
    }
  }

  // item: Q12.H5d S12
  // uses: lemma-recursion
  /** **H5.** Multiplying by the limb 0 (layer L4's `MulLimb`) keeps the
      length and gives a zero in every limb. */
  lemma MulLimbZeroLimbs(s: seq<nat>)
    ensures |MulLimb(s, 0)| == |s| && forall i | 0 <= i < |s| :: MulLimb(s, 0)[i] == 0
    decreases |s|
  {
    if |s| > 0 {
      MulLimbZeroLimbs(s[1..]);
      assert s[0] * 0 == 0;
    }
  }

  // item: Q12.H6d S12
  // uses: lemma-recursion
  /** **H6.** `Cmp` (layer L3) reads a missing limb as 0: a sequence compares
      equal to itself with one zero limb appended at the most significant
      end. No precondition. */
  lemma CmpTrailingZero(a: seq<nat>)
    ensures Cmp(a, a + [0]) == 0
    decreases |a|
  {
    if |a| > 0 {
      assert Tail(a + [0]) == Tail(a) + [0];
      CmpTrailingZero(Tail(a));
    }
  }

  // item: Q12.H7d S12
  // uses: lemma-recursion
  /** **H7.** Normalizing never lengthens a sequence. */
  lemma NormalizeShorter(s: seq<nat>)
    ensures |Normalize(s)| <= |s|
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeShorter(s[..|s| - 1]);
    }
  }
}

/*
HAND (learner-owned; the lab report reads it, no script does). One row per
item, written when its 12 minutes are up: verified within the time (yes or
no) and the minutes it took.
  H4d ToNatMono: (reference; no timing)
  H5d MulLimbZeroLimbs: (reference; no timing)
  H6d CmpTrailingZero: (reference; no timing)
  H7d NormalizeShorter: (reference; no timing)
*/
