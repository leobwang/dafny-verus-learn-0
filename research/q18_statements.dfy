// research/q18_statements.dfy — the capstone's committed statements, Dafny mirror (Q18; shipped as this form):
// the agent file dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy as shipped. At H2's step 2 you overwrite
// it with your copy of the agent file (statements, witnesses, tests) and commit: every later run checks against it.
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
}

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
