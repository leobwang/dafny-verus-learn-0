//! # qg_bignat_l6 — the BigNat spine, layer L6 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q13–Q18. From Q13 on, a module's crate depends on this layer beside
//! L1–L5. A file imports it with `use qg_bignat_l6::*;`, which also brings the L1–L5
//! names (re-exported below); the crate still lists the lower layers as dependencies.
//!
//! Do not open this file before you start Q13: it belongs to the intermediate practice
//! tier, and the files of a tier are opened with its first module.
//!
//! What it holds: one exec fn, `normalize`, which strips the most significant zero
//! limbs of a BigNat in place.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l5::*;

verus! {

// ---------------------------------------------------------------------------
// Exec code
// ---------------------------------------------------------------------------

/// Strip the most significant zero limbs in place: the result is well formed and keeps
/// the value.
pub fn normalize(a: &mut BigNat)
    ensures
        final(a).wf(),
        final(a).to_nat() == old(a).to_nat(),
{
    while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
        invariant
            a.to_nat() == old(a).to_nat(),
        decreases a.limbs.len(),
    {
        proof {
            lemma_seq_to_nat_drop_last_zero(a@);
        }
        a.limbs.pop();
    }
}

} // verus!
