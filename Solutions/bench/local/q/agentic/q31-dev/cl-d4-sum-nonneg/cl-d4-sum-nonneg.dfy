// Topic (e) course-local task cl-d4-sum-nonneg (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `SumNonNeg` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d4_sum_nonneg {
  function Total(s: seq<int>): int
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + Total(s[1..])
  }

  // A sequence of non-negative numbers has a non-negative total.
  lemma {:induction false} SumNonNeg(s: seq<int>)
    requires forall i | 0 <= i < |s| :: s[i] >= 0
    ensures Total(s) >= 0
    decreases |s|
  {
    if |s| > 0 {
      assert forall i | 0 <= i < |s[1..]| :: s[1..][i] == s[i + 1];
      SumNonNeg(s[1..]);
    }
  }
}
