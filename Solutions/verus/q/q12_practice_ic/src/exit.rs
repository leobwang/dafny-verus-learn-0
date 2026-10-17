//! # Q12 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q12_practice_ic/src/exit.rs` (author-only; never
//! learner-visible). Same imports, item markers, `need:` lines and order as the exit
//! file; the exit hole is filled. The file is silent: `scripts/vcheck --ref` on it prints
//! only the summary line.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// item: Q12.X1v S11
// need: pub proof fn lemma_weight_two()
// need: weight(2) == BASE * BASE
/// **X1.** The weight of two limbs. Layer L3's `weight` is `BASE` to the power `n`.
/// Prove the instance below.
pub proof fn lemma_weight_two()
    ensures
        weight(2) == BASE * BASE,
{
    reveal_with_fuel(weight, 3);  // did: unfolds the opaque weight three levels, to weight(0)
}

} // verus!
