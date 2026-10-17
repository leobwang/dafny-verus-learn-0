//! # qg_bignat_l5 — the BigNat spine, layer L5 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q10–Q18. From Q10 on, a module's crate depends on this layer beside
//! L1–L4. A file imports it with `use qg_bignat_l5::*;`, which also brings the L1–L4
//! names (re-exported below); the crate still lists the lower layers as dependencies.
//!
//! Do not open this file before you start Q10: it belongs to the practice tiers, and
//! the files of a tier are opened with its first module.
//!
//! What it holds: one proof fn about the L3 definitions, `lemma_weight_pos` (every
//! weight is positive).
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l4::*;

verus! {

// ---------------------------------------------------------------------------
// Proofs about the L3 definitions
// ---------------------------------------------------------------------------

/// Every weight is positive.
pub proof fn lemma_weight_pos(n: nat)
    ensures
        weight(n) > 0,
{
    lemma_weight_zero();
    lemma_weight_mono(0, n);
}

} // verus!
