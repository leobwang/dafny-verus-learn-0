/* CONTRACT
goal: implement and prove every statement of the STATEMENTS section of this file, changing no statement
allowed-files:
  - verus/q/q08_internals_ii/src/agent.rs
acceptance:
  - re-verify after every edit with `scripts/vcheck verus/q/q08_internals_ii/src/agent.rs`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q08_internals_ii/src/agent.rs` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q08_statements.rs verus/q/q08_internals_ii/src/agent.rs` reports no change: no statement changed
  - `scripts/vaudit verus/q/q08_internals_ii/src/agent.rs` reports no finding
  - `git diff` against the committed statements changes only the bodies of the STATEMENTS functions (each `#[verifier::external_body]` line removed with its `unimplemented!()` body) and the HELPERS section
  - every WITNESSES check is unchanged and verifies
  - new helper functions and proof fns go only under HELPERS
*/
//! # Q08 Flagship, Verus half — spec-to-proof (`/contract Q08`)
//!
//! What this file ships: the given layers L1–L4 and vstd's multiplication and division
//! lemmas imported, and three empty sections, STATEMENTS, WITNESSES and HELPERS. It is
//! green with no hole: `scripts/vcheck` reports it verified, with 0 tool-counted holes and
//! no error. Check command:
//!
//!     scripts/vcheck verus/q/q08_internals_ii/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies.
//!
//! Before the run (your statements; this is your half of the work):
//! 1. In STATEMENTS, state each operation the section names as an exec fn with its
//!    `requires` and `ensures`, marked `#[verifier::external_body]` over the body
//!    `unimplemented!()` (a stub: the contractor writes the body).
//! 2. In WITNESSES, write a fn that calls each operation on concrete arguments, so that
//!    every `requires` is shown satisfiable and every statement meaningful on an input
//!    that is not trivial (assert what the statement gives you).
//! 3. Run the check command: the file is green, with one hole per statement.
//! 4. Copy the file to research/q08_statements.rs, the statement snapshot the contract's
//!    freeze check compares against, and commit both (`git commit`), so that the
//!    contract's `git diff` compares the run with your statements.
//!
//! Learner follow-up (after the contractor delivers; THIS is the exercise):
//! 1. In a FRESH session, run /contract Q08 on this file (after the Dafny file's run).
//! 2. Audit the delivery: the freeze check (`scripts/specfreeze --against
//!    research/q08_statements.rs` on this file); the diff's scope (the stubs' bodies and
//!    HELPERS only); each helper's statement (does a helper assume what it should prove?);
//!    your witnesses (unchanged and verifying); and the transcript (did the contractor ask
//!    to change a statement? did it stop and report a statement it could not prove?).
//! 3. Write in AUDIT (the block at the end) which statement cost the contractor most, and
//!    why.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l4::*;

verus! {

// item: Q08.A1v S6

// ### STATEMENTS (learner-owned: your statements, each an `external_body` stub). Two
//    operations on canonical BigNats (L1's `BigNat`, `wf`, `to_nat`):
//    - the shift left by `k` limbs;
//    - the limbs above the low `k` (the part above a split at `k` limbs).

// ### WITNESSES (learner-owned: your checks that the statements can be met and say
//    something).

// ### HELPERS (the contractor's: helper fns and proof fns, if any).

} // verus!

// AUDIT (learner-owned; after the contract run)
//   the statement that cost the contractor most, and why:
//   each helper's statement (does it assume what it should prove?):
