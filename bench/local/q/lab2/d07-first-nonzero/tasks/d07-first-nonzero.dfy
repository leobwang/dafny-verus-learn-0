// Lab 2 local task d07-first-nonzero (Q15, course-authored; QPLAN §25.6).
// Write `FirstNonZero`'s `requires` and `ensures` from its prose (never change its code), and
// one call whose `requires` hold in `FirstNonZeroWitness`. Keep every other line of the file.
module Lab2_D07 {
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

  /** The index of the lowest non-zero limb of a limb sequence, or its length when every limb is zero. */
  method FirstNonZero(s: seq<nat>) returns (i: nat)
  {
    if |s| == 0 || s[0] != 0 {
      i := 0;
    } else {
      var k := FirstNonZero(s[1..]);
      i := k + 1;
    }
  }

  /** A non-vacuity witness for `FirstNonZero`: one call whose `requires` hold. */
  method FirstNonZeroWitness()
  {
  }
}
