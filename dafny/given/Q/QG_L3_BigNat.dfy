/*!
# QG_L3_BigNat — the BigNat spine, layer L3 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q04–Q18. From Q04 on, a module's files that use it import it
beside L1 and L2 (QG_L1_BigNat and QG_L2_BigNat, which such a file imports
too). Its module is QG_L3_BigNat, and each unit that reaches it includes this
file through its dfyconfig.toml.

Do not open this file before you start Q04: it holds proved versions of
lemmas that Q02 and Q03 pose as holes, so reading it earlier spoils them.

What it holds: five proved lemmas about the L2 definitions (`ToNatDropLastZero`,
`NormalizeToNat`, `NormalizeCanonical`, `FromNatCorrect`, `AddLimbCorrect`),
the moderate-tier definition `Cmp`, and the bridge lemma `PowIsStdPow`.
*/
module QG_L3_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import Power = Std.Arithmetic.Power

  // ---------------------------------------------------------------------------
  // Proved lemmas about the L2 definitions
  // ---------------------------------------------------------------------------

  // Dropping one most significant zero limb keeps the value.
  lemma ToNatDropLastZero(s: seq<nat>)
    requires |s| > 0 && s[|s| - 1] == 0
    ensures ToNat(s[..|s| - 1]) == ToNat(s)
  {
    var p := s[..|s| - 1];
    assert s == p + [0];
    ToNatAppendZero(p);
  }

  // Normalize keeps the value.
  lemma NormalizeToNat(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      ToNatDropLastZero(s);
      NormalizeToNat(s[..|s| - 1]);
    }
  }

  // Normalize of valid limbs is canonical.
  lemma NormalizeCanonical(s: seq<nat>)
    requires Valid(s)
    ensures Canonical(Normalize(s))
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeCanonical(s[..|s| - 1]);
    }
  }

  // FromNat gives valid limbs with value n.
  lemma FromNatCorrect(n: nat)
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
    decreases n
  {
    if n > 0 {
      FromNatCorrect(n / BASE);
      ToNatCons(n % BASE, FromNat(n / BASE));
      ValidCons(n % BASE, FromNat(n / BASE));
    }
  }

  // AddLimb of a valid sequence and one limb gives valid limbs with the sum.
  lemma AddLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(AddLimb(s, d)) && ToNat(AddLimb(s, d)) == ToNat(s) + d
    decreases |s|
  {
    if |s| == 0 {
      ToNatSingleton(d);
    } else if s[0] + d < BASE {
      ValidTail(s);
      ToNatCons(s[0] + d, s[1..]);
      ValidCons(s[0] + d, s[1..]);
    } else {
      ValidTail(s);
      AddLimbCorrect(s[1..], 1);
      ToNatCons(s[0] + d - BASE, AddLimb(s[1..], 1));
      ValidCons(s[0] + d - BASE, AddLimb(s[1..], 1));
    }
  }

  // ---------------------------------------------------------------------------
  // Moderate-tier definition
  // ---------------------------------------------------------------------------

  // Three-way comparison of two limb sequences: -1, 0 or 1.
  function Cmp(a: seq<nat>, b: seq<nat>): int
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then 0
    else
      var c := Cmp(Tail(a), Tail(b));
      if c != 0 then c
      else if Head(a) < Head(b) then -1
      else if Head(a) > Head(b) then 1
      else 0
  }

  // ---------------------------------------------------------------------------
  // Bridge
  // ---------------------------------------------------------------------------

  // L1's Pow is Power.Pow at BASE.
  lemma PowIsStdPow(n: nat)
    ensures Pow(n) == Power.Pow(BASE, n)
    decreases n
  {
    if n > 0 {
      PowIsStdPow(n - 1);
    }
  }
}
