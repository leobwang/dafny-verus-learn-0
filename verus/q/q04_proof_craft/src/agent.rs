/* CONTRACT
goal: close the goals lemma_pow_of_pow, lemma_low_limb_of_power and lemma_pow_mod_base, each with vstd library lemma calls only
allowed-files:
  - verus/q/q04_proof_craft/src/agent.rs
acceptance:
  - `scripts/vcheck --gate verus/q/q04_proof_craft/src/agent.rs` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `git diff` shows only the three goals' bodies: each hole line is replaced by library calls, and no other line changes (no signature, `requires`, `ensures`, doc comment or `use` line, no declaration added or removed)
  - each body holds only `vstd` library lemma calls with their arguments, each call on its own line followed by `// found-by: <rung>`, where `<rung>` is one of `ide`, `grep`, `docs`, `llm`, `memory`: no proof fn of your own, no `assert`, `calc!`, `broadcast use` or other statement
  - re-verify after every edit with `scripts/vcheck verus/q/q04_proof_craft/src/agent.rs`; never stack unverified edits
  - `scripts/vaudit --compare expected/q04_proof_craft_agent.audit verus/q/q04_proof_craft/src/agent.rs` reports no difference (an empty report: no finding)
*/
//! # Q04 Retriever race, Verus half — retriever (`/contract Q04`)
//!
//! What this file ships: three goals about powers of `BASE` (vstd's `pow`), each a proof fn
//! whose proof is a short chain of `vstd::arithmetic` lemma calls. It is green with holes:
//! the three labelled `assume(false)` lines are 3 tool-counted holes, and nothing else is
//! reported. Check command:
//!
//!     scripts/vcheck verus/q/q04_proof_craft/src/agent.rs
//!
//! Its audit dashboard shows one row per open goal (3 rows as shipped, none once every goal
//! is closed):
//!
//!     scripts/vaudit verus/q/q04_proof_craft/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies.
//!
//! Learner follow-up (before and after the contractor delivers; THIS is the exercise):
//! 1. Before the run: take each goal through your own search ladder, in order (IDE hover
//!    and go-to-definition, a scoped grep of the pinned vstd source, vstd's documentation,
//!    a model, memory), timing it, and fill the SEARCH LOG block at the end of this file.
//!    Do not edit the goals: the contractor proves them.
//! 2. In a FRESH session, run /contract Q04 on this file (after the Dafny file's run).
//! 3. Check the artifact yourself: the gate output, `git diff` (the three bodies only), the
//!    `// found-by:` lines and `scripts/vaudit`.
//! 4. Fill the COMPARISON block: did each `found-by:` rung match where the lemma lives? Did
//!    the transcript show a lemma name that does not exist (a resolution error), a step
//!    that is not a library call, or a statement edit? Which of your v0 rules did the run
//!    test?
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::power::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;

verus! {

// item: Q04.A1v S5

// ### The goals. Each proof is a short chain of `vstd::arithmetic` lemma calls.

/// The square of a power of `BASE` is a power of `BASE`.
pub proof fn lemma_pow_of_pow(n: nat)
    ensures
        pow(pow(BASE as int, n), 2) == pow(BASE as int, 2 * n),
{
    #[verifier::proof_note("Q04.A1v")] assume(false);  // HOLE: replace this line
}

/// Reducing the base modulo `BASE` first does not change the low limb of a power.
pub proof fn lemma_low_limb_of_power(x: int, e: nat)
    ensures
        pow(x % (BASE as int), e) % (BASE as int) == pow(x, e) % (BASE as int),
{
    #[verifier::proof_note("Q04.A1v")] assume(false);  // HOLE: replace this line
}

/// A positive power of `BASE` leaves the remainder 0 modulo `BASE`.
pub proof fn lemma_pow_mod_base(n: nat)
    requires
        n > 0,
    ensures
        pow(BASE as int, n) % (BASE as int) == 0,
{
    #[verifier::proof_note("Q04.A1v")] assume(false);  // HOLE: replace this line
}

} // verus!

// SEARCH LOG (learner-owned; before the contract run, with the Dafny half)
//   goal | lemma found | rung (ide, grep, docs, llm, memory) | minutes
//   lemma_pow_of_pow:
//   lemma_low_limb_of_power:
//   lemma_pow_mod_base:

// COMPARISON (learner-owned; after the contract run)
//   each `found-by:` rung against where the lemma lives:
//   a lemma name that does not exist (a resolution error) in the transcript?
//   a step that is not a library call, or a statement edit?
//   which rules of your contract v0 did the run test?
