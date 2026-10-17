//! # Q12 — Practice I-C + Lab 1: the practice block (Reference Solution)
//!
//! Hole-free reference for `verus/q/q12_practice_ic/src/lib.rs` (author-only; never
//! learner-visible). Same crate layout, imports, names, statements, item markers and order
//! as the exercise file; H3's hole is filled. The file is silent: `scripts/vcheck --ref`
//! on the crate prints only the summary line. The `cfree:` line is the conclusion's
//! second hop alone (it names `b` and `c` at `k` but never `a`'s term); it must fail.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use qg_bignat_l5::*;

mod lab1_hand;

verus! {

// =========================================================================================
// The prediction block. Q12's six predictions are the stage specimens
// specimens/Q12/P1d.dfy.specimen … P6v.rs.specimen; commit every one of them before you
// read past this block, and record the first tries:
//     scripts/firsttry.sh Q12 --check
// =========================================================================================

// =========================================================================================
// Holes
// =========================================================================================

// item: Q12.H3v S11
// uses: trigger
// cfree: { assert(limb_at(b, k) <= limb_at(c, k)); }
/// **H3.** A chain of two limb-wise bounds. Each hypothesis is quantified over every
/// position and fires on its own trigger (layer L2's `limb_at`, which reads a missing limb
/// as 0). Prove the conclusion at one position `k` inside `a`: give the verifier the terms
/// its triggers need, and nothing more.
pub proof fn lemma_chain_le(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, k: int)
    requires
        0 <= k < a.len(),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) <= limb_at(b, j),
        forall|j: int| 0 <= j ==> #[trigger] limb_at(b, j) <= limb_at(c, j),
    ensures
        a[k] as nat <= limb_at(c, k),
{
    assert(limb_at(a, k) <= limb_at(b, k));
}

} // verus!
