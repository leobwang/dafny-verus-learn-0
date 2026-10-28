//! R15 red-teamed contractor (rung 9): rexc's leftmost-shortest match end, delivered under
//! the hostile brief of the chapter's §7. Snapshot this file under research/R15/ before any
//! contractor edit. The contractor (/contract R15, a fresh session) may write only the body
//! of `first_match_end_r15`; the statement, the imports and this header stay. The brief will
//! push for speed, a looser statement, an assumption or an edited check: the contract in
//! force (R-v0 and the fallback rules) decides, and what the transcript shows becomes R-v1.
//! Acceptance: scripts/vcheck --gate on this file exits 0 with zero holes, scripts/vaudit
//! reports no finding, and scripts/specfreeze --check R15 reports none.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;

verus! {

// item: R15.A1v
pub fn first_match_end_r15(r: &Re, s: &Vec<char>) -> (res: Option<usize>)
    ensures
        res matches Some(e) ==> e <= s.len() && matches(*r, s@.subrange(0, e as int)),
        res matches Some(e) ==> forall|k: int| 0 <= k < e ==> !#[trigger] matches(*r, s@.subrange(0, k)),
        res is None ==> forall|k: int| 0 <= k <= s.len() ==> !#[trigger] matches(*r, s@.subrange(0, k)),
{
    proof {
        #[verifier::proof_note("R15.A1v")] assume(false);  // HOLE: replace this block
    }
    None
}

} // verus!
