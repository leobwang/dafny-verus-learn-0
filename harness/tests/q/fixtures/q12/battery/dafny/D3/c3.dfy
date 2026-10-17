// Battery goal D3, candidate 3 (a whole file; it stands alone).
module Battery_D3 {
  const BASE: nat := 18446744073709551616

  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  // Add one limb d, propagating the carry.
  function AddLimb(s: seq<nat>, d: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if d == 0 then [] else [d])
    else if s[0] + d < BASE then [s[0] + d] + s[1..]
    else [s[0] + d - BASE] + AddLimb(s[1..], 1)
  }

  // Adding the limb 0 to valid limbs changes nothing.
  lemma AddLimbZero(s: seq<nat>)
    requires Valid(s)
    ensures AddLimb(s, 0) == s
  {
    if |s| > 0 {
      assert [s[0]] + s[1..] == s;
    }
  }
}
