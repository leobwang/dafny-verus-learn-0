// QG_L3_BigNat.dfy -- DV0 spike reference (author-only; lives under Solutions/).
// Layer L3 (Q04-Q06): Cmp, which agrees with the ToNat order on valid inputs
// (canonical or not) and compiles through a `by method` loop; the
// length/value ordering facts for canonical numerals; and the std-tier
// helper (PowIsStdPow + PowMono through Std.Arithmetic.Power).
// Std tier: needs --standard-libraries. Verify together with L1 and L2.

module QG_L3_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import Std.Arithmetic.Power

  // Three-way comparison, decided by the most significant differing limb.
  // A missing limb reads as 0, so non-canonical inputs compare by value.
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
  } by method {
    var i := if |a| < |b| then |b| else |a|;
    var r := 0;
    // @hole-begin L3.CmpByMethod
    assert Drop(a, i) == [] && Drop(b, i) == [];
    // @hole-end L3.CmpByMethod
    while i > 0
      // @hole-begin L3.CmpByMethod
      invariant 0 <= i <= (if |a| < |b| then |b| else |a|)
      invariant r == Cmp(Drop(a, i), Drop(b, i))
      // @hole-end L3.CmpByMethod
      decreases i
    {
      i := i - 1;
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      // @hole-begin L3.CmpByMethod
      DropStep(a, i);
      DropStep(b, i);
      // @hole-end L3.CmpByMethod
      if r == 0 {
        r := if x < y then -1 else if x > y then 1 else 0;
      }
    }
    // @hole-begin L3.CmpByMethod
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    // @hole-end L3.CmpByMethod
    return r;
  }

  lemma {:induction false} CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  {
    // @hole-begin L3.CmpCorrect
    if |a| != 0 || |b| != 0 {
      ValidTail(a);
      ValidTail(b);
      CmpCorrect(Tail(a), Tail(b));
      ToNatHeadTail(a);
      ToNatHeadTail(b);
    }
    // @hole-end L3.CmpCorrect
  }

  // Std-tier helper: the local Pow is the library's Pow at the literal BASE.
  lemma {:induction false} PowIsStdPow(n: nat)
    ensures Pow(n) == Power.Pow(BASE, n)
  {
    // @hole-begin L3.PowIsStdPow
    if n > 0 {
      PowIsStdPow(n - 1);
    }
    // @hole-end L3.PowIsStdPow
  }

  // Monotonicity of BASE^n, by one library call.
  lemma {:induction false} PowMono(m: nat, n: nat)
    requires m <= n
    ensures Pow(m) <= Pow(n)
  {
    // @hole-begin L3.PowMono
    PowIsStdPow(m);
    PowIsStdPow(n);
    Power.LemmaPowIncreases(BASE, m, n);
    // @hole-end L3.PowMono
  }

  // Lower bound: a canonical numeral with k > 0 limbs is at least BASE^(k-1).
  lemma {:induction false} ToNatLowerBound(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
    decreases |s|
  {
    // @hole-begin L3.ToNatLowerBound
    if |s| > 1 {
      assert s[1..][|s[1..]| - 1] == s[|s| - 1];
      ValidTail(s);
      ToNatLowerBound(s[1..]);
    }
    // @hole-end L3.ToNatLowerBound
  }

  // For canonical numerals, fewer limbs means a smaller value.
  lemma {:induction false} CanonicalLengthOrder(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && |a| < |b|
    ensures ToNat(a) < ToNat(b)
  {
    // @hole-begin L3.CanonicalLengthOrder
    ToNatBound(a);
    ToNatLowerBound(b);
    PowMono(|a|, |b| - 1);
    // @hole-end L3.CanonicalLengthOrder
  }

  // Canonical numerals are unique: equal value means equal limbs.
  lemma CanonicalUnique(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && ToNat(a) == ToNat(b)
    ensures a == b
    decreases |a|
  {
    // @hole-begin L3.CanonicalUnique
    if |a| < |b| {
      CanonicalLengthOrder(a, b);
    } else if |b| < |a| {
      CanonicalLengthOrder(b, a);
    } else if |a| > 0 {
      ValidTail(a);
      ValidTail(b);
      if |a| > 1 {
        assert a[1..][|a| - 2] == a[|a| - 1];
        assert b[1..][|b| - 2] == b[|b| - 1];
      }
      CanonicalUnique(a[1..], b[1..]);
      assert a == [a[0]] + a[1..];
      assert b == [b[0]] + b[1..];
    }
    // @hole-end L3.CanonicalUnique
  }
}
