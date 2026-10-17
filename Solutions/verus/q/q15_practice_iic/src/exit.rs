//! # Q15 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q15_practice_iic/src/exit.rs` (author-only; never
//! learner-visible). The exit file ships no block (Q15's exit item is the Dafny one), so
//! the twin holds none either. Silent under `scripts/vcheck --ref`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l6::*;

verus! {

/// Given (not an item): an empty proof, so that the gate has one function to count (its
/// minimum is one verified function).
pub proof fn no_q15_verus_exit_item() {
}

} // verus!
