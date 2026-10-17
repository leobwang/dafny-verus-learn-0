/*!
# Q15 — Lab 2's prose specifications, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy`
(author-only; never learner-visible). Same module, imports, names, item
markers and order as the exercise file. Each prose task carries the author's
specification (the hidden equivalence check's other side; its sealed copy is
the Lab 2 hidden truth), the clients' checks are live, and each witness
method holds one call.
*/
module Q15_Lab2Specs {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q15.H3d S13
  // uses: ensures, witness
  // prose: EvenLimbs
  /** **H3.** Prose task. *Every other limb of a limb sequence, starting from
      the lowest: the limbs at positions 0, 2, 4, … of `s`, in that order, and
      no other limb.* Write `EvenLimbs`'s specification. */
  method EvenLimbs(s: seq<nat>) returns (r: seq<nat>)
    ensures |r| == (|s| + 1) / 2 && forall i | 0 <= i < |r| :: r[i] == s[2 * i]
  {
    if |s| <= 1 {
      r := s;
    } else {
      var t := EvenLimbs(s[2..]);
      r := [s[0]] + t;
    }
  }

  method EvenLimbsUse(s: seq<nat>)
    requires |s| == 5
  {
    var r := EvenLimbs(s);
    assert r == [s[0], s[2], s[4]];
  }

  /** Your non-vacuity witness for `EvenLimbs`: one call whose `requires` hold. */
  method EvenLimbsWitness()
  {
    var r := EvenLimbs([1, 2, 3]);
  }

  // item: Q15.H4d S13
  // uses: ensures, witness
  // prose: TopDiff
  /** **H4.** Prose task. *The index of the highest limb at which two limb
      sequences of one length differ, or -1 when they are equal: above that
      index they agree at every position.* Write `TopDiff`'s specification. */
  method TopDiff(a: seq<nat>, b: seq<nat>) returns (i: int)
    requires |a| == |b|
    ensures -1 <= i < |a| && (i >= 0 ==> a[i] != b[i]) && forall j | i < j < |a| :: a[j] == b[j]
  {
    if |a| == 0 || |b| == 0 {
      i := -1;
    } else if a[|a| - 1] != b[|b| - 1] {
      i := |a| - 1;
    } else {
      i := TopDiff(a[..|a| - 1], b[..|b| - 1]);
    }
  }

  method TopDiffUse(a: seq<nat>, b: seq<nat>)
    requires |a| == 3 && |b| == 3 && a[0] != b[0] && a[1..] == b[1..]
  {
    var i := TopDiff(a, b);
    assert i == 0;
  }

  /** Your non-vacuity witness for `TopDiff`: one call whose `requires` hold. */
  method TopDiffWitness()
  {
    var i := TopDiff([1, 2], [1, 3]);
  }

  // item: Q15.H5d S13
  // uses: ensures, witness
  // prose: SatSub
  /** **H5.** Prose task. *Saturating subtraction of two valid numbers: the
      difference as layer L6's `Sub` gives it when the first is at least the
      second, and the empty sequence (zero) otherwise.* Write `SatSub`'s
      specification. */
  method SatSub(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == if ToNat(b) <= ToNat(a) then Sub(a, b) else []
  {
    if ToNat(a) < ToNat(b) {
      r := [];
    } else {
      r := FromNat(ToNat(a) - ToNat(b));
    }
  }

  method SatSubUse(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && ToNat(a) < ToNat(b)
  {
    var r := SatSub(a, b);
    assert r == [];
    var d := SatSub(b, a);
    assert d == Sub(b, a);
  }

  /** Your non-vacuity witness for `SatSub`: one call whose `requires` hold. */
  method SatSubWitness()
  {
    var r := SatSub([5], [3]);
  }
}
