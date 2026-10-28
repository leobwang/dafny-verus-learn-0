//! # R16 — `rexc trust-report` (solo work: guard rule 2s; no contractor edits this file)
//!
//! Your gate for a delivered crate (the chapter's §9; Lab γ's instrument). It reads the
//! evidence of one delivery and answers PASS, FAIL or UNKNOWN, as R13's forensics and R15's
//! ladder taught: a green exit code is not evidence. You decide which checks it runs (the
//! reference gate with zero holes, vaudit, `specfreeze --check R16` against your frozen
//! statements, the seeds, the compiled tests) and how each outcome maps to a verdict; write
//! the rules down in research/TRUST.md before you run it on any delivery.
//!
//! As shipped every delivery is UNKNOWN. It is plain Rust outside `verus!`, compiled only
//! into the `rexc` binary.

/// The gate's three answers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    Pass,
    Fail,
    Unknown,
}

/// What the gate collected about one delivery; add the fields your rules need.
#[derive(Debug, Default)]
pub struct Evidence {
    pub gate_exit: Option<i32>,
    pub holes: Option<u32>,
    pub audit_findings: Option<u32>,
    pub freeze_findings: Option<u32>,
}

/// The verdict for the evidence: your rules.
pub fn verdict(evidence: &Evidence) -> Verdict {
    let _ = evidence;
    Verdict::Unknown
}
