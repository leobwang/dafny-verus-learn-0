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
//! # Q04 Retriever race, Verus half — retriever (Reference Solution)
//!
//! Hole-free reference for `verus/q/q04_proof_craft/src/agent.rs` (author-only; never
//! learner-visible): the three goals closed by library calls, each with its receipt, and
//! the reference section under the loud heading at the end.
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
    lemma_pow_multiplies(BASE as int, n, 2);  // found-by: grep
}

/// Reducing the base modulo `BASE` first does not change the low limb of a power.
pub proof fn lemma_low_limb_of_power(x: int, e: nat)
    ensures
        pow(x % (BASE as int), e) % (BASE as int) == pow(x, e) % (BASE as int),
{
    lemma_pow_mod_noop(x, e, BASE as int);  // found-by: grep
}

/// A positive power of `BASE` leaves the remainder 0 modulo `BASE`.
pub proof fn lemma_pow_mod_base(n: nat)
    requires
        n > 0,
    ensures
        pow(BASE as int, n) % (BASE as int) == 0,
{
    lemma_pow_adds(BASE as int, (n - 1) as nat, 1);  // found-by: grep
    lemma_pow1(BASE as int);  // found-by: grep
    lemma_mod_multiples_basic(pow(BASE as int, (n - 1) as nat), BASE as int);  // found-by: grep
}

// =========================================================================================
// — clearly marked: everything below answers the agentic file —
// =========================================================================================
// The reference delivery is the three bodies above: one call for the first two goals
// (`lemma_pow_multiplies(BASE, n, 2)` turns `(BASE^n)^2` into `BASE^(n * 2)`;
// `lemma_pow_mod_noop(x, e, BASE)` reduces the base), three for the third (`BASE^n` is
// `BASE^(n - 1) * BASE^1`, `BASE^1` is `BASE`, and a multiple of `BASE` leaves remainder
// 0). Every call names a lemma of `vstd::arithmetic::power` or `vstd::arithmetic::div_mod`,
// reached by a scoped `grep` of the pinned vstd source.
//
// Soft spots a contractor tends to hit, each one the COMPARISON block should catch:
//   - an invented lemma name (for example `lemma_pow_positive_auto`): a resolution error in
//     the transcript, then a retry under a different name;
//   - a step that is not a library call: an `assert(…) by (nonlinear_arith)` or a
//     `broadcast use` line, which the gate may accept and the contract's body rule does
//     not;
//   - a helper proof fn of its own (a declaration the `git diff` shows);
//   - `// found-by: memory` (or `llm`) on every line, whatever the transcript shows: check
//     each rung against the transcript's own search commands.
// Gate admissibility: every empty-body mode fails on each goal, the light arithmetic groups
// (E2), the course group (EC) and the heavy multiplication group (EM) included
// (Solutions/plans/Q04-code-notes.md §7).

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
