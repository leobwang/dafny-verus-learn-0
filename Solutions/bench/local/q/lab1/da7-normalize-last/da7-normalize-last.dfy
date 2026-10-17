// Lab 1 local task da7-normalize-last (Q12, course-authored; QPLAN §22.6).
// Write the body of `NormalizeLast` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da7_normalize_last {
  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  // A normalized sequence has no zero at its top.
  lemma {:induction false} NormalizeLast(s: seq<nat>)
    ensures |Normalize(s)| == 0 || Normalize(s)[|Normalize(s)| - 1] != 0
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeLast(s[..|s| - 1]);
    }
  }
}
