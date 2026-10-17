// Reference Solution (author-only): research/q18_statements.dfy as a learner commits it at H2's step 2 (Q18.H2d):
// the Dafny agent file with the reference statements, witnesses and test rows, every statement a stub. The
// statement route of `firsttry.sh Q18 --empty-body` checks the reference delivery against it (the user's decision D9).
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
# Q18 The capstone, Dafny mirror — rungs 14a and 14b (`/contract Q18`)

What this file ships: a module that imports the given layers L1–L7 and two
standard-library modules, and six empty sections: STATEMENTS, WITNESSES,
TESTS, REVIEW, HELPERS and, at the end, AUDIT. It is green with no hole:
`scripts/vcheck` reports it verified, with 0 tool-counted holes and no
error. Check command:

    scripts/vcheck dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy

The file is outside every build: no unit includes it. It is the Dafny
mirror of the capstone crate `bignat` (verus/q/q18_practice_iiic): the same
operations, stated and proved again, compiled to Python by
`scripts/vcheck --test` for the differential check against the Verus crate.

The capstone round (the chapter's H2) runs through this file and
verus/q/q18_practice_iiic/src/agent.rs:
1. Your blueprint (paper/Q18_answers.tex, B1) is graded first, at least 3 on
   every dimension, before you write any statement.
2. Your statements (H2d here, H2v in agent.rs): in STATEMENTS, each new
   operation the section names, as a compiled method with no body (its
   signature, its `requires`, one `ensures` clause), and the round-trip
   statement as a lemma with no body. In WITNESSES, a method that calls each
   operation on concrete arguments. In TESTS, the sample rows of the
   differential check: `{:test}` methods that call the operations on the
   same rows as agent.rs's tests. Run the check command: green, one hole per
   statement. Copy this file to research/q18_statements.dfy (and agent.rs to
   research/q18_statements.rs) and commit all four: the snapshot every later
   run is checked against.
3. The statement-only review (A1dv): in a FRESH session, `/contract Q18`, and
   name THIS file when asked which run it is; the CONTRACT above is the
   review's. Then decide, by hand, which findings change a statement; if any
   does, re-commit the statement files.
4. The co-developer (A2dv): in a FRESH session, `/contract Q18`, and name
   verus/q/q18_practice_iiic/src/agent.rs when asked; its CONTRACT is the
   co-developer's, over both files. You may only hint, in the chat.
5. Fill AUDIT, then the adversarial plant and the ship step (the chapter).
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

  method DivWord(a: seq<nat>, w: nat) returns (q: seq<nat>, rem: nat)
    requires Valid(a) && 0 < w < BASE
    ensures Valid(q) && rem < w && ToNat(a) == ToNat(q) * w + rem

  method ToDecimal(a: seq<nat>) returns (d: seq<nat>)
    requires Valid(a)
    ensures DecWf(d) && DecToNat(d) == ToNat(a)

  method FromDecimal(d: seq<nat>) returns (r: seq<nat>)
    requires DecDigits(d)
    ensures Valid(r) && ToNat(r) == DecToNat(d)

  // The round trip: canonical decimal chunks are fixed by their value, so
  // ToDecimal gives back the very chunks FromDecimal read.
  lemma DecimalRoundTrip(d1: seq<nat>, d2: seq<nat>)
    requires DecWf(d1) && DecWf(d2) && DecToNat(d1) == DecToNat(d2)
    ensures d1 == d2
    decreases |d1|

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

}

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
