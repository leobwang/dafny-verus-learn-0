// Reference Solution.
//! R13 pipeline forensic: a delivery whose public caller delegates to a helper. Read this
//! file, snapshot it under research/R13/ before any contractor edit, and find which
//! dependency makes the caller's apparent success incomplete. The contractor
//! (/contract R13, a fresh session) may write only the helper's body, over the printed
//! domain; every signature, clause and the provided caller stay. Review the delivery
//! yourself with at least two instruments on the full file.
use vstd::prelude::*;

verus! {

/// Provided caller: its contract is the helper's.
pub fn delivered_score_r13(a: u32, b: u32) -> (score: u64)
    ensures
        score == 2 * a + 3 * b,
        score <= 21474836475,
{
    support_score_r13(a, b)
}

// item: R13.A1v
// triv: { 0 }
fn support_score_r13(a: u32, b: u32) -> (score: u64)
    ensures
        score == 2 * a + 3 * b,
        score <= 21474836475,
{
    // ref-begin R13.A1v
    // did: widen before the weighted additions, with no trusted helper.
    2 * (a as u64) + 3 * (b as u64)
    // ref-end R13.A1v
}

} // verus!
