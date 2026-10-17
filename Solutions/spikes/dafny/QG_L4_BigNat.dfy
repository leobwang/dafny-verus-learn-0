// QG_L4_BigNat.dfy -- DV0 spike reference (author-only; lives under Solutions/).
// Layer L4 (Q07-Q09): Add with its correctness proof (carry recursion) and a
// compiled loop form with an invariant; MulLimb (multiply by one limb) with
// its proof and loop form; full Mul (to test whether the design 10.1
// fallback is needed); an abstract module BigNatSpec and a concrete
// refinement. Std tier: needs --standard-libraries. Verify with L1-L3.
//
// Nonlinear arithmetic is off in every module of this file. Probe
// toy-nl-modattr: at Dafny 4.11.0 the module attribute
// {:disableNonlinearArithmetic} also switches nonlinear arithmetic off in
// every module declared after it in the same file, so the attribute is
// written on each module to say what is in force. The nonlinear facts the
// proofs need come from Std.Arithmetic.Mul (QG_L4_Arith), and AddC is opaque.

// Nonlinear facts, proved by library calls (no nonlinear solver support).
module {:disableNonlinearArithmetic} QG_L4_Arith {
  import opened QG_L1_BigNat
  import opened Std.Arithmetic.Mul

  lemma MulNonneg(x: nat, y: nat)
    ensures 0 <= x * y
  {
    // @hole-begin Arith.MulNonneg
    LemmaMulNonnegative(x, y);
    // @hole-end Arith.MulNonneg
  }

  lemma MulZero(x: nat, y: nat)
    requires x == 0 || y == 0
    ensures x * y == 0
  {
    // @hole-begin Arith.MulZero
    LemmaMulBasics(x);
    LemmaMulBasics(y);
    // @hole-end Arith.MulZero
  }

  lemma MulComm(x: nat, y: nat)
    ensures x * y == y * x
  {
    // @hole-begin Arith.MulComm
    LemmaMulIsCommutative(x, y);
    // @hole-end Arith.MulComm
  }

  // A carry out of one limb product is itself a limb.
  lemma MulLimbDigit(x: nat, d: nat, c: nat)
    requires x < BASE && d < BASE && c < BASE
    ensures (x * d + c) / BASE < BASE
  {
    // @hole-begin Arith.MulLimbDigit
    LemmaMulUpperBound(x, BASE - 1, d, BASE - 1);
    // @hole-end Arith.MulLimbDigit
  }

  // The Horner step distributes over a multiplier.
  lemma DistribHorner(h: nat, t: nat, x: nat)
    ensures (h + BASE * t) * x == h * x + BASE * (t * x)
  {
    // @hole-begin Arith.DistribHorner
    LemmaMulIsDistributive(x, h, BASE * t);
    LemmaMulIsAssociative(BASE, t, x);
    // @hole-end Arith.DistribHorner
  }
}

module {:disableNonlinearArithmetic} QG_L4_BigNat {
  import opened QG_L1_BigNat
  import opened QG_L4_Arith

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
    // @hole-begin L4.AddCCorrect
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
    // @hole-end L4.AddCCorrect
  }

  lemma AddCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Add(a, b)) && ToNat(Add(a, b)) == ToNat(a) + ToNat(b)
  {
    // @hole-begin L4.AddCorrect
    AddCCorrect(a, b, 0);
    // @hole-end L4.AddCorrect
  }

  // One unfolding of AddC at position i, phrased with Drop.
  lemma AddCDropStep(a: seq<nat>, b: seq<nat>, i: nat, c: nat)
    requires i < |a| || i < |b|
    ensures var t := (if i < |a| then a[i] else 0) + (if i < |b| then b[i] else 0) + c;
            AddC(Drop(a, i), Drop(b, i), c)
            == [if t < BASE then t else t - BASE]
               + AddC(Drop(a, i + 1), Drop(b, i + 1), if t < BASE then 0 else 1)
  {
    // @hole-begin L4.AddCDropStep
    reveal AddC();
    DropStep(a, i);
    DropStep(b, i);
    // @hole-end L4.AddCDropStep
  }

  // Compiled loop form of Add: the Dafny half of the add pair.
  method {:isolate_assertions} AddLoop(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures r == Add(a, b) && Valid(r) && ToNat(r) == ToNat(a) + ToNat(b)
  {
    var n := if |a| < |b| then |b| else |a|;
    r := [];
    var carry: nat := 0;
    var i := 0;
    // @hole-begin L4.AddLoop
    assert Drop(a, 0) == a && Drop(b, 0) == b;
    // @hole-end L4.AddLoop
    while i < n
      // @hole-begin L4.AddLoop
      invariant 0 <= i <= n
      invariant carry <= 1
      invariant r + AddC(Drop(a, i), Drop(b, i), carry) == Add(a, b)
      // @hole-end L4.AddLoop
      decreases n - i
    {
      var x := if i < |a| then a[i] else 0;
      var y := if i < |b| then b[i] else 0;
      var t := x + y + carry;
      var digit := if t < BASE then t else t - BASE;
      var c: nat := if t < BASE then 0 else 1;
      // @hole-begin L4.AddLoop
      AddCDropStep(a, b, i, carry);
      ghost var rest := AddC(Drop(a, i + 1), Drop(b, i + 1), c);
      assert r + ([digit] + rest) == (r + [digit]) + rest;
      // @hole-end L4.AddLoop
      r := r + [digit];
      carry := c;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    // @hole-begin L4.AddLoop
    reveal AddC();
    AddCorrect(a, b);
    // @hole-end L4.AddLoop
  }

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
    // @hole-begin L4.MulLimbCCorrect
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
    // @hole-end L4.MulLimbCCorrect
  }

  lemma MulLimbCorrect(s: seq<nat>, d: nat)
    requires Valid(s) && d < BASE
    ensures Valid(MulLimb(s, d)) && ToNat(MulLimb(s, d)) == ToNat(s) * d
  {
    // @hole-begin L4.MulLimbCorrect
    MulLimbCCorrect(s, d, 0);
    // @hole-end L4.MulLimbCorrect
  }

  // Compiled loop form of MulLimb: the Dafny mirror of mul_limb.
  method {:isolate_assertions} MulLimbLoop(s: seq<nat>, d: nat) returns (r: seq<nat>)
    requires Valid(s) && d < BASE
    ensures r == MulLimb(s, d) && Valid(r) && ToNat(r) == ToNat(s) * d
  {
    r := [];
    var carry: nat := 0;
    var i := 0;
    // @hole-begin L4.MulLimbLoop
    assert s[0..] == s;
    // @hole-end L4.MulLimbLoop
    while i < |s|
      // @hole-begin L4.MulLimbLoop
      invariant 0 <= i <= |s|
      invariant r + MulLimbC(s[i..], d, carry) == MulLimb(s, d)
      // @hole-end L4.MulLimbLoop
      decreases |s| - i
    {
      // @hole-begin L4.MulLimbLoop
      MulNonneg(s[i], d);
      assert s[i..][1..] == s[i + 1..];
      // @hole-end L4.MulLimbLoop
      var t := s[i] * d + carry;
      r := r + [t % BASE];
      carry := t / BASE;
      i := i + 1;
    }
    if carry != 0 {
      r := r + [carry];
    }
    // @hole-begin L4.MulLimbLoop
    MulLimbCorrect(s, d);
    // @hole-end L4.MulLimbLoop
  }

  // Full multiplication: one MulLimb row per limb of b, shifted by one limb.
  function Mul(a: seq<nat>, b: seq<nat>): seq<nat>
    decreases |b|
  {
    if |b| == 0 then [] else Add(MulLimb(a, b[0]), [0] + Mul(a, b[1..]))
  }

  lemma MulCorrect(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(Mul(a, b)) && ToNat(Mul(a, b)) == ToNat(a) * ToNat(b)
    decreases |b|
  {
    // @hole-begin L4.MulCorrect
    if |b| == 0 {
      MulZero(ToNat(a), ToNat(b));
    } else {
      ValidTail(b);
      MulCorrect(a, b[1..]);
      MulLimbCorrect(a, b[0]);
      ToNatCons(0, Mul(a, b[1..]));
      ValidCons(0, Mul(a, b[1..]));
      AddCorrect(MulLimb(a, b[0]), [0] + Mul(a, b[1..]));
      DistribHorner(b[0], ToNat(b[1..]), ToNat(a));
      MulComm(ToNat(a), ToNat(b));
      MulComm(ToNat(a), b[0]);
      MulComm(ToNat(a), ToNat(b[1..]));
    }
    // @hole-end L4.MulCorrect
  }
}

// The frozen statement layer: what any BigNat implementation must provide.
abstract module {:disableNonlinearArithmetic} BigNatSpec {
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

// The concrete limb implementation refines the frozen spec.
module {:disableNonlinearArithmetic} BigNatLimbs refines BigNatSpec {
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
    // @hole-begin Spec.ZeroCorrect
    // @hole-end Spec.ZeroCorrect
  }

  lemma FromNatCorrect(n: nat)
  {
    // @hole-begin Spec.FromNatCorrect
    L2.FromNatCorrect(n);
    // @hole-end Spec.FromNatCorrect
  }

  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    // @hole-begin Spec.AddCorrect
    L4.AddCorrect(a, b);
    // @hole-end Spec.AddCorrect
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    // @hole-begin Spec.CmpCorrect
    L3.CmpCorrect(a, b);
    // @hole-end Spec.CmpCorrect
  }
}
