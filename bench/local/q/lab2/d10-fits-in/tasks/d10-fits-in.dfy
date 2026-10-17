// Lab 2 local task d10-fits-in (Q15, course-authored; QPLAN §25.6).
// Write `FitsIn`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `FitsInWitness`. Keep every other line of the file.
module Lab2_D10 {
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

  /** Whether a limb sequence needs at most k limbs: every limb at position k or above is zero. */
  method FitsIn(s: seq<nat>, k: nat) returns (b: bool)
  {
    if |s| <= k {
      b := true;
    } else if s[|s| - 1] != 0 {
      b := false;
    } else {
      b := FitsIn(s[..|s| - 1], k);
    }
  }

  /** A non-vacuity witness for `FitsIn`: one call whose `requires` hold. */
  method FitsInWitness()
  {
  }
}
