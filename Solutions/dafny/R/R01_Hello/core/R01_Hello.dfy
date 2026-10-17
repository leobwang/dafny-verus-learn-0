/*! R01 — Reference Solution (author-only).
Complete, silent twin; declarations and item order match the learner source.
All prediction switches and supplied checks are enabled. */
module R01_Hello {
  newtype U32 = x: int | 0 <= x < 0x1_0000_0000

  function CountChar(s: seq<char>, c: char): nat
    decreases |s|
  {
    if |s| == 0 then 0 else (if s[0] == c then 1 else 0) + CountChar(s[1..], c)
  }

  // Prediction block: record both verdict lines before running their scenarios.
  // item: R01.P1dv verdict
  /** Midpoint: verify `m := (lo + hi) / 2` under `requires lo <= hi` and
      `ensures lo <= m <= hi`, first with Dafny int, then Dafny U32, then Verus u32.
      Answer form: D-int:<v> D-u32:<v> V:<v>, where v is ok, fail, timeout or err:<stage>.
      The Rust body is `(lo + hi) / 2`; its specification uses mathematical addition. */
  // CHECK P1dv

  // item: R01.P2dv verdict
  /** HalveEven(n) requires n % 2 == 0 and ensures twice its result is n; body n / 2.
      Verify it with a test calling HalveEven(7) and checking that twice the result is 7:
      Dafny @Test method; Rust #[test] outside verus!. Then run the compiled tests.
      Answer form: D:<v>,<t> V:<v>,<t>, where v is as above and t is passed, failed or not-run.
      The full scenario files stay behind their prediction switch in the chapter. */
  // CHECK P2dv

  // item: R01.T1d
  // uses: ensures, assert, lemma-call
  // pair: R01.T1v
  /** Closed-book census. Close BOTH holes using CountChar's definition. The proof
      states the count in a two-character sequence; the method counts the first two
      entries of any sequence. Keep their contracts; then record the first try. */
  lemma CountCharPair(d: char, e: char, c: char)
    ensures CountChar([d, e], c) == (if d == c then 1 else 0) + (if e == c then 1 else 0)
  {
    // @hole-begin R01.T1d
    assert [d, e][1..] == [e];
    assert [e][1..] == [];
    assert CountChar([], c) == 0;
    assert CountChar([e], c) == (if e == c then 1 else 0);
    // @hole-end R01.T1d
  }

  method CountFirstTwo(s: seq<char>, c: char) returns (n: nat)
    requires |s| >= 2
    ensures n == CountChar(s[..2], c)
  {
    CountCharPair(s[0], s[1], c);
    assert s[..2] == [s[0], s[1]];
    n := (if s[0] == c then 1 else 0) + (if s[1] == c then 1 else 0);
  }
  // Reference checks (enabled):
  // reference-only: enabled shipped check
  method CensusCheck() { CountCharPair('a', 'b', 'a'); assert ['a', 'b'][..2] == ['a', 'b']; var n := CountFirstTwo(['a', 'b'], 'a'); assert n == 1; }

  // item: R01.W1d
  /** A method exports its postcondition to callers. The precondition makes the last
      index legal. Read the signature before tracing its body. */
  method LastChar(s: seq<char>) returns (c: char)
    requires |s| > 0
    ensures c == s[|s| - 1]
  {
    c := s[|s| - 1];
  }

  // item: R01.W2d
  /** A proof follows the recursive definition, recording the available facts after
      each step. The recursive call contributes its postcondition on the shorter input. */
  lemma CountCharBound(s: seq<char>, c: char)
    ensures CountChar(s, c) <= |s|
    decreases |s|
  {
    if |s| > 0 {
      assert |s[1..]| == |s| - 1;
      CountCharBound(s[1..], c);
      assert CountChar(s[1..], c) <= |s[1..]|;
      assert CountChar(s, c) <= 1 + CountChar(s[1..], c);
    }
  }

  // item: R01.C1d write:ensures
  // EXPECT: card-c1d.dfy.specimen fails; read only after predictions are recorded.
  method KeepChar(c: char) returns (r: char)
    ensures r == c
  { r := c; }

  // item: R01.C2d write:assert
  // EXPECT: card-c2d.dfy.specimen fails.
  lemma EmptyPrefix(s: seq<char>)
    ensures [] + s == s
  { assert [] + s == s; }

  // item: R01.C3d write:lemma-call
  // EXPECT: card-c3d.dfy.specimen fails.
  method CountWithinLength(s: seq<char>, c: char) returns (n: nat)
    ensures n <= |s|
  {
    CountCharBound(s, c);
    n := CountChar(s, c);
  }

  // item: R01.C4dv recognise:requires
  // A caller proves requires; the body may assume it. See LastChar, and H3's callers.
  // item: R01.C5dv recognise:decreases
  // CountChar and CountCharBound state the smaller input explicitly in both languages.
  // item: R01.C6dv recognise:function
  // Dafny function is compiled when its context permits; Rust spec fn is ghost specification.
  // item: R01.C7dv recognise:forall
  // Rosetta: forall i | 0 <= i < |s| :: s[i] == c
  //          forall|i: int| 0 <= i < s.len() ==> s[i] == c
  // These formulas have a bounded domain and describe every position in a sequence.

  // item: R01.H1d
  // uses: ensures
  // pair: R01.H1v
  /** Implement the mathematical midpoint of two ordered bounded values. Preserve both
      the interval guarantee and the exact-average guarantee. */
  method Midpoint(lo: U32, hi: U32) returns (m: U32)
    requires lo <= hi
    ensures lo <= m <= hi && m as int == (lo as int + hi as int) / 2
  {
    m := lo + (hi - lo) / 2;
  }
  // Reference checks (enabled):
  // reference-only: enabled shipped check
  method MidpointCheck() { var m := Midpoint(0xFFFF_FFFE, 0xFFFF_FFFF); assert m == 0xFFFF_FFFE; }

  // item: R01.H2d
  // uses: assert, lemma-call
  // pair: R01.H2v
  /** A character's count in a concatenation is the sum of its counts in the two parts.
      Write the induction yourself; the lemma's automatic induction is disabled. */
  lemma {:induction false} CountCharAppend(s: seq<char>, t: seq<char>, c: char)
    ensures CountChar(s + t, c) == CountChar(s, c) + CountChar(t, c)
    decreases |s|
  {
    // @hole-begin R01.H2d
    if |s| > 0 {
      assert (s + t)[1..] == s[1..] + t;
      CountCharAppend(s[1..], t, c);
    } else {
      assert s + t == t;
    }
    // @hole-end R01.H2d
  }
  // Reference checks (enabled):
  // reference-only: enabled shipped check
  lemma AppendCheck() { CountCharAppend(['x'], ['y', 'x'], 'x'); }

  // item: R01.H3d
  // uses: requires
  // pair: R01.H3v
  /** Keep the body and the mathematical result statement. Supply a requires clause
      that makes the body verify while preserving all THREE supplied callers below. */
  method MeanOfTwo(a: U32, b: U32) returns (m: U32)
    // @hole-begin R01.H3d
    requires a as int + b as int < 0x1_0000_0000
    // @hole-end R01.H3d
    ensures m as int == (a as int + b as int) / 2
  {
    m := (a + b) / 2;
  }
  method MeanZero() { var m := MeanOfTwo(0, 0); assert m == 0; }
  method MeanSmall() { var m := MeanOfTwo(4, 6); assert m == 5; }
  method MeanEdge() { var m := MeanOfTwo(0x7FFF_FFFF, 0x8000_0000); assert m == 0x7FFF_FFFF; }

  // item: R01.C8dv diverge:false-friends
  // Final cards: calc / assert / forall / old / decreases / ==>. Six paired demos
  // under specimens/R01/card-c8dv-<row>-<d|v>.*, linked in the chapter after predictions.
  // item: R01.C9dv diverge:r01-c9
  // Integer division: read the paired demo only after R01.P5d and R01.P6v are recorded.

  /* TRIAGE — before reading the chapter's debrief, classify each of the five captured
     cases in §6 by verdict and stage. State what the result licenses and what it does
     not. Write your own lines here; never infer zero holes from a green verdict.
     case 1: ...  case 2: ...  case 3: ...  case 4: ...  case 5: ...

     CALIBRATION
     Estimate / actual / correction, in your words: ...
     Record with scripts/firsttry.sh R01 --record.
  */
}
