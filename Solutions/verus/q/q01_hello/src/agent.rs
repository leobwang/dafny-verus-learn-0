/* CONTRACT
goal: make this file verify by repairing its four planted bugs, each with a one-line edit to a body
allowed-files:
  - verus/q/q01_hello/src/agent.rs
acceptance:
  - `scripts/vcheck --gate verus/q/q01_hello/src/agent.rs` exits 0 and prints only the summary line
  - `git diff` shows only body lines: no signature, requires, ensures, decreases, heading or doc comment line changed
  - every fix is one line (one changed or one added line per bug)
  - re-verify after every edit with `scripts/vcheck verus/q/q01_hello/src/agent.rs`, never two edits between runs
  - zero holes in the allowed file (tool-counted), and no new assume, admit, external_body or verifier attribute
  - `scripts/vaudit --compare expected/q01_hello_agent.audit verus/q/q01_hello/src/agent.rs` reports no difference
*/
//! # Q01 AgentRepair, Verus half — repairer, rung 1 (Reference Solution)
//!
//! The reference delivery for `verus/q/q01_hello/src/agent.rs`: the four repairs applied,
//! one line each, nothing else changed (the learner file's text follows).
//!
//! This file ships RED: `scripts/vcheck verus/q/q01_hello/src/agent.rs` exits 1 with
//! exactly 4 errors, one message per bug, and no hole (the done gate adds one summary
//! error of its own). Each bug sits in its own declaration under a neutral heading; the doc
//! comment of each declaration states the intended behaviour, and each repair is one line
//! in a body. It is never `mod`-declared: `scripts/vcheck` builds it standalone with the
//! crate's dependencies. Done is the gate:
//!
//!     scripts/vcheck --gate verus/q/q01_hello/src/agent.rs
//!
//! The learner follow-up (the exercise) and the THREE DOORS block are in the Dafny half,
//! `dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy`.
#![allow(unused_imports)]
use vstd::prelude::*;

verus! {

// item: Q01.A1v S12

// ### Bug 1

/// The successor of `x` (for `x < 100`).
pub fn succ(x: u64) -> (y: u64)
    requires
        x < 100,
    ensures
        y == x + 1,
{
    x + 1
}

// ### Bug 2

/// Returns `n`, counting up from 0 one step at a time.
pub fn count_up(n: u64) -> (i: u64)
    ensures
        i == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

// ### Bug 3

/// Multiplying a positive number by one leaves it unchanged.
pub proof fn pos(n: nat)
    requires
        n > 0,
    ensures
        n * 1 == n,
{
}

/// Uses `pos` on a positive number.
pub proof fn use_pos() {
    pos(1);
}

// ### Bug 4

/// Three doubled is six.
pub proof fn check() {
    assert(3 * 2 == 6);
}

// ### — clearly marked: everything below answers the agentic file —
// Reference delivery: the four one-line repairs above (Bug 1 `x + 1`, Bug 2
// `i = i + 1;`, Bug 3 `pos(1);`, Bug 4 `assert(3 * 2 == 6);`); `git diff` shows four
// changed body lines.
// Shipped output (captured on the pins, `scripts/vcheck <learner file>`): exit 1, 2
// verified, 0 holes, 4 errors: Bug 1 "postcondition not satisfied", Bug 2 "decreases not
// satisfied at end of loop", Bug 3 "precondition not satisfied", Bug 4 "assertion
// failed"; `--gate` adds its own summary error ('success' is false). All four are
// verification-stage errors, so no bug masks another. (The Dafny half's Bug 2 is an
// index error; in Verus an out-of-range `v[i]` is reported as a failed precondition of
// the indexing call, the same message as Bug 3, so the Verus Bug 2 is a loop that does
// not advance.)
// Planted soft spots for the audit: none beyond the bugs. A contractor that weakens a
// postcondition, adds an `assume` or an `external_body`, or drops the loop's `decreases`
// for an attribute would be caught by the acceptance lines (`git diff` body-only, the
// empty audit pin, no new verifier attribute).

} // verus!
