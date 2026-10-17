// Lab 2 local task d02-top-is-zero (Q15, course-authored; QPLAN §25.6).
// Write `TopIsZero`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `TopIsZeroWitness`. Keep every other line of the file.
module Lab2_D02 {
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

  /** Whether the top limb of a limb sequence is zero; an empty sequence has no top limb, so the answer is false. */
  method TopIsZero(s: seq<nat>) returns (b: bool)
  {
    b := |s| > 0 && s[|s| - 1] == 0;
  }

  /** A non-vacuity witness for `TopIsZero`: one call whose `requires` hold. */
  method TopIsZeroWitness()
  {
  }
}
