/*!
# Q14 — Practice II-B (Reference Solution)

Hole-free reference for `dafny/Q/Q14_PracticeIIB/std/Q14_PracticeIIB.dfy`
(author-only; never learner-visible). Same modules, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and the verdict switch is enabled; the verdict
answer is in `Solutions/slots/Q14.slots`, its hash in `expected/Q14.pins`.
Each item uses at most the one lemma of its own the tier allows, in its
`HELPERS` area. The `// cfree:` line is a shortcut answer the author measured;
it must fail (Solutions/plans/Q14-code-notes.md).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. `Q14_Cached` turns nonlinear arithmetic off and comes last in
the file, as in the exercise file.
*/
module Q14_Term {

  // ===========================================================================
  // The prediction block.
  // ===========================================================================

  // item: Q14.P1dv S7 verdict
  /** **P1.** Warm-up: a recursion that swaps its arguments. */
  // CHECK P1dv

  // ===========================================================================
  // Termination
  // ===========================================================================

  // Given (not an item): the two sequences' elements in turn, from `a`.
  function Interleave(a: seq<nat>, b: seq<nat>): seq<nat>
    decreases |a| + |b|
  {
    if |a| == 0 then b else [a[0]] + Interleave(b, a[1..])
  }

  // HELPERS (Q14.H3d): at most one lemma of your own, here.
  // reference-only: the learner's own helper (the tier allows one)
  lemma InterleaveCount(a: seq<nat>, b: seq<nat>)
    ensures |Interleave(a, b)| == |a| + |b| && multiset(Interleave(a, b)) == multiset(a) + multiset(b)
    decreases |a| + |b|
  {
    if |a| > 0 {
      var t := a[1..];
      InterleaveCount(b, t);
      assert a == [a[0]] + t;
      assert multiset(a) == multiset([a[0]]) + multiset(t);
    }
  }

  // item: Q14.H3d S7
  // uses: decreases, lemma-recursion
  // pair: Q14.H3v
  /** **H3.** Reference: one induction on `|a| + |b|` (the default measure,
      the parameters in order, does not decrease at the swapped call). The
      recursive call on `(b, a[1..])` with the same `x` and `y` gives the
      appended laws for the swapped pair: an equal-length pair needs the
      other case of the swapped pair, and the other way round; the rest is
      the slices of the appended sequences. The helper proves the length and
      multiset conjuncts by the same recursion, apart: in one lemma the
      multiset axioms meet the appended sequences, and the proof costs up to
      3.9 M resource units (78% of the limit; Solutions/plans/Q14-code-notes.md). */
  lemma InterleaveSpec(a: seq<nat>, b: seq<nat>, x: nat, y: nat)
    ensures |Interleave(a, b)| == |a| + |b| &&
            multiset(Interleave(a, b)) == multiset(a) + multiset(b) &&
            (|a| == |b| ==> Interleave(a + [x], b + [y]) == Interleave(a, b) + [x, y]) &&
            (|a| == |b| + 1 ==> Interleave(a + [y], b + [x]) == Interleave(a, b) + [x, y])
    decreases |a| + |b|
  {
    InterleaveCount(a, b);
    if |a| == 0 {
      assert [] + [x] == [x] && [] + [y] == [y];
    } else {
      var t := a[1..];
      InterleaveSpec(b, t, x, y);
      assert (a + [x])[1..] == t + [x];
      assert (a + [y])[1..] == t + [y];
    }
  }

  method InterleaveSpecCheck(a: seq<nat>, b: seq<nat>)
    requires |a| == |b|
  {
    InterleaveSpec(a, b, 3, 4);
    assert |Interleave(a, b)| == 2 * |a|;
    assert Interleave(a + [3], b + [4])[2 * |a| + 1] == 4;
  }
}

// =============================================================================
// The refinement. Nonlinear arithmetic is off in this module (the attribute
// on its `module` line), which comes last in the file.
// =============================================================================
module {:disableNonlinearArithmetic} Q14_Cached refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat
  import L5 = QG_L5_BigNat
  import L6 = QG_L6_BigNat
  import Power = Std.Arithmetic.Power

  // Given (not items): a number that caches its length.
  datatype Num = Num(limbs: seq<nat>, len: nat)
  type BigNat = Num

  ghost function Val(x: BigNat): nat { L1.ToNat(x.limbs) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x.limbs) && x.len == |x.limbs| }

  function Zero(): BigNat { Num([], 0) }
  function FromNat(n: nat): BigNat { var s := L2.FromNat(n); Num(s, |s|) }
  function Add(a: BigNat, b: BigNat): BigNat { var s := L2.Normalize(L4.Add(a.limbs, b.limbs)); Num(s, |s|) }
  function Cmp(a: BigNat, b: BigNat): int
  {
    if a.len < b.len then -1 else if a.len > b.len then 1 else L3.Cmp(a.limbs, b.limbs)
  }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L6.FromNatCanonical(n);
  }

  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L6.NormalizeAddCorrect(a.limbs, b.limbs);
  }

  // HELPERS (Q14.H1d): at most one lemma of your own, here.
  // reference-only: the learner's own helper (the tier allows one)
  lemma Shorter(x: seq<nat>, y: seq<nat>)
    requires L2.Canonical(x) && L2.Canonical(y) && |x| < |y|
    ensures L1.ToNat(x) < L1.ToNat(y)
  {
    L2.ToNatBound(x);
    L5.CanonicalLower(y);
    L3.PowIsStdPow(|x|);
    L3.PowIsStdPow(|y| - 1);
    Power.LemmaPowIncreases(L1.BASE, |x|, |y| - 1);
  }

  // item: Q14.H1d S6
  // uses: refines
  // cfree: { L4.CmpCorrect(a.limbs, b.limbs); }
  /** **H1.** Reference: split on the cached lengths. Equal lengths are L4's
      comparison; a shorter canonical number is the smaller (the helper: L2's
      upper bound, L5's lower bound, and `Std.Arithmetic.Power`'s
      monotonicity through L3's bridge). The `cfree:` line skips the
      lengths: L4's lemma speaks of L3's `Cmp`, not of this one. */
  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    if a.len < b.len {
      Shorter(a.limbs, b.limbs);
    } else if a.len > b.len {
      Shorter(b.limbs, a.limbs);
    } else {
      L4.CmpCorrect(a.limbs, b.limbs);
    }
  }

  method CmpCorrectCheck(x: BigNat, y: BigNat)
    requires Wf(x) && Wf(y) && x.len < y.len
  {
    CmpCorrect(x, y);
    assert Val(x) < Val(y);
  }
}
