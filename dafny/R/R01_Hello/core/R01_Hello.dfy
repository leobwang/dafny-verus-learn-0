/*!
# R01 — Hello, two verifiers (exercises)

Standalone R track; no given layer and no earlier exercise is imported.
The other half is verus/r/r01_hello/src/lib.rs.

Commit predictions first: fill slots/R01.slots, the three prediction specimens
and dafny/checks/R01_checks.dfy, then run scripts/firsttry.sh R01 --check.
Do not open card demos, plans, CI logs or later chapter answers first.
The census T1 is closed book before reading the worked examples.
Each hole H1–H3 has a prompt with a guiding question and two hints below it.

Five holes ship here: two in T1d, and H1d–H3d; Verus holds the other five.
There are six predictions and two test-out items across the pair.
A typed placeholder counts as a hole even when verification is green.
Done: scripts/vcheck --gate dafny/R/R01_Hello/core exits 0 with zero holes;
scripts/vaudit dafny/R/R01_Hello/core reports zero findings;
scripts/specfreeze --check R01 and scripts/firsttry.sh R01 --report --strict pass.
Replace only the requested bodies/annotations. Keep every supplied contract and caller.
Stuck for 20 minutes? /tutor R01. The chapter explains the three tool loops.
*/
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
  // SLOT: CHECK P1dv

  // item: R01.P2dv verdict
  /** HalveEven(n) requires n % 2 == 0 and ensures twice its result is n; body n / 2.
      Verify it with a test calling HalveEven(7) and checking that twice the result is 7:
      Dafny @Test method; Rust #[test] outside verus!. Then run the compiled tests.
      Answer form: D:<v>,<t> V:<v>,<t>, where v is as above and t is passed, failed or not-run.
      The full scenario files stay behind their prediction switch in the chapter. */
  // SLOT: CHECK P2dv

  // item: R01.T1d
  // uses: ensures, assert, lemma-call
  // pair: R01.T1v
  /** Closed-book census. Close BOTH holes using CountChar's definition. The proof
      states the count in a two-character sequence; the method counts the first two
      entries of any sequence. Keep their contracts; then record the first try. */
  lemma CountCharPair(d: char, e: char, c: char)
    ensures CountChar([d, e], c) == (if d == c then 1 else 0) + (if e == c then 1 else 0)
  // HOLE: write the proof body.

  method CountFirstTwo(s: seq<char>, c: char) returns (n: nat)
    requires |s| >= 2
    ensures n == CountChar(s[..2], c)
  {
    assume false;  // HOLE: replace this line with the implementation
  }
  // Uncomment as you go:
  // method CensusCheck()
  // {
  //   CountCharPair('a', 'b', 'a');
  //   assert ['a', 'b'][..2] == ['a', 'b'];
  //   var n := CountFirstTwo(['a', 'b'], 'a');
  //   assert n == 1;
  // }

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
  {
    r := c;
  }

  // item: R01.C2d write:assert
  // EXPECT: card-c2d.dfy.specimen fails.
  lemma EmptyPrefix(s: seq<char>)
    ensures [] + s == s
  {
    assert [] + s == s;
  }

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

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: R01.H1d
  // uses: ensures
  // pair: R01.H1v
  /** **H1.** Implement the midpoint of two ordered bounded values, keeping both
      the interval clause and the exact-average clause. Which operations does
      your body perform on `U32` values, and what must be true of each result
      for every call the precondition admits? */
  method Midpoint(lo: U32, hi: U32) returns (m: U32)
    requires lo <= hi
    ensures lo <= m <= hi && m as int == (lo as int + hi as int) / 2
  {
    assume false;  // HOLE: implement the midpoint
  }
  // Hint(1): every intermediate value of the body must be a U32, not only the result.
  // Hint(2): the precondition `lo <= hi` is the one given fact the body can spend:
  //    which subtraction does it make legal?
  // Uncomment as you go:
  // method MidpointCheck()
  // {
  //   var m := Midpoint(0xFFFF_FFFE, 0xFFFF_FFFF);
  //   assert m == 0xFFFF_FFFE;
  // }

  // item: R01.H2d
  // uses: assert, lemma-call
  // pair: R01.H2v
  /** **H2.** A character's count in a concatenation is the sum of its counts in
      the two parts. Prove it by recursion on `s`, the way W2 recurses (the lever
      `{:induction false}` keeps Dafny from finding the recursive call for you).
      What is `s + t` once its first element is dropped, and which call of this
      lemma then supplies the rest of the sum? */
  lemma {:induction false} CountCharAppend(s: seq<char>, t: seq<char>, c: char)
    ensures CountChar(s + t, c) == CountChar(s, c) + CountChar(t, c)
    decreases |s|
  // HOLE: write the proof body.
  // Hint(1): split on whether `s` is empty; CountChar's definition does the same.
  // Hint(2): a call of this lemma on a shorter `s` is the hypothesis (W2's call);
  //    the verifier also needs the slice fact that connects `s + t` to that call.
  // Uncomment as you go:
  // lemma AppendCheck()
  // {
  //   CountCharAppend(['x'], ['y', 'x'], 'x');
  // }

  // item: R01.H3d
  // uses: requires
  // pair: R01.H3v
  /** **H3.** Keep the body and the result clause; write the `requires` clause
      that makes `(a + b) / 2` verify while all three given callers below still
      verify. Which operation of the body owes a range fact, and which caller
      rejects a clause that bounds each argument on its own? */
  method MeanOfTwo(a: U32, b: U32) returns (m: U32)
    // HOLE: add a requires clause here; do not change the body or callers.
    ensures m as int == (a as int + b as int) / 2
  {
    assume false;  // HOLE: remove after supplying the missing precondition
    m := (a + b) / 2;
  }
  // Hint(1): the failing obligation is the addition's; read its diagnostic first.
  // Hint(2): run the three callers after each candidate clause: `MeanEdge`
  //    rejects any clause that is stronger than the addition needs.
  method MeanZero()
  {
    var m := MeanOfTwo(0, 0);
    assert m == 0;
  }
  method MeanSmall()
  {
    var m := MeanOfTwo(4, 6);
    assert m == 5;
  }
  method MeanEdge()
  {
    var m := MeanOfTwo(0x7FFF_FFFF, 0x8000_0000);
    assert m == 0x7FFF_FFFF;
  }

  // item: R01.C8dv diverge:false-friends
  // Final cards: calc / assert / forall / old / decreases / ==>. Six paired demos
  // under specimens/R01/card-c8dv-<row>-<d|v>.*, linked in the chapter after predictions.
  // item: R01.C9dv diverge:r01-c9
  // Integer division: read the paired demo only after R01.P5d and R01.P6v are recorded.

  /* TRIAGE — before reading the chapter's debrief, classify each of the five captured
     cases in §7 by verdict and stage. State what the result licenses and what it does
     not. Write your own lines here; never infer zero holes from a green verdict.
     case 1: ...
     case 2: ...
     case 3: ...
     case 4: ...
     case 5: ...

     CALIBRATION
     Estimate / actual / correction, in your words: ...
     Record with scripts/firsttry.sh R01 --record.
  */
}
