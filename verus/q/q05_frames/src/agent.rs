/* CONTRACT
goal: diagnose this file's two wiring failures from its RECEIPTS block, then repair them
allowed-files:
  - verus/q/q05_frames/src/agent.rs
acceptance:
  - a DIAGNOSIS block, filled in this file before any other edit: one line per failure, naming the instrument that reports it, the cause, and the RECEIPTS line it rests on
  - `git diff` changes no line of a fn (signature, contract or body): only lines outside every fn change, and the DIAGNOSIS block
  - `scripts/vcheck --gate verus/q/q05_frames/src/agent.rs` exits 0 and prints only the summary line
  - zero holes in the allowed file (tool-counted)
  - after every edit, re-run both `scripts/vcheck --json verus/q/q05_frames/src/agent.rs` and `scripts/vaudit verus/q/q05_frames/src/agent.rs`, never two edits between runs
  - `scripts/vaudit --compare expected/q05_frames_agent.audit verus/q/q05_frames/src/agent.rs` reports no difference
*/
//! # Q05 AgentInfra, Verus half — infra debugger, rung 5 (`/contract Q05`)
//!
//! This file ships RED by design: it holds two planted wiring failures and no hole. As
//! shipped, `scripts/vcheck --json` on it exits 1 with exactly one error and no hole, and
//! `scripts/vaudit` exits 1 with two findings. Its fns are right as written, and each doc
//! comment states the intended behaviour; once the file is wired right, it verifies and
//! its audit is clean. It is never `mod`-declared:
//! `scripts/vcheck` builds it standalone with the crate's dependencies. A wiring file (a
//! Cargo.toml, MODULES.toml, anything under scripts/) is never the fix: the guard refuses
//! every edit there. The two instruments:
//!
//!     scripts/vcheck --json verus/q/q05_frames/src/agent.rs
//!     scripts/vaudit verus/q/q05_frames/src/agent.rs
//!
//! Done is the gate, with a clean audit:
//!
//!     scripts/vcheck --gate verus/q/q05_frames/src/agent.rs
//!
//! The learner follow-up (the receipts first, the audit afterwards) is in the Dafny half,
//! dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy; this file's RECEIPTS block is at its end.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l2::*;

verus! {

// item: Q05.A1v S6

/// One more than a numeral, computed by the layer's `add_limb`.
pub fn one_more(a: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() + 1,
{
    add_limb(a, 1)
}

} // verus!

/// The number of limbs of a numeral.
pub fn limb_count(a: &BigNat) -> usize {
    a.limbs.len()
}

/* RECEIPTS (learner-owned; filled before the run, verbatim):
   $ scripts/vcheck --json verus/q/q05_frames/src/agent.rs
     exit code   →
     diagnostics →
   $ scripts/vaudit verus/q/q05_frames/src/agent.rs
     exit code   →
     findings    →
   layer chain (MODULES.toml) →
*/

/* DIAGNOSIS (the contractor fills it before any other edit; one line per failure:
   instrument · cause · the RECEIPTS line it rests on):
*/
