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
//! # Q07 Refactor, Verus half — refactorer under harness (`/contract Q07`)
//!
//! What this file ships: four verified exec fns that compose layer L4's `big_add` and
//! `mul_limb`, each proved monolithically (the same facts restated in every body), in two
//! sections. FROZEN holds the statements the contract pins: its freeze line compares them
//! with your snapshot. API holds statements that callers rely on but that no acceptance line
//! pins. HELPERS is empty: it takes the proof fns of the refactor. The file is green with no
//! hole. Check command:
//!
//!     scripts/vcheck verus/q/q07_internals_i/src/agent.rs
//!
//! The file is never `mod`-declared: no build of the crate reaches it; `scripts/vcheck`
//! verifies it on its own with the crate's dependencies.
//!
//! Before the run:
//! 1. Copy the FROZEN section to research/q07_frozen.rs: this file's `use` lines and the
//!    `verus! {` line, then everything from `// ### FROZEN` through the end of
//!    `scaled_sum_three`, then `} // verus!`. It is the snapshot the contract's freeze line
//!    compares against.
//! 2. Commit it with research/q07_frozen.dfy (the Dafny file's header says how), in a commit
//!    that leaves this file as shipped.
//!
//! Learner follow-up (after the contractor delivers; THIS is the exercise):
//! 1. In a FRESH session, run /contract Q07 on this file (after the Dafny file's run).
//! 2. Review the diff from the snapshot's commit and fill REVIEW (the block at the end):
//!    every changed line; every API statement (weaker than before? a clause dropped?);
//!    every new proof fn's statement (weaker than its callers need? a `requires` no caller
//!    can establish?).
//! 3. Add this run to the Dafny file's COMPARISON block. (The local Qwen replay runs on the
//!    Dafny file only.)
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
    let sb = mul_limb(b, x);
    let r = big_add(&sa, &sb);
    proof {
        assert(sa.to_nat() == a.to_nat() * x);
        assert(sb.to_nat() == b.to_nat() * x);
        assert(r.to_nat() == a.to_nat() * x + b.to_nat() * x);
        lemma_mul_is_distributive_add_other_way(x as int, a.to_nat() as int, b.to_nat() as int);
    }
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
    let sa = mul_limb(a, x);
    let sb = mul_limb(b, x);
    let sc = mul_limb(c, x);
    let t = big_add(&sa, &sb);
    let r = big_add(&t, &sc);
    proof {
        assert(sa.to_nat() == a.to_nat() * x);
        assert(sb.to_nat() == b.to_nat() * x);
        assert(sc.to_nat() == c.to_nat() * x);
        assert(t.to_nat() == a.to_nat() * x + b.to_nat() * x);
        lemma_mul_is_distributive_add_other_way(x as int, a.to_nat() as int, b.to_nat() as int);
        assert(t.to_nat() == (a.to_nat() + b.to_nat()) * x);
        lemma_mul_is_distributive_add_other_way(
            x as int,
            (a.to_nat() + b.to_nat()) as int,
            c.to_nat() as int,
        );
    }
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
    proof {
        assert(r.to_nat() == a.to_nat() * x * y);
        lemma_mul_is_associative(a.to_nat() as int, x as int, y as int);
    }
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
    let r = big_add(a, &sb);
    proof {
        assert(sb.to_nat() == b.to_nat() * x);
    }
    r
}

// ### HELPERS (the refactor's proof fns go here)

} // verus!

/*
REVIEW (learner-owned; advisory: no script reads it). After the /contract run, from
`git diff` against the snapshot's commit:
  changed lines (file:line, what changed):
  API statements (each: unchanged / weaker, and how):
  new proof fns (each: its statement strong enough for every caller? a `requires` no
  caller can establish?):
*/
