// Lab 1 local task da1-addlimb-all-max (Q12, course-authored; QPLAN §22.6).
// Write the body of `AddLimbAllMax` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da1_addlimb_all_max {
  const BASE: nat := 18446744073709551616

  function AddLimb(s: seq<nat>, d: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if d == 0 then [] else [d])
    else if s[0] + d < BASE then [s[0] + d] + s[1..]
    else [s[0] + d - BASE] + AddLimb(s[1..], 1)
  }

  // Adding 1 to limbs that are all BASE - 1 carries out of the top.
  lemma {:induction false} AddLimbAllMax(s: seq<nat>)
    requires forall i | 0 <= i < |s| :: s[i] == BASE - 1
    ensures |AddLimb(s, 1)| == |s| + 1
    decreases |s|
  {
  }
}
