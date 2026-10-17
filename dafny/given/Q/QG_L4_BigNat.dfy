/*!
# QG_L4_BigNat — the BigNat spine, layer L4 (PROVIDED, complete)

This file is provided infrastructure, not an exercise: there is nothing to fill
in and nothing here is a hole. It is frozen: no session edits it, and no
module copies it.

Imported by: Q07–Q18. From Q07 on, a module's files that use it import it
beside L1–L3. Its modules are QG_L4_BigNat, QG_L4_Spec and QG_L4_Limbs, and
each unit that reaches it includes this file through its dfyconfig.toml.

Do not open this file before you start Q07: it holds proved versions of
lemmas that Q04 poses as holes, so reading it earlier spoils them.

What it holds: two proved lemmas about the L1 and L3 definitions (`PowAdd`,
`CmpCorrect`); schoolbook addition (`AddC`, `Add`) with its proofs and a
compiled loop (`AddLoop`); multiplication by one limb (`MulLimbC`, `MulLimb`)
with its proofs and a compiled loop (`MulLimbLoop`); the arithmetic facts they
use; the abstract module QG_L4_Spec (what any big-number implementation must
provide) and its limb implementation QG_L4_Limbs.
*/
module {:disableNonlinearArithmetic} QG_L4_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened Std.Arithmetic.Mul

  // ---------------------------------------------------------------------------
  // Proved lemmas about the L1 and L3 definitions
  // ---------------------------------------------------------------------------

  // The power of a sum is the product of the powers.
  lemma PowAdd(m: nat, n: nat)
    ensures Pow(m + n) == Pow(m) * Pow(n)
    decreases m
  {
    if m == 0 {
      LemmaMulBasics(Pow(n));
    } else {
      PowAdd(m - 1, n);
      LemmaMulIsAssociative(BASE, Pow(m - 1), Pow(n));
    }
  }

  // Cmp agrees with the order of the values.
  lemma CmpCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures -1 <= Cmp(a, b) <= 1
            && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
            && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
    decreases |a| + |b|
  {
    if |a| != 0 || |b| != 0 {
      ValidTail(a);
      ValidTail(b);
      CmpCorrect(Tail(a), Tail(b));
      ToNatHeadTail(a);
      ToNatHeadTail(b);
    }
  }

  // ---------------------------------------------------------------------------
  // Arithmetic facts (from Std.Arithmetic.Mul)
  // ---------------------------------------------------------------------------

  lemma MulNonneg(x: nat, y: nat)
    ensures 0 <= x * y
  {
    LemmaMulNonnegative(x, y);
  }

  lemma MulZero(x: nat, y: nat)
    requires x == 0 || y == 0
    ensures x * y == 0
  {
    LemmaMulBasics(x);
    LemmaMulBasics(y);
  }

  lemma MulComm(x: nat, y: nat)
    ensures x * y == y * x
  {
    LemmaMulIsCommutative(x, y);
  }

  // A carry out of one limb product is itself a limb.
  lemma MulLimbDigit(x: nat, d: nat, c: nat)
    requires x < BASE && d < BASE && c < BASE
    ensures (x * d + c) / BASE < BASE
  {
    LemmaMulUpperBound(x, BASE - 1, d, BASE - 1);
  }

  // The Horner step distributes over a multiplier.
  lemma DistribHorner(h: nat, t: nat, x: nat)
    ensures (h + BASE * t) * x == h * x + BASE * (t * x)
  {
    LemmaMulIsDistributive(x, h, BASE * t);
    LemmaMulIsAssociative(BASE, t, x);
  }

  // ---------------------------------------------------------------------------
  // Addition
  // ---------------------------------------------------------------------------

  // Schoolbook addition with an incoming carry c.
  opaque function AddC(a: seq<nat>, b: seq<nat>, c: nat): seq<nat>
    decreases |a| + |b|
  {
    if |a| == 0 && |b| == 0 then (if c == 0 then [] else [c])
    else
      var t := Head(a) + Head(b) + c;
      if t < BASE then [t] + AddC(Tail(a), Tail(b), 0)
      else [t - BASE] + AddC(Tail(a), Tail(b), 1)
  }

  function Add(a: seq<nat>, b: seq<nat>): seq<nat>
  {
    AddC(a, b, 0)
  }

  lemma {:induction false} AddCCorrect(a: seq<nat>, b: seq<nat>, c: nat)
    requires Valid(a) && Valid(b) && c <= 1
    ensures Valid(AddC(a, b, c)) && ToNat(AddC(a, b, c)) == ToNat(a) + ToNat(b) + c
    decreases |a| + |b|
  {
    reveal AddC();
    if |a| == 0 && |b| == 0 {
      if c != 0 {
        ToNatSingleton(c);
      }
    } else {
      ValidTail(a);
      ValidTail(b);
      ToNatHeadTail(a);
      ToNatHeadTail(b);
      var t := Head(a) + Head(b) + c;
      var c' := if t < BASE then 0 else 1;
      var d := if t < BASE then t else t - BASE;
      AddCCorrect(Tail(a), Tail(b), c');
      ToNatCons(d, AddC(Tail(a), Tail(b), c'));
      ValidCons(d, AddC(Tail(a), Tail(b), c'));
    }
  }

  lemma AddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Add(a, b)) && ToNat(Add(a, b)) == ToNat(a) + ToNat(b)
  {
    AddCCorrect(a, b, 0);
  }

  // One unfolding of AddC at position i, phrased with Drop.
  lemma AddCDropStep(a: seq<nat>, b: seq<nat>, i: nat, c: nat)
    requires i < |a| || i < |b|
    ensures var t := (if i < |a| then a[i] else 0) + (if i < |b| then b[i] else 0) + c;
            AddC(Drop(a, i), Drop(b, i), c)
            == [if t < BASE then t else t - BASE]
               + AddC(Drop(a, i + 1), Drop(b, i + 1), if t < BASE then 0 else 1)
  {
    reveal AddC();
    DropStep(a, i);
    DropStep(b, i);
  }

  // Compiled loop form of Add.
  method {:isolate_assertions} AddLoop(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Add(a, b) && Valid(r) && ToNat(r) == ToNat(a) + ToNat(b)
  {
    var n := if |a| < |b| then |b| else |a|;
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    while i < n
      invariant 0 <= i <= n
      invariant carry <= 1
      invariant r + AddC(Drop(a, i), Drop(b, i), carry) == Add(a, b)
      decreases n - i
    {
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      var t := x + y + carry;
      var digit := if t < BASE then t else t - BASE;
      var c: nat := if t < BASE then 0 else 1;
      ghost var rest := AddC(Drop(a, i + 1), Drop(b, i + 1), c);
      assert r + ([digit] + rest) == (r + [digit]) + rest;
      AddCDropStep(a, b, i, carry);
      r := r + [digit];
      carry := c;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    reveal AddC();
    AddCorrect(a, b);
  }

  // ---------------------------------------------------------------------------
  // Multiplication by one limb
  // ---------------------------------------------------------------------------

  // Multiply by one limb d with an incoming carry c.
  function MulLimbC(s: seq<nat>, d: nat, c: nat): seq<nat>
    decreases |s|
  {
    if |s| == 0 then (if c == 0 then [] else [c])
    else
      MulNonneg(s[0], d);
      var t := s[0] * d + c;
      [t % BASE] + MulLimbC(s[1..], d, t / BASE)
  }

  function MulLimb(s: seq<nat>, d: nat): seq<nat>
  {
    MulLimbC(s, d, 0)
  }

  lemma {:induction false} MulLimbCCorrect(s: seq<nat>, d: nat, c: nat)
    requires Valid(s) && d < BASE && c < BASE
    ensures Valid(MulLimbC(s, d, c)) && ToNat(MulLimbC(s, d, c)) == ToNat(s) * d + c
    decreases |s|
  {
    if |s| == 0 {
      MulZero(ToNat(s), d);
      if c != 0 {
        ToNatSingleton(c);
      }
    } else {
      ValidTail(s);
      MulNonneg(s[0], d);
      var t := s[0] * d + c;
      MulLimbDigit(s[0], d, c);
      MulLimbCCorrect(s[1..], d, t / BASE);
      ToNatCons(t % BASE, MulLimbC(s[1..], d, t / BASE));
      ValidCons(t % BASE, MulLimbC(s[1..], d, t / BASE));
      DistribHorner(s[0], ToNat(s[1..]), d);
    }
  }

  lemma MulLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d
  {
    MulLimbCCorrect(s, d, 0);
  }

  // Compiled loop form of MulLimb.
  method {:isolate_assertions} MulLimbLoop(s: seq<nat>, d: nat) returns (r: seq<nat>)
    requires Valid(s) && d < BASE
    ensures r == MulLimb(s, d) && Valid(r) && ToNat(r) == ToNat(s) * d
  {
    r := [];
    var carry: nat := 0;
    var i := 0;
    assert s[0..] == s;
    while i < |s|
      invariant 0 <= i <= |s|
      invariant r + MulLimbC(s[i..], d, carry) == MulLimb(s, d)
      decreases |s| - i
    {
      MulNonneg(s[i], d);
      assert s[i..][1..] == s[i + 1..];
      var t := s[i] * d + carry;
      r := r + [t % BASE];
      carry := t / BASE;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    MulLimbCorrect(s, d);
  }
}

// What any big-number implementation must provide: the frozen statements.
abstract module {:disableNonlinearArithmetic} QG_L4_Spec {
  type BigNat

  ghost function Val(x: BigNat): nat
  ghost predicate Wf(x: BigNat)

  function Zero(): BigNat
  function FromNat(n: nat): BigNat
  function Add(a: BigNat, b: BigNat): BigNat
  function Cmp(a: BigNat, b: BigNat): int

  lemma ZeroCorrect()
    ensures Wf(Zero()) && Val(Zero()) == 0

  lemma FromNatCorrect(n: nat)
    ensures Wf(FromNat(n)) && Val(FromNat(n)) == n

  lemma AddCorrect(a: BigNat, b: BigNat)
    requires Wf(a) && Wf(b)
    ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)

  lemma CmpCorrect(a: BigNat, b: BigNat)
    requires Wf(a) && Wf(b)
    ensures (Cmp(a, b) < 0 <==> Val(a) < Val(b)) && (Cmp(a, b) == 0 <==> Val(a) == Val(b))
}

// The limb implementation refines the frozen statements.
module {:disableNonlinearArithmetic} QG_L4_Limbs refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L1.Valid(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L4.Add(a, b) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
  }

  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L4.AddCorrect(a, b);
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }
}
