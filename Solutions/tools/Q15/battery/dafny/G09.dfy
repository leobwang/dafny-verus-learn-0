// Battery goal G09, Dafny form (a whole file; it stands alone; given, Q15).
// Three place values in a row (a trigger with two terms).
// The goal is the last lemma; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
module Battery_G09 {
  const BASE: nat := 18446744073709551616

  // The place value of limb n, BASE to the power n. Opaque: its facts are
  // the lemmas below.
  opaque function Pow(n: nat): nat
    decreases n
  {
    if n == 0 then 1 else BASE * Pow(n - 1)
  }

  lemma PowStep(k: nat)
    ensures Pow(k + 1) == BASE * Pow(k)
  {
    reveal Pow();
  }

  lemma PowPos(k: nat)
    ensures 0 < Pow(k)
  {
    reveal Pow();
    if k > 0 {
      PowPos(k - 1);
    }
  }

  // The value of a limb sequence, least significant limb first.
  function ToNat(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // Every limb is a digit in base BASE.
  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  lemma ThreePlaces(n: nat)
    ensures Pow(n) < Pow(n + 1) && Pow(n + 1) < Pow(n + 1 + 1)
  {
    forall k: nat {:trigger Pow(k)} ensures Pow(k) < Pow(k + 1) {
      PowStep(k);
      PowPos(k);
    }
  }
}
