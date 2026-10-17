/* CONTRACT
goal: refactor the proofs of this file so that the reasoning they share lives in proof fns under HELPERS and no fn body is longer than the REFACTOR comment's bound; change no statement
allowed-files:
  - verus/q/q07_internals_i/src/agent.rs
acceptance:
  - re-verify after every edit with `scripts/vcheck verus/q/q07_internals_i/src/agent.rs`; never stack unverified edits
  - `scripts/vcheck --gate verus/q/q07_internals_i/src/agent.rs` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q07_frozen.rs verus/q/q07_internals_i/src/agent.rs` reports no change
  - `scripts/vaudit verus/q/q07_internals_i/src/agent.rs` reports no finding
  - `git diff` from the commit of research/q07_frozen.rs changes no line of a FROZEN statement, and every new proof fn sits under HELPERS
  - no `reveal_with_fuel` call is added
*/
//! # Q07 Refactor, Verus half — refactorer under harness (Reference Solution)
//!
//! Hole-free reference for `verus/q/q07_internals_i/src/agent.rs` (author-only): the
//! delivered state, the proof that the contract is satisfiable as stated. Same CONTRACT,
//! imports, statements, item marker and order as the agent file; every FROZEN and API body
//! is refactored to at most 4 lines, and the one helper sits under HELPERS, after the loud
//! heading. Silent under `scripts/vcheck --ref`; `scripts/vaudit --ref` reports no finding;
//! `scripts/specfreeze --against` a snapshot of the shipped FROZEN section reports no
//! change.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l4::*;

verus! {

// item: Q07.A1v S5

// REFACTOR: no fn body longer than 4 lines (lines of code, not counting blank lines and
//    comments; a `proof { … }` block on one line counts as one).

// ### FROZEN

/// Two numbers scaled by one word, then added: the sum scaled.
pub fn scaled_sum(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat()) * x,
{
    let sa = mul_limb(a, x);
    let r = add_scaled(&sa, b, x);
    proof { lemma_sum_scaled(a.to_nat(), b.to_nat(), x as nat); }
    r
}

/// Three numbers scaled by one word, then added left to right: the sum scaled.
pub fn scaled_sum_three(a: &BigNat, b: &BigNat, c: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        c.wf(),
    ensures
        r.wf(),
        r.to_nat() == (a.to_nat() + b.to_nat() + c.to_nat()) * x,
{
    let t = scaled_sum(a, b, x);
    let r = add_scaled(&t, c, x);
    proof { lemma_sum_scaled(a.to_nat() + b.to_nat(), c.to_nat(), x as nat); }
    r
}

// ### API

/// Scaling twice is scaling by the product.
pub fn scale_twice(a: &BigNat, x: u64, y: u64) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() * (x * y),
{
    let t = mul_limb(a, x);
    let r = mul_limb(&t, y);
    proof { lemma_mul_is_associative(a.to_nat() as int, x as int, y as int); }
    r
}

/// A number plus another scaled by one word.
pub fn add_scaled(a: &BigNat, b: &BigNat, x: u64) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + b.to_nat() * x,
{
    let sb = mul_limb(b, x);
    big_add(a, &sb)
}

// ### HELPERS (the refactor's proof fns go here)

// =========================================================================================
// — clearly marked: everything below answers the agentic file —
// =========================================================================================
// The reference refactor has one proof fn, lemma_sum_scaled (the distributivity step both
// FROZEN fns repeat); scaled_sum goes through the API fn add_scaled, and scaled_sum_three
// reuses scaled_sum. The value facts the monolithic bodies restate are the callees'
// ensures, so they go. Every body is at most 4 lines.
//
// Soft spots a contract run shows (the learner's REVIEW looks for them):
//   - an API statement weakened to fit a helper: scale_twice's value ensures relaxed to
//     `>=` passes the gate, the audit and the freeze line (the snapshot holds FROZEN
//     only); the same change in scaled_sum is freeze-changed;
//   - a helper stated over `int` where callers pass `nat` values, or the reverse, with a
//     `requires` added to patch the gap;
//   - a reveal_with_fuel call or a verifier attribute added to make a step go through.

pub proof fn lemma_sum_scaled(u: nat, v: nat, x: nat)
    ensures
        u * x + v * x == (u + v) * x,
{
    lemma_mul_is_distributive_add_other_way(x as int, u as int, v as int);
}

} // verus!

/*
REVIEW (learner-owned; advisory: no script reads it). After the /contract run, from
`git diff` against the snapshot's commit:
  changed lines (file:line, what changed):
  API statements (each: unchanged / weaker, and how):
  new proof fns (each: its statement strong enough for every caller? a `requires` no
  caller can establish?):
*/
