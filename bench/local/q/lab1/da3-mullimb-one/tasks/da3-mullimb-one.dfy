// Lab 1 local task da3-mullimb-one (Q12, course-authored; QPLAN §22.6).
// Write the body of `MulLimbOne` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_da3_mullimb_one {
  const BASE: nat := 18446744073709551616

  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

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

  // Multiplying valid limbs by the limb 1 changes nothing.
  lemma {:induction false} MulLimbOne(s: seq<nat>)
    requires Valid(s)
    ensures MulLimb(s, 1) == s
    decreases |s|
  {
  }
}
