// Lab 1 local task dh5-mullimb-zero (Q12, course-authored; QPLAN §22.6).
// Write the body of `MulLimbZeroLimbs` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_dh5_mullimb_zero {
  const BASE: nat := 18446744073709551616

  function MulLimbC(s: seq<nat>, d: nat, c: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if c == 0 then [] else [c])
    else
      var t := s[0] * d + c;
      [t % BASE] + MulLimbC(s[1..], d, t / BASE)
  }

  function MulLimb(s: seq<nat>, d: nat): seq<nat>
  {
    MulLimbC(s, d, 0)
  }

  // Multiplying by the limb 0 keeps the length and zeroes every limb.
  lemma {:induction false} MulLimbZeroLimbs(s: seq<nat>)
    ensures |MulLimb(s, 0)| == |s| && forall i | 0 <= i < |s| :: MulLimb(s, 0)[i] == 0
    decreases |s|
  {
  }
}
