//! # qg_bignat_l7 — the BigNat spine, layer L7 (PROVIDED, complete)
//!
//! This file is provided infrastructure, not an exercise: there is nothing to fill in
//! and nothing here is a hole. It is frozen: no session edits it, and no module copies
//! it.
//!
//! Imported by: Q16–Q18. From Q16 on, a module's crate depends on this layer beside
//! L1–L6. A file imports it with `use qg_bignat_l7::*;`, which also brings the L1–L6
//! names (re-exported below) and the base API of `src/api.rs`; the crate still lists the
//! lower layers as dependencies.
//!
//! Do not open this file before you start Q16: it belongs to the hard practice tier, and
//! the files of a tier are opened with its first module.
//!
//! What it holds: two exec fns, `big_sub` (subtraction of a smaller or equal BigNat) and
//! `to_u64` (the value as one word, when it fits); and, in `src/api.rs`, the frozen base
//! API `BigNatCore`, which extends L4's `NatLike` with `minus` and `to_word`, with its
//! implementation for `BigNat` by those two fns.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
pub use qg_bignat_l6::*;

pub mod api;
pub use api::*;

verus! {

// ---------------------------------------------------------------------------
// Exec code
// ---------------------------------------------------------------------------

// The limbs r and the borrows c (c[j] into position j, c[|r|] out of the top) add up to
// the two values.
proof fn lemma_sub_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)
    requires
        a.len() == r.len(),
        b.len() <= r.len(),
        c.len() == r.len() + 1,
        c[r.len() as int] <= 1,
        forall|j: int|
            0 <= j < r.len() ==> limb_at(a, j) + BASE * c[j + 1] == #[trigger] r[j] + limb_at(b, j)
                + c[j],
    ensures
        seq_to_nat(a) + (if c[r.len() as int] == 0 { 0 } else { weight(r.len()) }) == seq_to_nat(r)
            + seq_to_nat(b) + c[0],
    decreases r.len(),
{
    reveal(weight);
    if r.len() > 0 {
        let a2 = a.drop_first();
        let b2 = if b.len() > 0 { b.drop_first() } else { b };
        let r2 = r.drop_first();
        let c2 = c.drop_first();
        assert forall|j: int| 0 <= j < r2.len() implies limb_at(a2, j) + BASE * c2[j + 1]
            == #[trigger] r2[j] + limb_at(b2, j) + c2[j] by {
            assert(limb_at(a, j + 1) + BASE * c[j + 2] == r[j + 1] + limb_at(b, j + 1) + c[j + 1]);
        }
        lemma_sub_lift(a2, b2, r2, c2);
        assert(limb_at(a, 0) + BASE * c[1] == r[0] + limb_at(b, 0) + c[0]);
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

/// Subtraction: `a - b`, for `b` at most `a`, well formed.
pub fn big_sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;
    let n = a.limbs.len();
    let m = b.limbs.len();
    let mut res: Vec<u64> = Vec::new();
    let mut borrow: u64 = 0;
    let mut i: usize = 0;
    let ghost mut c: Seq<nat> = seq![0nat];
    while i < n
        invariant
            n == a@.len(),
            m == b@.len(),
            m <= n,
            i <= n,
            res@.len() == i,
            c.len() == i + 1,
            c[0] == 0,
            c[i as int] == borrow,
            borrow <= 1,
            forall|j: int|
                0 <= j < i ==> limb_at(a@, j) + BASE * c[j + 1] == #[trigger] res@[j] + limb_at(b@, j)
                    + c[j],
        decreases n - i,
    {
        let x: u64 = a.limbs[i];
        let y: u64 = if i < m { b.limbs[i] } else { 0 };
        let d: u64;
        if x >= y && x - y >= borrow {
            d = x - y - borrow;
            borrow = 0;
        } else {
            d = ((x as u128 + 0x1_0000_0000_0000_0000u128) - y as u128 - borrow as u128) as u64;
            borrow = 1;
        }
        res.push(d);
        proof {
            c = c.push(borrow as nat);
        }
        i = i + 1;
    }
    proof {
        lemma_sub_lift(a@, b@, res@, c);
    }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}

/// The value as one word: `Some` of it when it is below `BASE`, else `None`.
pub fn to_u64(a: &BigNat) -> (r: Option<u64>)
    requires
        a.wf(),
    ensures
        r is Some <==> a.to_nat() < BASE,
        r is Some ==> r->0 as nat == a.to_nat(),
{
    let n = a.limbs.len();
    if n == 0 {
        Some(0)
    } else if n == 1 {
        proof {
            assert(a@.drop_first() =~= Seq::<u64>::empty());
            assert(seq_to_nat(a@.drop_first()) == 0);
        }
        Some(a.limbs[0])
    } else {
        proof {
            lemma_seq_to_nat_lower(a@);
            lemma_weight_mono(1, (n - 1) as nat);
            lemma_weight_zero();
            lemma_weight_succ(0);
        }
        None
    }
}

} // verus!
