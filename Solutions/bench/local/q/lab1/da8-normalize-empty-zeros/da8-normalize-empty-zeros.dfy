// Lab 1 local task da8-normalize-empty-zeros (Q12, course-authored; QPLAN §22.6).
// Write the body of `NormalizeEmptyZeros` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da8_normalize_empty_zeros {
  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  // A sequence that normalizes to nothing is all zero.
  lemma {:induction false} NormalizeEmptyZeros(s: seq<nat>)
    requires Normalize(s) == []
    ensures forall i | 0 <= i < |s| :: s[i] == 0
    decreases |s|
  {
    if |s| > 0 {
      NormalizeEmptyZeros(s[..|s| - 1]);
      assert forall i | 0 <= i < |s| - 1 :: s[i] == s[..|s| - 1][i];
    }
  }
}
