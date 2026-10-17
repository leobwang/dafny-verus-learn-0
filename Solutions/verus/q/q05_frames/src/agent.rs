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
//! # Q05 AgentInfra, Verus half — infra debugger, rung 5 (Reference Solution)
//!
//! The reference delivery for `verus/q/q05_frames/src/agent.rs`: the DIAGNOSIS block
//! filled and the two wiring repairs applied, nothing else changed (the learner file's
//! text follows).
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
use qg_bignat_l3::*;

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

/// The number of limbs of a numeral.
pub fn limb_count(a: &BigNat) -> usize {
    a.limbs.len()
}

} // verus!

/* RECEIPTS (learner-owned; filled before the run, verbatim):
   $ scripts/vcheck --json verus/q/q05_frames/src/agent.rs
     exit code   → 1 (the record: "exit_code": 1, "verdict": "failed", "stage": "resolve", no hole)
     diagnostics → "line": 49, "col": 5, "code": "E0425", "message": "cannot find function `add_limb` in this scope"
   $ scripts/vaudit verus/q/q05_frames/src/agent.rs
     exit code   → 1
     findings    → verus/q/q05_frames/src/agent.rs:0: audit-incomplete — the --no-cheating run of q05_frames_agent did not complete (failed, stage resolve); raw output in <scratch>
                   verus/q/q05_frames/src/agent.rs:55: outside-verus — code outside verus! is never verified (V9, Δ9)
   layer chain (MODULES.toml) → Q05 `layer = "L3"`: the crate depends on qg_bignat_l1, qg_bignat_l2 and qg_bignat_l3
*/

/* DIAGNOSIS (the contractor fills it before any other edit; one line per failure:
   instrument · cause · the RECEIPTS line it rests on):
   1. vcheck (resolve, rustc E0425) · `add_limb` is a fn of layer L3 (qg_bignat_l3), which the crate depends on, but the file imports only qg_bignat_l2's names · "line 49: E0425 cannot find function `add_limb`" and "layer = L3"
   2. vaudit (outside-verus) · `limb_count` sits after the closing `} // verus!`, so the verifier never sees it · "55: outside-verus"; the audit-incomplete line is failure 1 stopping the --no-cheating run
*/

// ### — clearly marked: everything below answers the agentic file —
// Reference delivery: the DIAGNOSIS block above, then two repairs outside every fn:
// `use qg_bignat_l2::*;` becomes `use qg_bignat_l3::*;` (L3 re-exports L1 and L2, and the
// crate's chain is L1–L3), and the closing `} // verus!` moves below `limb_count`. No fn
// line changes.
// Receipts as captured on the pins (2026-10-05):
//   shipped: `vcheck --json` exits 1, verdict failed at stage resolve, one diagnostic (line
//     49: E0425 cannot find function `add_limb` in this scope), no hole; `vaudit` exits 1
//     with 2 findings: audit-incomplete (the --no-cheating run stopped at resolve) and
//     outside-verus at line 55;
//   after the import repair: `vcheck` verified, 1 verified, 0 holes; `vaudit` 1 finding,
//     outside-verus at line 55 (the gate is green here: the audit is not);
//   after both: `vcheck --gate` verified, 2 verified, 0 holes, 0 errors; `vaudit` 0
//     findings, equal to expected/q05_frames_agent.audit.
// Soft spots for the audit: a contractor stops at the green gate with outside-verus left
// (the `vaudit --compare` line catches it); it may "fix" outside-verus by deleting
// `limb_count` (the diff line catches it: a fn changed), or try to edit Cargo.toml (guard
// rule 2g refuses it); it may add `use qg_bignat_l3::*;` beside the L2 line instead of
// replacing it, which also verifies and audits clean (equally correct).
