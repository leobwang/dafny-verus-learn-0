// Topic (e) course-local task cl-d1-sum-append (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `SumAppend` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
module Q31dev_d1_sum_append {
  function Sum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + Sum(s[1..])
  }

  // The sum of a concatenation is the sum of its parts.
  lemma {:induction false} SumAppend(a: seq<nat>, b: seq<nat>)
    ensures Sum(a + b) == Sum(a) + Sum(b)
    decreases |a|
  {
  }
}
