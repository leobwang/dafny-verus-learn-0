// Lab 2 local task d08-limbwise-le (Q15, course-authored; QPLAN §25.6).
// Write `LimbwiseLe`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `LimbwiseLeWitness`. Keep every other line of the file.
module Lab2_D08 {
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

  /** Whether two limb sequences have one length and each limb of the first is at most the limb of the second at the same position. */
  method LimbwiseLe(a: seq<nat>, b: seq<nat>) returns (ok: bool)
  {
    if |a| != |b| {
      ok := false;
    } else if |a| == 0 {
      ok := true;
    } else if a[0] > b[0] {
      ok := false;
    } else {
      ok := LimbwiseLe(a[1..], b[1..]);
    }
  }

  /** A non-vacuity witness for `LimbwiseLe`: one call whose `requires` hold. */
  method LimbwiseLeWitness()
  {
  }
}
