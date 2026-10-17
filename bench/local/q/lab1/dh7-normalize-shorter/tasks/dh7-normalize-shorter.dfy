// Lab 1 local task dh7-normalize-shorter (Q12, course-authored; QPLAN §22.6).
// Write the body of `NormalizeShorter` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_dh7_normalize_shorter {
  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  // Normalizing never lengthens a sequence.
  lemma {:induction false} NormalizeShorter(s: seq<nat>)
    ensures |Normalize(s)| <= |s|
    decreases |s|
  {
  }
}
