/* CONTRACT
goal: review every statement of the STATEMENTS sections of this file and of verus/q/q18_practice_iiic/src/agent.rs for vacuity, weakness and over-strength, and record each finding under REVIEW; change no statement
allowed-files:
  - dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy
  - verus/q/q18_practice_iiic/src/agent.rs
acceptance:
  - re-verify after every edit with `scripts/vcheck <the edited file>`; never stack unverified edits
  - `scripts/specfreeze --against research/q18_statements.dfy dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` reports no change
  - `scripts/specfreeze --against research/q18_statements.rs verus/q/q18_practice_iiic/src/agent.rs` reports no change
  - every finding is a lemma (Dafny) or proof fn (Verus) under its file's REVIEW section that verifies: a witness that a statement can be met, or a counterexample that it is false, too weak or too strong on concrete values, each with a one-line comment naming the statement and the finding
  - `git diff` against the committed statements changes only the two REVIEW sections
*/
/*!
# Q18 The capstone, Dafny mirror — rungs 14a and 14b (Reference Solution)

Hole-free reference for `dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy`
(author-only): the proof that the round's contracts are satisfiable as
stated. The six sections are empty, as shipped; the closing reference section,
inside the module, holds a reference set of statements (each method's header
is what a learner commits in STATEMENTS, as a method with no body; the round
trip as a lemma with no body), witnesses and tests for them, and the reference
delivery: the bodies and the helpers a co-developer puts under HELPERS.
Committed with no bodies (Solutions/plans/Q18-code-notes.md §6), the
statements leave the file green with 5 holes, the witnesses verifying; the
delivery below passes every acceptance line of both CONTRACTs: `vcheck --gate`
with 0 holes, `specfreeze --against` the statements with no finding, `vaudit`
with no finding, and `vcheck --test` 7/7 on the same sample rows as the Verus
crate's tests. Stable on seeds 1-3 under both bundled solvers.
*/
module {:disableNonlinearArithmetic} Q18_AgentCapstone {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat
  import opened QG_L7_BigNat
  import opened Std.Arithmetic.Mul
  import DivMod = Std.Arithmetic.DivMod

  // item: Q18.A1dv S12

  // item: Q18.H2d S12
  // uses: witness
  // ### STATEMENTS (learner-owned: your statements). The capstone's new
  //    operations on valid limb sequences (`seq<nat>`, least significant limb
  //    first), each a compiled method with no body and one `ensures` clause:
  //    - multiplication of two values (state it against L7's `Times`, or
  //      against the values);
  //    - division by one limb `w > 0`: the quotient and the remainder;
  //    - `ToDecimal`: the value as decimal chunks, each below 10^19, least
  //      significant chunk first (by repeated division by 10^19);
  //    - `FromDecimal`: back from such chunks (by Horner steps of `MulLimb`
  //      and `AddLimb`);
  //    and one lemma with no body: the round trip, decimal chunks and back.
  //    Name your decimal chunk value as a function here too; it is part of
  //    your statements.

  // ### WITNESSES (learner-owned: a method that calls each operation on
  //    concrete arguments and asserts what its statement gives).

  // ### TESTS (learner-owned: the differential check's sample rows, as
  //    `{:test}` methods with `expect` lines; agent.rs's tests use the same
  //    rows).

  // ### REVIEW (the reviewer's, run A1dv: one lemma per finding).

  // ### HELPERS (the co-developer's, run A2dv: helper functions and lemmas).

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // A reference set of statements (H2d) and the reference delivery (A2dv):
  // the decimal chunk value and its predicates, the four operations as
  // compiled methods with one `ensures` each, the round trip as a lemma, the
  // witnesses, the tests over the sample rows the Verus crate's tests use, and
  // the bodies with their helpers (Solutions/plans/Q18-code-notes.md §6).

  // The decimal chunk base, 10^19 (the largest power of ten below BASE).
  const DEC: nat := 10000000000000000000

  // The value of decimal chunks, least significant chunk first.
  function DecToNat(d: seq<nat>): nat
    decreases |d|
  {
    if |d| == 0 then 0 else d[0] + DEC * DecToNat(d[1..])
  }

  // Every chunk is a decimal digit in base 10^19.
  predicate DecDigits(d: seq<nat>)
  {
    forall i | 0 <= i < |d| :: d[i] < DEC
  }

  // Decimal digits with no zero chunk on top (zero is no chunk at all).
  predicate DecWf(d: seq<nat>)
  {
    DecDigits(d) && (|d| == 0 || d[|d| - 1] != 0)
  }

  method Multiply(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    requires Valid(a) && Valid(b)
    ensures Valid(r) && ToNat(r) == ToNat(a) * ToNat(b)
  {
    r := [];
    var j := |b|;
    assert b[|b|..] == [];
    LemmaMulBasics(ToNat(a));
    while j > 0
      invariant 0 <= j <= |b|
      invariant Valid(r) && ToNat(r) == ToNat(a) * ToNat(b[j..])
      decreases j
    {
      j := j - 1;
      ValidTail(b[j..]);
      MulStep(a, b, j, r);
      r := Add(Shift(r, 1), MulLimb(a, b[j]));
    }
    assert b[0..] == b;
  }

  method DivWord(a: seq<nat>, w: nat) returns (q: seq<nat>, rem: nat)
    requires Valid(a) && 0 < w < BASE
    ensures Valid(q) && rem < w && ToNat(a) == ToNat(q) * w + rem
  {
    q := [];
    rem := 0;
    var j := |a|;
    assert a[|a|..] == [];
    LemmaMulBasics(w);
    while j > 0
      invariant 0 <= j <= |a|
      invariant Valid(q) && rem < w && ToNat(a[j..]) == ToNat(q) * w + rem
      decreases j
    {
      j := j - 1;
      ValidTail(a[j..]);
      assert a[j..][0] == a[j];
      var cur := RowValue(rem, a[j]);
      DivStep(rem, a[j], w, cur);
      var qd: nat, r2: nat := cur / w, cur % w;
      DivInvariantStep(a, j, q, w, rem, qd, r2, cur);
      q, rem := [qd] + q, r2;
    }
    assert a[0..] == a;
  }

  method ToDecimal(a: seq<nat>) returns (d: seq<nat>)
    requires Valid(a)
    ensures DecWf(d) && DecToNat(d) == ToNat(a)
  {
    var x := Normalize(a);
    NormalizeToNat(a);
    NormalizeCanonical(a);
    d := [];
    LemmaMulBasics(ToNat(x));
    while |x| > 0
      invariant Canonical(x)
      invariant DecDigits(d) && (|x| == 0 ==> |d| == 0 || d[|d| - 1] != 0)
      invariant DecToNat(d) + DecPow(|d|) * ToNat(x) == ToNat(a)
      decreases ToNat(x)
    {
      CanonicalPositive(x);
      var q, c := DivWord(x, DEC);
      NormalizeToNat(q);
      NormalizeCanonical(q);
      DecPush(d, c);
      ToDecimalStep(DecPow(|d|), c, ToNat(q), ToNat(x));
      CanonicalZero(Normalize(q));
      x := Normalize(q);
      d := d + [c];
    }
    LemmaMulBasics(DecPow(|d|));
  }

  method FromDecimal(d: seq<nat>) returns (r: seq<nat>)
    requires DecDigits(d)
    ensures Valid(r) && ToNat(r) == DecToNat(d)
  {
    r := [];
    var j := |d|;
    assert d[|d|..] == [];
    while j > 0
      invariant 0 <= j <= |d|
      invariant Valid(r) && ToNat(r) == DecToNat(d[j..])
      decreases j
    {
      j := j - 1;
      MulLimbCorrect(r, DEC);
      AddLimbCorrect(MulLimb(r, DEC), d[j]);
      DecSuffixStep(d, j);
      LemmaMulIsCommutative(ToNat(r), DEC);
      r := AddLimb(MulLimb(r, DEC), d[j]);
    }
    assert d[0..] == d;
  }

  // The round trip: canonical decimal chunks are fixed by their value, so
  // ToDecimal gives back the very chunks FromDecimal read.
  lemma DecimalRoundTrip(d1: seq<nat>, d2: seq<nat>)
    requires DecWf(d1) && DecWf(d2) && DecToNat(d1) == DecToNat(d2)
    ensures d1 == d2
    decreases |d1|
  {
    if |d1| == 0 || |d2| == 0 {
      DecWfPositive(d1);
      DecWfPositive(d2);
    } else {
      var t1, t2 := d1[1..], d2[1..];
      LemmaMulIsCommutative(DEC, DecToNat(t1));
      LemmaMulIsCommutative(DEC, DecToNat(t2));
      DivMod.LemmaFundamentalDivModConverse(DecToNat(d1), DEC, DecToNat(t1), d1[0]);
      DivMod.LemmaFundamentalDivModConverse(DecToNat(d2), DEC, DecToNat(t2), d2[0]);
      DecTailWf(d1);
      DecTailWf(d2);
      DecimalRoundTrip(t1, t2);
      assert d1 == [d1[0]] + t1;
      assert d2 == [d2[0]] + t2;
    }
  }

  // The witnesses: each operation called on concrete arguments.
  method CapstoneWitnesses()
  {
    ToNatSingleton(6);
    ToNatSingleton(7);
    ToNatSingleton(43);
    var p := Multiply([6], [7]);
    assert ToNat(p) == 42;
    var q, r := DivWord([43], 6);
    assert ToNat(q) * 6 + r == 43 && r < 6;
    var d := ToDecimal(p);
    assert DecToNat(d) == 42;
    var back := FromDecimal(d);
    assert ToNat(back) == 42;
  }

  // The reference TESTS: the differential check's sample rows (the Verus
  // crate's tests use the same rows).
  method {:test} Row1TimesSmall()
  {
    var r := Multiply([6], [7]);
    expect r == [42];
  }

  method {:test} Row2TimesTopWords()
  {
    var m: nat := BASE - 1;
    var r := Multiply([m], [m]);
    expect r == [1, 18446744073709551614];
  }

  method {:test} Row3DivWordSmall()
  {
    var q, r := DivWord([43], 6);
    expect Normalize(q) == [7] && r == 1;
  }

  method {:test} Row4DivWordByDecBase()
  {
    var q, r := DivWord([0, 1], DEC);
    expect Normalize(q) == [1] && r == 8446744073709551616;
  }

  method {:test} Row5ToDecimalBase()
  {
    var d := ToDecimal([0, 1]);
    expect d == [8446744073709551616, 1];
  }

  method {:test} Row6FromDecimalBase()
  {
    var r := FromDecimal([8446744073709551616, 1]);
    expect r == [0, 1];
  }

  method {:test} Row7ToDecimalZero()
  {
    var d := ToDecimal([]);
    expect d == [];
  }

  // --- the delivery's helpers ---------------------------------------------

  // DEC to the power k.
  function DecPow(k: nat): nat
    decreases k
  {
    if k == 0 then 1 else DEC * DecPow(k - 1)
  }

  // One Horner row of a division: the remainder times BASE plus a limb.
  function RowValue(rem: nat, x: nat): nat
  {
    rem * BASE + x
  }

  lemma MulStep(a: seq<nat>, b: seq<nat>, j: nat, r: seq<nat>)
    requires Valid(a) && Valid(b) && j < |b| && Valid(r)
    requires ToNat(r) == ToNat(a) * ToNat(b[j + 1..])
    ensures Valid(Add(Shift(r, 1), MulLimb(a, b[j])))
    ensures ToNat(Add(Shift(r, 1), MulLimb(a, b[j]))) == ToNat(a) * ToNat(b[j..])
  {
    assert seq(1, _ => 0) == [0];
    assert Shift(r, 1) == [0] + r;
    ToNatCons(0, r);
    ValidCons(0, r);
    assert b[j..] == [b[j]] + b[j + 1..];
    ToNatCons(b[j], b[j + 1..]);
    ValidTail(b[j..]);
    MulLimbCorrect(a, b[j]);
    AddCorrect(Shift(r, 1), MulLimb(a, b[j]));
    var av, h, t1 := ToNat(a), b[j], ToNat(b[j + 1..]);
    LemmaMulIsDistributiveAdd(av, h, BASE * t1);
    LemmaMulIsAssociative(av, BASE, t1);
    LemmaMulIsCommutative(av, BASE);
    LemmaMulIsAssociative(BASE, av, t1);
    LemmaMulIsCommutative(av, h);
  }

  lemma DivStep(rem: nat, x: nat, w: nat, cur: nat)
    requires 0 < w < BASE && rem < w && x < BASE && cur == RowValue(rem, x)
    ensures 0 <= cur / w < BASE && 0 <= cur % w < w && cur == (cur / w) * w + cur % w
  {
    DivMod.LemmaDivPosIsPos(cur, w);
    DivMod.LemmaFundamentalDivMod(cur, w);
    LemmaMulIsCommutative(w, cur / w);
    DivMod.LemmaModPosBound(cur, w);
    LemmaMulInequality(rem, w - 1, BASE);
    LemmaMulIsDistributiveSub(BASE, w, 1);
    LemmaMulIsCommutative(BASE, w);
    LemmaMulIsCommutative(BASE, w - 1);
    LemmaMulBasics(BASE);
    assert cur < w * BASE;
    DivMod.LemmaMultiplyDivideLt(cur, w, BASE);
  }

  lemma DivInvariantStep(a: seq<nat>, j: nat, q: seq<nat>, w: nat, rem: nat, qd: nat,
                         r2: nat, cur: nat)
    requires Valid(a) && j < |a| && Valid(q) && 0 < w < BASE && rem < w
    requires ToNat(a[j + 1..]) == ToNat(q) * w + rem
    requires cur == RowValue(rem, a[j]) && qd < BASE && r2 < w && cur == qd * w + r2
    ensures Valid([qd] + q) && ToNat(a[j..]) == ToNat([qd] + q) * w + r2
  {
    ValidCons(qd, q);
    ToNatCons(qd, q);
    assert a[j..] == [a[j]] + a[j + 1..];
    ToNatCons(a[j], a[j + 1..]);
    var qs := ToNat(q);
    LemmaMulIsDistributiveAdd(BASE, qs * w, rem);
    LemmaMulIsAssociative(BASE, qs, w);
    LemmaMulIsDistributiveAddOtherWay(w, qd, BASE * qs);
    LemmaMulIsCommutative(rem, BASE);
  }

  lemma CanonicalPositive(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures ToNat(s) > 0
  {
    CanonicalLower(s);
    PowPositive(|s| - 1);
  }

  lemma CanonicalZero(s: seq<nat>)
    requires Canonical(s)
    ensures |s| == 0 <==> ToNat(s) == 0
  {
    if |s| > 0 {
      CanonicalPositive(s);
    }
  }

  lemma DecPush(d: seq<nat>, c: nat)
    ensures DecToNat(d + [c]) == DecToNat(d) + DecPow(|d|) * c
    decreases |d|
  {
    if |d| == 0 {
      assert d + [c] == [c];
      assert [c][1..] == [];
      LemmaMulBasics(c);
    } else {
      assert (d + [c])[1..] == d[1..] + [c];
      DecPush(d[1..], c);
      var t, w := DecToNat(d[1..]), DecPow(|d| - 1);
      LemmaMulIsDistributiveAdd(DEC, t, w * c);
      LemmaMulIsAssociative(DEC, w, c);
    }
  }

  lemma ToDecimalStep(w: nat, c: nat, qv: nat, xv: nat)
    requires xv == qv * DEC + c && xv > 0 && c < DEC
    ensures w * c + (DEC * w) * qv == w * xv
    ensures qv < xv
    ensures qv == 0 ==> c > 0
  {
    LemmaMulIsDistributiveAdd(w, c, qv * DEC);
    LemmaMulIsAssociative(w, qv, DEC);
    LemmaMulIsCommutative(w * qv, DEC);
    LemmaMulIsAssociative(DEC, w, qv);
    LemmaMulIsCommutative(DEC, w);
    LemmaMulIsCommutative(qv, DEC);
    if qv > 0 {
      LemmaMulIncreases(DEC, qv);
    } else {
      LemmaMulBasics(DEC);
    }
  }

  lemma DecSuffixStep(d: seq<nat>, j: nat)
    requires j < |d|
    ensures DecToNat(d[j..]) == d[j] + DEC * DecToNat(d[j + 1..])
  {
    assert d[j..][1..] == d[j + 1..];
  }

  lemma DecTailWf(d: seq<nat>)
    requires DecWf(d) && |d| > 0
    ensures DecWf(d[1..])
  {
  }

  lemma DecWfPositive(d: seq<nat>)
    requires DecWf(d)
    ensures |d| > 0 ==> DecToNat(d) > 0
    decreases |d|
  {
    if |d| > 1 {
      DecTailWf(d);
      DecWfPositive(d[1..]);
      LemmaMulStrictlyPositive(DEC, DecToNat(d[1..]));
    } else if |d| == 1 {
      assert d[1..] == [];
      LemmaMulBasics(DEC);
    }
  }
}

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
