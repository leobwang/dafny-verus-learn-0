// QG_L1_BigNat.dfy -- DV0 spike reference (author-only; lives under Solutions/).
// Layer L1 (Q01): little-endian limbs as seq<nat>, the literal BASE = 2^64,
// the Horner abstraction ToNat, Valid, one worked lemma, and the small
// structural helpers (Head/Tail/Drop) that later layers use.
// Core tier: no standard library.
//
// Markers: "// @hole-begin <id>" / "// @hole-end <id>" delimit the body that
// the empty-body gate (tools/gate.py) removes. They are author tooling only.

module QG_L1_BigNat {

  // 2^64 written as a literal, so BASE * x stays linear for the solver.
  const BASE: nat := 18446744073709551616

  // Every limb is a digit in base 2^64.
  predicate Valid(s: seq<nat>)
  {
    forall i | 0 <= i < |s| :: s[i] < BASE
  }

  // Horner-style abstraction, least significant limb first.
  function ToNat(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
  }

  // BASE^n, defined by repeated multiplication by the literal BASE.
  function Pow(n: nat): nat
  {
    if n == 0 then 1 else BASE * Pow(n - 1)
  }

  // Total head and tail: a missing limb reads as 0.
  function Head(s: seq<nat>): nat
  {
    if |s| == 0 then 0 else s[0]
  }

  function Tail(s: seq<nat>): seq<nat>
  {
    if |s| == 0 then [] else s[1..]
  }

  // Suffix from position i; empty once i passes the end.
  function Drop(s: seq<nat>, i: nat): seq<nat>
  {
    if i >= |s| then [] else s[i..]
  }

  // Worked lemma (W): a high zero limb does not change the value.
  lemma ToNatAppendZero(s: seq<nat>)
    ensures ToNat(s + [0]) == ToNat(s)
  {
    // @hole-begin L1.ToNatAppendZero
    if |s| == 0 {
      assert s + [0] == [0];
    } else {
      assert (s + [0])[1..] == s[1..] + [0];
      ToNatAppendZero(s[1..]);
    }
    // @hole-end L1.ToNatAppendZero
  }

  lemma ToNatSingleton(d: nat)
    ensures ToNat([d]) == d
  {
    // @hole-begin L1.ToNatSingleton
    assert [d][1..] == [];
    // @hole-end L1.ToNatSingleton
  }

  lemma ToNatCons(d: nat, s: seq<nat>)
    ensures ToNat([d] + s) == d + BASE * ToNat(s)
  {
    // @hole-begin L1.ToNatCons
    assert ([d] + s)[1..] == s;
    // @hole-end L1.ToNatCons
  }

  // The Horner step, valid for the empty sequence too.
  lemma ToNatHeadTail(s: seq<nat>)
    ensures ToNat(s) == Head(s) + BASE * ToNat(Tail(s))
  {
    // @hole-begin L1.ToNatHeadTail
    // @hole-end L1.ToNatHeadTail
  }

  lemma ValidTail(s: seq<nat>)
    requires Valid(s)
    ensures Valid(Tail(s)) && Head(s) < BASE
  {
    // @hole-begin L1.ValidTail
    if |s| > 0 {
      forall i | 0 <= i < |Tail(s)|
        ensures Tail(s)[i] < BASE
      {
        assert Tail(s)[i] == s[i + 1];
      }
    }
    // @hole-end L1.ValidTail
  }

  lemma ValidCons(d: nat, s: seq<nat>)
    requires d < BASE && Valid(s)
    ensures Valid([d] + s)
  {
    // @hole-begin L1.ValidCons
    forall i | 0 <= i < |[d] + s|
      ensures ([d] + s)[i] < BASE
    {
      if i > 0 {
        assert ([d] + s)[i] == s[i - 1];
      }
    }
    // @hole-end L1.ValidCons
  }

  // Drop one more limb: the head of the suffix is limb i (0 past the end).
  lemma DropStep(s: seq<nat>, i: nat)
    ensures Head(Drop(s, i)) == (if i < |s| then s[i] else 0)
            && Tail(Drop(s, i)) == Drop(s, i + 1)
  {
    // @hole-begin L1.DropStep
    if i < |s| {
      assert Drop(s, i)[1..] == s[i + 1..];
    }
    // @hole-end L1.DropStep
  }

  // Upper bound: n limbs hold a value below BASE^n.
  lemma {:induction false} ToNatBound(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(s) < Pow(|s|)
  {
    // @hole-begin L1.ToNatBound
    if |s| > 0 {
      ValidTail(s);
      ToNatBound(s[1..]);
    }
    // @hole-end L1.ToNatBound
  }
}
