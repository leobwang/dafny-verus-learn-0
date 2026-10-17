// Battery goal G04, Dafny form (a whole file; it stands alone; given, Q15).
// Two valid numbers of one length are below twice its place value.
// The goal is the last lemma; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
module Battery_G04 {
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

  lemma TwoBelowTwice(s: seq<nat>, t: seq<nat>)
    requires Valid(s) && Valid(t) && |s| == |t|
    ensures ToNat(s) + ToNat(t) < 2 * Pow(|s|)
  {
    forall u: seq<nat> {:trigger Pow(|u|)} | Valid(u) ensures ToNat(u) < Pow(|u|) {
      ToNatBound(u);
    }
  }
}
