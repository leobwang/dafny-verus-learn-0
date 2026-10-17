// Lab 1 local task da4-normalize-valid (Q12, course-authored; QPLAN §22.6).
// Write the body of `NormalizeValid` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da4_normalize_valid {
  const BASE: nat := 18446744073709551616

  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  // Normalizing keeps the limbs valid.
  lemma {:induction false} NormalizeValid(s: seq<nat>)
    requires Valid(s)
    ensures Valid(Normalize(s))
    decreases |s|
  {
  }
}
