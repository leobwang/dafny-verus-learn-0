// Lab 2 local task d06-has-zero-limb (Q15, course-authored; QPLAN §25.6).
// Write `HasZeroLimb`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `HasZeroLimbWitness`. Keep every other line of the file.
module Lab2_D06 {
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

  /** Whether some limb of a limb sequence is zero. */
  method HasZeroLimb(s: seq<nat>) returns (b: bool)
  {
    if |s| == 0 {
      b := false;
    } else if s[0] == 0 {
      b := true;
    } else {
      b := HasZeroLimb(s[1..]);
    }
  }

  /** A non-vacuity witness for `HasZeroLimb`: one call whose `requires` hold. */
  method HasZeroLimbWitness()
  {
  }
}
