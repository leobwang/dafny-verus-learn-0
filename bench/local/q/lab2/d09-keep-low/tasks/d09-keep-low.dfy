// Lab 2 local task d09-keep-low (Q15, course-authored; QPLAN §25.6).
// Write `KeepLow`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `KeepLowWitness`. Keep every other line of the file.
module Lab2_D09 {
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

  /** The lowest k limbs of a limb sequence, or all of them when it has fewer than k. */
  method KeepLow(s: seq<nat>, k: nat) returns (t: seq<nat>)
  {
    if k >= |s| {
      t := s;
    } else {
      t := s[..k];
    }
  }

  /** A non-vacuity witness for `KeepLow`: one call whose `requires` hold. */
  method KeepLowWitness()
  {
  }
}
