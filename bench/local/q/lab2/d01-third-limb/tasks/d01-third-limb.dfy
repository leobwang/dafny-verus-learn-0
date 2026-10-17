// Lab 2 local task d01-third-limb (Q15, course-authored; QPLAN §25.6).
// Write `ThirdLimb`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `ThirdLimbWitness`. Keep every other line of the file.
module Lab2_D01 {
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

  /** The third-lowest limb of a limb sequence, or 0 when it has fewer than three limbs. */
  method ThirdLimb(s: seq<nat>) returns (d: nat)
  {
    if |s| < 3 {
      d := 0;
    } else {
      d := s[2];
    }
  }

  /** A non-vacuity witness for `ThirdLimb`: one call whose `requires` hold. */
  method ThirdLimbWitness()
  {
  }
}
