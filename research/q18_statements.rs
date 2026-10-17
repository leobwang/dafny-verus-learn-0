// research/q18_statements.rs — the capstone's committed statements, Verus crate (Q18; shipped as this form):
// the agent file verus/q/q18_practice_iiic/src/agent.rs as shipped. At H2's step 2 you overwrite it with your
// copy of the agent file (statements, witnesses, tests) and commit: every later run checks against it.
/* CONTRACT
goal: implement and prove every statement of the STATEMENTS sections of this file and of dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy, following the graded blueprint in paper/Q18_answers.tex (B1), changing no statement
allowed-files:
  - verus/q/q18_practice_iiic/src/agent.rs
  - dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck <the edited file>`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q18_practice_iiic/src/agent.rs` exits 0 with zero tool-counted holes
  - `scripts/vcheck --gate dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` exits 0 with zero tool-counted holes
  - `scripts/specfreeze --against research/q18_statements.rs verus/q/q18_practice_iiic/src/agent.rs` reports no change
  - `scripts/specfreeze --against research/q18_statements.dfy dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` reports no change
  - `scripts/vaudit verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vaudit dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` report no finding
  - the differential check: `scripts/vcheck --test verus/q/q18_practice_iiic/src/agent.rs` and `scripts/vcheck --test dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy` run every test on the same sample rows, and every test passes
  - `git diff` against the committed statements changes only the bodies of the statements and the two HELPERS sections; every WITNESSES and TESTS line is unchanged
  - new helper fns, proof fns, functions and lemmas go only under HELPERS
*/
//! # Q18 The capstone, Verus half: the crate's proof work — rungs 14a and 14b (`/contract Q18`)
//!
//! What this file ships: the given layers L1–L7 (the base API `BigNatCore` among them)
//! and vstd's multiplication and division lemmas imported, and six empty sections:
//! STATEMENTS, WITNESSES, TESTS, REVIEW, HELPERS and, at the end, AUDIT. It is green with
//! no hole: `scripts/vcheck` reports it verified, with 0 tool-counted holes and no error.
//! Check command:
//!
//!     scripts/vcheck verus/q/q18_practice_iiic/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies. The capstone round's steps are
//! in the Dafny mirror's header (dafny/Q/Q18_PracticeIIIC/agent/Q18_AgentCapstone.dfy):
//! the statement-only review runs from that file's CONTRACT, the co-developer from THIS
//! file's CONTRACT (name this file when `/contract Q18` asks which run it is).
//!
//! Your statements here (H2v): in STATEMENTS, an extension trait of L7's `BigNatCore`
//! (`pub trait <YourName>: BigNatCore { … }`) with each new operation as a trait method
//! with its `requires` and `ensures`, any spec fns your statements name, and `impl
//! <YourName> for BigNat` with every method marked `#[verifier::external_body]` over the
//! body `unimplemented!()` (a stub: the co-developer writes the bodies); the round trip as
//! a proof fn whose body is one labelled `assume(false)`. In WITNESSES, a fn that calls
//! each operation on concrete arguments; in TESTS, `#[test]` fns over the same sample rows
//! as the Dafny mirror's tests. Then copy this file to research/q18_statements.rs and
//! commit (the Dafny header's step 2).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l7::*;

verus! {

// item: Q18.A2dv S12

// item: Q18.H2v S12
// uses: trait-spec, witness
// ### STATEMENTS (learner-owned: your extension trait of `BigNatCore`, its spec fns, and
//    its `impl` for `BigNat` as `external_body` stubs). The new operations:
//    - multiplication of two values;
//    - division by one word `w > 0`: the quotient and the remainder;
//    - `to_decimal`: the value as decimal chunks, each below 10^19, least significant
//      chunk first (by repeated division by 10^19);
//    - `from_decimal`: back from such chunks (by Horner steps of `mul_limb` and
//      `add_limb`);
//    and the round trip as a proof fn.

// ### WITNESSES (learner-owned: a fn that calls each operation on concrete arguments and
//    asserts what its statement gives).

// ### REVIEW (the reviewer's, run A1dv: one proof fn per finding).

// ### HELPERS (the co-developer's, run A2dv: helper fns and proof fns).

} // verus!

// ### TESTS (learner-owned: the differential check's sample rows, as `#[test]` fns over
//    the same rows as the Dafny mirror's tests; tests sit outside `verus!`).

// AUDIT (learner-owned; after the co-developer run)
//   each REVIEW finding: kept, changed a statement (which), or rejected (why):
//   the statement that cost the co-developer most, and why:
//   each helper's statement (does it assume what it should prove?):
