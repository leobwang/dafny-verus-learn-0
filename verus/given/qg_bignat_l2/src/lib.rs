//! # qg_bignat_l2 — the BigNat spine, layer L2 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q02–Q18. Q02's and Q03's crates depend on this layer and on L1; from
//! Q04 on, a module's crate depends on it beside the later layers of its chain. A file
//! imports it with `use qg_bignat_l2::*;`, which also brings L1's names (re-exported
//! below); the crate still lists `qg_bignat_l1` as a dependency.
//!
//! What it holds: the spec helper `limb_at` and the carry-lifting lemma
//! `lemma_add_limb_lift`. It holds no exec fn.
#![allow(unused_imports)]
use vstd::prelude::*;
pub use qg_bignat_l1::*;

verus! {

/// Limb `j` of `s`, reading past the end as zero.
pub open spec fn limb_at(s: Seq<u64>, j: int) -> nat {
    if 0 <= j < s.len() {
        s[j] as nat
    } else {
        0
    }
}

/// Carry lifting: per-limb relations `limb_at(a, j) + c[j] == r[j] + BASE * c[j + 1]`
/// for every limb of `r`, with a final carry of zero, add up to the value relation
/// `seq_to_nat(r) == seq_to_nat(a) + c[0]`.
pub proof fn lemma_add_limb_lift(a: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] == 0,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + c[j] == #[trigger] r[j] + BASE * c[j + 1],
    ensures
        seq_to_nat(r) == seq_to_nat(a) + c[0],
    decreases r.len(),
{
    if r.len() > 0 {
        let a2 = if a.len() > 0 {
            a.drop_first()
        } else {
            a
        };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + c2[j] == #[trigger] r2[j]
            + BASE * c2[j + 1] by {
            assert(limb_at(a, j + 1) + c[j + 1] == r[j + 1] + BASE * c[j + 2]);
        }
        lemma_add_limb_lift(a2, r2, c2);
        assert(limb_at(a, 0) + c[0] == r[0] + BASE * c[1]);
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
    }
}

} // verus!
