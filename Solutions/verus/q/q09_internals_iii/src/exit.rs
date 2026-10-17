//! # Q09 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q09_internals_iii/src/exit.rs` (author-only; never
//! learner-visible). Same items, given declarations, item markers, `need:` and `form:` lines
//! and order as the exit file; both exit holes are filled. The file is silent:
//! `scripts/vcheck --ref` on it prints only the summary line. No proof fn carries a resource
//! attribute.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

/// Given (not an item): the sum of the limbs of a sequence, and how it adds up over a
/// concatenation, for X2.
pub open spec fn limb_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + limb_sum(s.drop_first())
    }
}

pub proof fn lemma_limb_sum_append(s: Seq<u64>, t: Seq<u64>)
    ensures
        limb_sum(s + t) == limb_sum(s) + limb_sum(t),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s + t =~= t);
    } else {
        assert((s + t).drop_first() =~= s.drop_first() + t);
        lemma_limb_sum_append(s.drop_first(), t);
    }
}

// item: Q09.X1v S11
// uses: proof-split
// need: pub proof fn lemma_product_plus_carry(x: nat, y: nat, z: nat, n: nat)
// need: x * y + z < weight(n) * weight(n)
// pair: Q09.X1d
// form: nl-steps:2, stable
// cfree: { let p = weight(n); assert(x * y + z < p * p) by (nonlinear_arith) requires x < p, y < p, z < p; }
/// **X1.** A product plus a carry stays below the square. Reference: two scoped steps, the
/// product at most `(p - 1) * (p - 1)` from the two bounds, and `(p - 1) * (p - 1) + (p - 1)`
/// below `p * p` from `p >= 1`; the carry fills at most the `p - 1` left over. Stable under
/// seeds 1-3. The `cfree:` line above (one step with all three bounds) verifies too: the
/// `nl-steps:2` form stops it, a presence check of two scoped steps.
pub proof fn lemma_product_plus_carry(x: nat, y: nat, z: nat, n: nat)
    requires
        x < weight(n),
        y < weight(n),
        z < weight(n),
    ensures
        x * y + z < weight(n) * weight(n),
{
    let p = weight(n);
    // did: the product bounded by the largest factors, from the two bounds alone
    assert(x * y <= (p - 1) * (p - 1)) by (nonlinear_arith)
        requires
            x < p,
            y < p,
    ;
    // did: the expansion of the square, from p >= 1 alone
    assert((p - 1) * (p - 1) + (p - 1) < p * p) by (nonlinear_arith)
        requires
            p >= 1,
    ;
}

// item: Q09.X2v S11
// uses: trigger-rewrite
// need: pub proof fn lemma_sum_four(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
// need: limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d)
// need: limb_sum(s + t) == limb_sum(s) + limb_sum(t)
// need: lemma_limb_sum_append(s, t);
// pair: Q09.X2d
// form: trigger, stable
// cfree: { lemma_limb_sum_append(a + b + c, d); lemma_limb_sum_append(a + b, c); lemma_limb_sum_append(a, b); }
/// **X2.** The limb sum of four concatenated parts. Reference: the quoted fact with its
/// trigger moved to the composite term `limb_sum(s + t)`, which fires only at the three
/// concatenations the goal holds; the quoted multi-trigger fires on every pair of limb-sum
/// terms and its instances explode. Stable under seeds 1-3. The `cfree:` line above (three
/// direct calls) verifies too: the `need:` lines and the `trigger` form stop it.
pub proof fn lemma_sum_four(a: Seq<u64>, b: Seq<u64>, c: Seq<u64>, d: Seq<u64>)
    ensures
        limb_sum(a + b + c + d) == limb_sum(a) + limb_sum(b) + limb_sum(c) + limb_sum(d),
{
    assert forall|s: Seq<u64>, t: Seq<u64>|
        #[trigger] limb_sum(s + t) == limb_sum(s) + limb_sum(t) by {
        lemma_limb_sum_append(s, t);
    }
}

} // verus!
