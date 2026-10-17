// QG_L2_BigNat.dfy -- DV0 spike reference (author-only; lives under Solutions/).
// Layer L2 (Q02-Q03): Normalize (strip high zero limbs, value preserved),
// FromNat, AddLimb, plus the loop form of Normalize (the invariant pair).
// Verify together with QG_L1_BigNat.dfy.

module QG_L2_BigNat {
  import opened QG_L1_BigNat

  // Canonical: valid, and no high zero limb (zero is the empty sequence).
  predicate Canonical(s: seq<nat>)
  {
    Valid(s) && (|s| == 0 || s[|s| - 1] != 0)
  }

  function Normalize(s: seq<nat>): seq<nat>
    decreases |s|
  {
    if |s| == 0 then []
    else if s[|s| - 1] != 0 then s
    else Normalize(s[..|s| - 1])
  }

  function FromNat(n: nat): seq<nat>
    decreases n
  {
    if n == 0 then [] else [n % BASE] + FromNat(n / BASE)
  }

  // Add one limb d (d < BASE) with carry propagation.
  function AddLimb(s: seq<nat>, d: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if d == 0 then [] else [d])
    else if s[0] + d < BASE then [s[0] + d] + s[1..]
    else [s[0] + d - BASE] + AddLimb(s[1..], 1)
  }

  lemma NormalizeToNat(s: seq<nat>)
    ensures ToNat(Normalize(s)) == ToNat(s)
    decreases |s|
  {
    // @hole-begin L2.NormalizeToNat
    if |s| > 0 && s[|s| - 1] == 0 {
      var p := s[..|s| - 1];
      assert s == p + [0];
      ToNatAppendZero(p);
      NormalizeToNat(p);
    }
    // @hole-end L2.NormalizeToNat
  }

  lemma {:induction false} NormalizeCanonical(s: seq<nat>)
    requires Valid(s)
    ensures Canonical(Normalize(s))
    decreases |s|
  {
    // @hole-begin L2.NormalizeCanonical
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeCanonical(s[..|s| - 1]);
    }
    // @hole-end L2.NormalizeCanonical
  }

  lemma {:induction false} NormalizeIdempotent(s: seq<nat>)
    ensures Normalize(Normalize(s)) == Normalize(s)
    decreases |s|
  {
    // @hole-begin L2.NormalizeIdempotent
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeIdempotent(s[..|s| - 1]);
    }
    // @hole-end L2.NormalizeIdempotent
  }

  lemma {:induction false} FromNatCorrect(n: nat)
    ensures Valid(FromNat(n)) && ToNat(FromNat(n)) == n
    decreases n
  {
    // @hole-begin L2.FromNatCorrect
    if n > 0 {
      FromNatCorrect(n / BASE);
      ToNatCons(n % BASE, FromNat(n / BASE));
      ValidCons(n % BASE, FromNat(n / BASE));
    }
    // @hole-end L2.FromNatCorrect
  }

  lemma {:induction false} FromNatCanonical(n: nat)
    ensures Canonical(FromNat(n))
    decreases n
  {
    // @hole-begin L2.FromNatCanonical
    FromNatCorrect(n);
    if n > 0 {
      FromNatCanonical(n / BASE);
    }
    // @hole-end L2.FromNatCanonical
  }

  lemma {:induction false} AddLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(AddLimb(s, d)) && ToNat(AddLimb(s, d)) == ToNat(s) + d
    decreases |s|
  {
    // @hole-begin L2.AddLimbCorrect
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
    // @hole-end L2.AddLimbCorrect
  }

  // Loop form of Normalize: the Dafny half of the Q10 invariant pair.
  method NormalizeLoop(s: seq<nat>) returns (r: seq<nat>)
    ensures r == Normalize(s)
  {
    var n := |s|;
    // @hole-begin L2.NormalizeLoop
    assert s[..n] == s;
    // @hole-end L2.NormalizeLoop
    while n > 0 && s[n - 1] == 0
      // @hole-begin L2.NormalizeLoop
      invariant 0 <= n <= |s|
      invariant Normalize(s[..n]) == Normalize(s)
      // @hole-end L2.NormalizeLoop
      decreases n
    {
      // @hole-begin L2.NormalizeLoop
      assert s[..n][..n - 1] == s[..n - 1];
      // @hole-end L2.NormalizeLoop
      n := n - 1;
    }
    r := s[..n];
  }
}
