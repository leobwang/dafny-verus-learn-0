/*!
# Q09 — Internals III: the trigger test-out (Reference Solution)

Hole-free reference for `dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy`
(author-only; never learner-visible). Same module, options, imports, names,
statements, item markers and order as the exercise file; T1's hole is
filled. The file is silent: `scripts/vcheck --ref` on its unit prints only
the summary line.

Why this file has nonlinear arithmetic off (the author notes §0.3; the
empty-body gate's maxauto run agrees, `lever-needed`): with it on, both P2's
quoted attempt and T1's empty body verify, so neither would test a
trigger. With it off, the attempt's trigger `Pow(k)` makes each
instance create the next term `Pow(k + 1)`, which matches again, and the
loop spends the budget (P2: inconclusive under every seed).
*/
module {:disableNonlinearArithmetic} Q09_Triggers {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q09.T1d S11
  // uses: trigger-rewrite
  // pair: Q09.T1v
  // form: trigger, stable
  // cfree: { assert Pow(m + 1) == BASE * Pow(m); if m + 1 < n { PowGrowsByBase(m + 1, n); PowAdd(m + 1, 0); } }
  /** **T1.** (test-out) Each power of BASE is at least BASE times every
      smaller one. Reference: the quantified step `Pow(k) * BASE <=
      Pow(k + 1)` with the trigger on the successor term `Pow(k + 1)`: no
      instance creates a new term of that shape, so the step fires only at
      the terms the proof holds (the recursive call's `Pow(m + 1)`), and the
      recursion closes the gap, with `PowAdd(m + 1, 0)` for the last
      comparison (the author notes' A.10 reference, unchanged). Stable
      under seeds 1-3 and both bundled solvers; no resource attribute. The
      `cfree:` line above is a proof with no quantifier at all: it verifies,
      and the `trigger` form stops it (a presence check; the rubric checks
      that the quantified step carries the proof). */
  lemma PowGrowsByBase(m: nat, n: nat)
    requires m < n
    ensures Pow(m) * BASE <= Pow(n)
    decreases n - m
  {
    forall k: nat {:trigger Pow(k + 1)} ensures Pow(k) * BASE <= Pow(k + 1) {
      assert Pow(k + 1) == BASE * Pow(k);
    }
    if m + 1 < n {
      PowGrowsByBase(m + 1, n);
      PowAdd(m + 1, 0);
    }
  }
}
