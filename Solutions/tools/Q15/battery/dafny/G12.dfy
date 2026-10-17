// Battery goal G12, Dafny form (a whole file; it stands alone; given, Q15).
// Limbs under a bound stay under it in a concatenation (the step on the parts).
// The goal is the last lemma; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
module Battery_G12 {
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

  // Every limb is at most m.
  predicate Below(s: seq<nat>, m: nat)
  {
    forall i | 0 <= i < |s| :: s[i] <= m
  }

  lemma BelowConcat(s: seq<nat>, t: seq<nat>, m: nat)
    requires Below(s, m) && Below(t, m)
    ensures Below(s + t, m)
  {
    forall i {:trigger s[i]} | 0 <= i < |s + t| ensures (s + t)[i] <= m {
      if i >= |s| {
        assert (s + t)[i] == t[i - |s|];
      }
    }
  }
}
