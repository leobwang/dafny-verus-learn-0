/*!
# QG_L2_BigNat — the BigNat spine, layer L2 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q02–Q18. Q02's and Q03's files import this layer and L1; from
Q04 on, a module's files import it beside the later layers of their chain.
Its module is QG_L2_BigNat (the L1 names stay in QG_L1_BigNat, which a file
imports too), and each unit's dfyconfig.toml includes this file.

What it holds: helper lemmas about the L1 definitions, all proved, and the
intro-tier definitions `Canonical`, `Normalize`, `FromNat` and `AddLimb`. It
holds no lemma about those four definitions.
*/
module QG_L2_BigNat {
  import opened QG_L1_BigNat

  // ---------------------------------------------------------------------------
  // Helper lemmas about the L1 definitions
  // ---------------------------------------------------------------------------

  lemma ToNatSingleton(d: nat)
    ensures ToNat([d]) == d
  {
    assert [d][1..] == [];
  }

  lemma ToNatCons(d: nat, s: seq<nat>)
    ensures ToNat([d] + s) == d + BASE * ToNat(s)
  {
    assert ([d] + s)[1..] == s;
  }

  // The Horner step, for the empty sequence too.
  lemma ToNatHeadTail(s: seq<nat>)
    ensures ToNat(s) == Head(s) + BASE * ToNat(Tail(s))
  {
  }

  lemma ValidTail(s: seq<nat>)
    requires Valid(s)
    ensures Valid(Tail(s)) && Head(s) < BASE
  {
    if |s| > 0 {
      forall i | 0 <= i < |Tail(s)|
        ensures Tail(s)[i] < BASE
      {
        assert Tail(s)[i] == s[i + 1];
      }
    }
  }

  lemma ValidCons(d: nat, s: seq<nat>)
    requires d < BASE && Valid(s)
    ensures Valid([d] + s)
  {
    forall i | 0 <= i < |[d] + s|
      ensures ([d] + s)[i] < BASE
    {
      if i > 0 {
        assert ([d] + s)[i] == s[i - 1];
      }
    }
  }

  // Dropping one more limb: the head of the suffix is limb i (0 past the end).
  lemma DropStep(s: seq<nat>, i: nat)
    ensures Head(Drop(s, i)) == (if i < |s| then s[i] else 0)
            && Tail(Drop(s, i)) == Drop(s, i + 1)
  {
    if i < |s| {
      assert Drop(s, i)[1..] == s[i + 1..];
    }
  }

  // n valid limbs hold a value below BASE^n.
  lemma {:induction false} ToNatBound(s: seq<nat>)
    requires Valid(s)
    ensures ToNat(s) < Pow(|s|)
    decreases |s|
  {
    if |s| > 0 {
      ValidTail(s);
      ToNatBound(s[1..]);
    }
  }

  // ---------------------------------------------------------------------------
  // Intro-tier definitions
  // ---------------------------------------------------------------------------

  // Canonical: valid, and no most significant zero limb (zero is the empty
  // sequence).
  predicate Canonical(s: seq<nat>)
  {
    Valid(s) && (|s| == 0 || s[|s| - 1] != 0)
  }

  // Strip the most significant zero limbs.
  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  // The base-2^64 digits of n, least significant first.
  function FromNat(n: nat): seq<nat>
    decreases n
  {
    if n == 0 then [] else [n % BASE] + FromNat(n / BASE)
  }

  // Add one limb d (meant for d < BASE), propagating the carry.
  function AddLimb(s: seq<nat>, d: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if d == 0 then [] else [d])
    else if s[0] + d < BASE then [s[0] + d] + s[1..]
    else [s[0] + d - BASE] + AddLimb(s[1..], 1)
  }
}
