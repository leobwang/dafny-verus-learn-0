// Lab 1 local task dh4-tonat-mono (Q12, course-authored; QPLAN §22.6).
// Write the body of `ToNatMono` so that `scripts/vcheck --gate` verifies this file. Keep
// every other line of the file as it is: the definitions above it, its statement and
// its attributes.
module Lab1_dh4_tonat_mono {
  const BASE: nat := 18446744073709551616

  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // The value is monotone in each limb.
  lemma {:induction false} ToNatMono(a: seq<nat>, b: seq<nat>)
    requires |a| == |b| && forall i | 0 <= i < |a| :: a[i] <= b[i]
    ensures ToNat(a) <= ToNat(b)
    decreases |a|
  {
  }
}
