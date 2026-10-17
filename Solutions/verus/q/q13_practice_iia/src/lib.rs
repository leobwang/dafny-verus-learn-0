//! # Q13 — Practice II-A: the Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q13_practice_iia/src/lib.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the
//! exercise crate; every hole is filled, every check is live, and the prose item's
//! statement is the reference one (the hidden equivalence check's other side). Each item
//! uses at most the one helper the tier allows, in its `HELPERS` area; the exec item
//! declares its trivial body in a `// triv:` line.
//!
//! Silent under `scripts/vcheck --ref` on the crate.
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// HELPERS (Q13.H1v): at most one proof fn of your own, here.
/// The borrow chain's lift: the limbs written, with the ghost borrows `c`, add up to the
/// two values.
pub proof fn lemma_sub_lift(a: Seq<u64>, b: Seq<u64>, r: Seq<u64>, c: Seq<nat>)  // reference-only: the learner's helper
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

// item: Q13.H1v S1
// uses: invariant, ghost, lemma-recursion
// triv: { BigNat { limbs: Vec::new() } }
/// **H1.** Subtraction with a borrow chain: one pass over the limbs from the low limb,
/// each step subtracting the next limb of `b` (0 past its end) and the borrow, borrowing
/// from the next limb when that goes below zero. No skeleton; layer L6's `normalize` is
/// available for the result. What ghost record of the borrows lets one lemma tie the
/// limbs you wrote to the two values?
pub fn sub(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
    ensures
        r.wf(),
        r.to_nat() == a.to_nat() - b.to_nat(),
{
    broadcast use group_bignat_bounds;  // did: the layers' bounds, so that m <= n
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
        proof { c = c.push(borrow as nat); }
        i = i + 1;
    }
    proof { lemma_sub_lift(a@, b@, res@, c); }
    let mut r = BigNat { limbs: res };
    normalize(&mut r);
    r
}

fn sub_check(a: &BigNat, b: &BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() >= b.to_nat(),
{
    let r = sub(a, b);
    assert(r.to_nat() + b.to_nat() == a.to_nat());
}

// HELPERS (Q13.H3v): at most one proof fn of your own, here.
/// The sequence without its low limb (empty stays empty).
pub open spec fn tail(s: Seq<u64>) -> Seq<u64> {  // reference-only: the learner's definition
    if s.len() > 0 { s.drop_first() } else { s }
}

/// Two sequences that agree at every position (a missing limb read as zero) have one value.
pub proof fn lemma_eq_any(a: Seq<u64>, b: Seq<u64>)  // reference-only: the learner's helper
    requires
        forall|j: int| 0 <= j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) == seq_to_nat(b),
    decreases a.len() + b.len(),
{
    if a.len() > 0 || b.len() > 0 {
        assert forall|j: int| 0 <= j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j) by {
            assert(limb_at(a, j + 1) == limb_at(b, j + 1));
        }
        lemma_eq_any(tail(a), tail(b));
        assert(limb_at(a, 0) == limb_at(b, 0));
        if a.len() == 0 {
            assert(seq_to_nat(a) == 0);
        }
        if b.len() == 0 {
            assert(seq_to_nat(b) == 0);
        }
    }
}

// item: Q13.H3v S2
// uses: lemma-recursion, forall
// prose: lemma_lt_at_any
/// **H3.** Prose item. *Read a missing limb as zero. If two limb sequences — not
/// necessarily canonical, possibly of different lengths — agree at every position above
/// some index, and at that index the first one's limb is the smaller, then the first one's
/// value is the smaller.*
///
/// State it as `pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)`, above
/// the client `prose_use_site`, and prove it (layer L3's `limb_at` reads a missing limb as
/// zero). Then uncomment the use-site check, write one non-vacuity witness in
/// `prose_witness` (a call whose `requires` hold), and delete the client's assume.
// reference-only: the prose item's statement, written by the learner
pub proof fn lemma_lt_at_any(a: Seq<u64>, b: Seq<u64>, i: int)
    requires
        0 <= i,
        limb_at(a, i) < limb_at(b, i),
        forall|j: int| i < j ==> #[trigger] limb_at(a, j) == limb_at(b, j),
    ensures
        seq_to_nat(a) < seq_to_nat(b),
    decreases i,
{
    assert forall|j: int| i - 1 < j implies #[trigger] limb_at(tail(a), j) == limb_at(tail(b), j)
        by {
        assert(limb_at(a, j + 1) == limb_at(b, j + 1));
    }
    if i == 0 {
        lemma_eq_any(tail(a), tail(b));
    } else {
        lemma_lt_at_any(tail(a), tail(b), i - 1);
    }
    if a.len() == 0 {
        assert(seq_to_nat(a) == 0);
    }
}

pub proof fn prose_use_site(a: Seq<u64>, b: Seq<u64>)
    requires
        a.len() == 3,
        b.len() == 2,
        a[1] < b[1],
        a[2] == 0,
{
    lemma_lt_at_any(a, b, 1);
    assert(seq_to_nat(a) < seq_to_nat(b));
}

/// Your non-vacuity witness for `lemma_lt_at_any`: one call whose `requires` hold.
pub proof fn prose_witness() {
    lemma_lt_at_any(Seq::<u64>::empty(), seq![1u64], 0);
}

// HELPERS (Q13.H4v): at most one proof fn of your own, here.

// item: Q13.H4v S5
// uses: library-call
// pair: Q13.H4d
// form: no-nl
// cfree: { if n == 0 { lemma_weight_zero(); assert(seq_to_nat(Seq::new(n, |i: int| d)) == 0); } else { let k = (n - 1) as nat; assert(Seq::new(n, |i: int| d).drop_first() =~= Seq::new(k, |i: int| d)); lemma_repeat_value(d, k); lemma_weight_succ(k); let tv = seq_to_nat(Seq::new(k, |i: int| d)) as int; let w = weight(k) as int; assert(seq_to_nat(Seq::new(n, |i: int| d)) == d + BASE * tv); assert(seq_to_nat(Seq::new(n, |i: int| d)) * (BASE - 1) == d * (weight(n) - 1)) by (nonlinear_arith) requires tv * (BASE - 1) == d * (w - 1), seq_to_nat(Seq::new(n, |i: int| d)) == d + BASE * tv, weight(n) == BASE * w; } }
/// **H4.** The value of `n` equal non-zero limbs, by `vstd::arithmetic::mul` (imported):
/// with no `nonlinear_arith`, every product step is a named lemma. Which steps need one?
pub proof fn lemma_repeat_value(d: u64, n: nat)
    requires
        0 < d,
    ensures
        seq_to_nat(Seq::new(n, |i: int| d)) * (BASE - 1) == d * (weight(n) - 1),
    decreases n,
{
    let s = Seq::new(n, |i: int| d);
    if n == 0 {
        lemma_weight_zero();
        assert(seq_to_nat(s) == 0);
    } else {
        let k = (n - 1) as nat;
        let t = Seq::new(k, |i: int| d);
        assert(s.drop_first() =~= t);
        lemma_repeat_value(d, k);
        lemma_weight_succ(k);
        let tv = seq_to_nat(t) as int;
        let w = weight(k) as int;
        assert(seq_to_nat(s) == d + BASE * tv);
        lemma_mul_is_distributive_add_other_way((BASE - 1) as int, d as int, BASE * tv);
        lemma_mul_is_associative(BASE as int, tv, (BASE - 1) as int);
        lemma_mul_is_distributive_sub(d as int, w, 1);
        lemma_mul_is_associative(BASE as int, d as int, w);
        lemma_mul_is_commutative(BASE as int, d as int);
        lemma_mul_is_associative(d as int, BASE as int, w);
        lemma_mul_is_distributive_sub(d as int, BASE * w, 1);
    }
}

} // verus!
