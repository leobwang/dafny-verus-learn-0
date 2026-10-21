// Topic (e) course-local task cl-d5-take-sum (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `TakeAppendSum` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d5_take_sum {
  function Acc(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else Acc(s[..|s| - 1]) + s[|s| - 1]
  }

  // A prefix's total plus the next element is the longer prefix's total.
  lemma {:induction false} TakeAppendSum(s: seq<nat>, k: nat)
    requires k < |s|
    ensures Acc(s[..k + 1]) == Acc(s[..k]) + s[k]
  {
    assert s[..k + 1][..k] == s[..k];
  }
}
