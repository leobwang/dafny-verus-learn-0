// Lab 2 local task d03-drop-low (Q15, course-authored; QPLAN §25.6).
// Write `DropLow`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `DropLowWitness`. Keep every other line of the file.
module Lab2_D03 {
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

  /** The limb sequence without its lowest limb, the empty sequence staying empty. */
  method DropLow(s: seq<nat>) returns (t: seq<nat>)
  {
    if |s| == 0 {
      t := [];
    } else {
      t := s[1..];
    }
  }

  /** A non-vacuity witness for `DropLow`: one call whose `requires` hold. */
  method DropLowWitness()
  {
  }
}
