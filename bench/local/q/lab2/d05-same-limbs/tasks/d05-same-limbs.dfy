// Lab 2 local task d05-same-limbs (Q15, course-authored; QPLAN §25.6).
// Write `SameLimbs`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `SameLimbsWitness`. Keep every other line of the file.
module Lab2_D05 {
  const BASE: nat := 18446744073709551616

  // Every limb is a digit in base BASE.
  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  // The value of a limb sequence, least significant limb first.
  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  /** Whether two limb sequences are the same sequence, limb for limb. */
  method SameLimbs(a: seq<nat>, b: seq<nat>) returns (e: bool)
  {
    e := |a| == |b| && forall i | 0 <= i < |a| :: a[i] == b[i];
  }

  /** A non-vacuity witness for `SameLimbs`: one call whose `requires` hold. */
  method SameLimbsWitness()
  {
  }
}
