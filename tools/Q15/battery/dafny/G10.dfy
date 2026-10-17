// Battery goal G10, Dafny form (a whole file; it stands alone; given, Q15).
// A valid number is below the place value of any longer length.
// The goal is the last lemma; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
module Battery_G10 {
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

  lemma ToNatBound(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(s) < Pow(|s|)
    decreases |s|
  {
    if |s| == 0 {
      reveal Pow();
    } else {
      assert Valid(s[1..]);
      ToNatBound(s[1..]);
      PowStep(|s| - 1);
    }
  }

  lemma PowMono(m: nat, n: nat)
    requires m <= n
    ensures Pow(m) <= Pow(n)
    decreases n - m
  {
    if m < n {
      PowMono(m + 1, n);
      PowStep(m);
      PowPos(m);
    }
  }

  lemma BelowLongerPlace(s: seq<nat>, n: nat)
    requires Valid(s) && |s| <= n
    ensures ToNat(s) < Pow(n)
  {
    forall m: nat, k: nat {:trigger Pow(k)} | m <= k ensures Pow(m) <= Pow(k) {
      PowMono(m, k);
    }
    ToNatBound(s);
  }
}
