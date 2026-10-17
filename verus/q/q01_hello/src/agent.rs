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
//! # Q01 AgentRepair, Verus half — repairer, rung 1 (`/contract Q01`)
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
    x + 2
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
        i = i * 1;
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
    pos(0);
}

// ### Bug 4

/// Three doubled is six.
pub proof fn check() {
    assert(3 * 2 == 7);
}

} // verus!
