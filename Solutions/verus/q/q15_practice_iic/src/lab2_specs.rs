//! # Q15 — Lab 2's prose specifications, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q15_practice_iic/src/lab2_specs.rs` (author-only;
//! never learner-visible). Same names, item markers and order as the exercise file. Each
//! prose task carries the author's specification (the hidden equivalence check's other
//! side; its sealed copy is the Lab 2 hidden truth) and the proof its code needs; the
//! clients' checks are live, and each witness fn holds one call.
#![allow(unused_imports)]
use vstd::prelude::*;
use core::cmp::Ordering;
use vstd::arithmetic::mul::*;
use qg_bignat_l6::*;

verus! {

// =========================================================================================
// Holes
// =========================================================================================

// HELPERS (Q15.H3v): any spec fn your specification needs, and at most one proof fn.

/// The number of non-zero limbs, counted from the top.
pub open spec fn nonzero_count(s: Seq<u64>) -> nat  // reference-only: the learner's definition
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        nonzero_count(s.drop_last()) + if s.last() != 0 { 1nat } else { 0nat }
    }
}

// item: Q15.H3v S13
// uses: ensures, witness
// prose: count_nonzero
/// **H3.** Prose task. *The number of non-zero limbs of a number's limb sequence, wherever
/// they sit.* Write `count_nonzero`'s specification, with the count itself as a spec fn of
/// your own, `nonzero_count(s: Seq<u64>) -> nat`, in the HELPERS area above.
pub fn count_nonzero(a: &BigNat) -> (n: usize)
    ensures
        n == nonzero_count(a@),
{
    let mut n: usize = 0;
    let mut i: usize = 0;
    while i < a.limbs.len()
        invariant
            i <= a@.len(),
            n <= i,
            n == nonzero_count(a@.subrange(0, i as int)),
        decreases a@.len() - i,
    {
        assert(a@.subrange(0, i as int + 1).drop_last() =~= a@.subrange(0, i as int));
        if a.limbs[i] != 0 {
            n = n + 1;
        }
        i = i + 1;
    }
    assert(a@.subrange(0, i as int) =~= a@);
    n
}

fn count_use(a: &BigNat)
    requires
        a@.len() == 1,
        a@[0] != 0,
{
    let n = count_nonzero(a); proof { reveal_with_fuel(nonzero_count, 2); }  // did: the client's own reveal
    assert(n == 1);
}

/// Your non-vacuity witness for `count_nonzero`: one call whose `requires` hold.
fn count_witness() {
    let a = from_u64(7);
    let n = count_nonzero(&a);
}

// HELPERS (Q15.H4v): at most one proof fn of your own, here.

// item: Q15.H4v S13
// uses: ensures, witness
// prose: split_at_limb
/// **H4.** Prose task. *Split a canonical number at limb `k`: the low part is the number
/// the limbs below `k` make, and below the place value of limb `k`; the high part is the
/// number the limbs from `k` on make; both are canonical, and the low part plus the high
/// part times that place value is the number. A `k` at or past the length leaves the high
/// part zero.* Write `split_at_limb`'s specification.
pub fn split_at_limb(a: &BigNat, k: usize) -> (r: (BigNat, BigNat))
    requires
        a.wf(),
    ensures
        r.0.wf(),
        r.1.wf(),
        r.0.to_nat() < weight(k as nat),
        a.to_nat() == r.0.to_nat() + weight(k as nat) * r.1.to_nat(),
{
    let n = a.limbs.len();
    let m = if k < n { k } else { n };
    let mut lo: Vec<u64> = Vec::new();
    let mut hi: Vec<u64> = Vec::new();
    let mut i: usize = 0;
    while i < m
        invariant
            m <= n,
            n == a@.len(),
            i <= m,
            lo@ == a@.subrange(0, i as int),
        decreases m - i,
    {
        lo.push(a.limbs[i]);
        i = i + 1;
    }
    let mut j: usize = m;
    while j < n
        invariant
            m <= j <= n,
            n == a@.len(),
            hi@ == a@.subrange(m as int, j as int),
        decreases n - j,
    {
        hi.push(a.limbs[j]);
        j = j + 1;
    }
    proof {
        broadcast use group_bignat_bounds;  // did: the layers' bounds, for both parts
        assert(lo@ == a@.subrange(0, m as int));
        assert(hi@ =~= a@.subrange(m as int, n as int));
        assert(a@ =~= lo@ + hi@);
        lemma_seq_to_nat_append(lo@, hi@);
        assert(seq_to_nat(lo@) < weight(m as nat));
        if m < k {
            assert(hi@.len() == 0);
            assert(seq_to_nat(hi@) == 0);
        }
    }
    let mut low = BigNat { limbs: lo };
    normalize(&mut low);
    let high = BigNat { limbs: hi };
    proof {
        broadcast use group_bignat_bounds;  // did: weight is monotone
        if hi@.len() > 0 {
            assert(hi@.last() == a@.last());
        }
        assert(weight(m as nat) <= weight(k as nat));
        assert(low.to_nat() == seq_to_nat(lo@));
        assert(low.to_nat() < weight(k as nat));
        assert(high.wf());
        assert(a.to_nat() == low.to_nat() + weight(m as nat) * high.to_nat());
        if m < k {
            assert(high.to_nat() == 0);
            assert(weight(m as nat) * high.to_nat() == 0);
            assert(weight(k as nat) * high.to_nat() == 0);
        }
    }
    (low, high)
}

fn split_use(a: &BigNat)
    requires
        a.wf(),
{
    let (lo, hi) = split_at_limb(a, 1);
    assert(a.to_nat() == lo.to_nat() + weight(1) * hi.to_nat());
    assert(lo.to_nat() < weight(1) && lo.wf() && hi.wf());
}

/// Your non-vacuity witness for `split_at_limb`: one call whose `requires` hold.
fn split_witness() {
    let a = from_u64(7);
    let r = split_at_limb(&a, 1);
}

// HELPERS (Q15.H5v): at most one proof fn of your own, here.

// item: Q15.H5v S13
// uses: ensures, witness
// prose: max_big
// triv: { BigNat { limbs: a.limbs.clone() } }
/// **H5.** Prose task. *The larger of two canonical numbers, as a canonical number (either
/// one when they are equal).* Its `requires` ships (the code's comparison needs it):
/// write `max_big`'s `ensures`.
pub fn max_big(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
    ensures
        r.wf(),
        r.to_nat() == if a.to_nat() < b.to_nat() { b.to_nat() } else { a.to_nat() },
{
    let c = cmp(a, b);
    let src = match c {
        Ordering::Less => b,
        _ => a,
    };
    let limbs = src.limbs.clone();
    BigNat { limbs }
}

fn max_use(a: &BigNat, b: &BigNat)
    requires
        a.wf(),
        b.wf(),
        a.to_nat() < b.to_nat(),
{
    let r = max_big(a, b);
    assert(r.wf() && r.to_nat() == b.to_nat());
    let s = max_big(b, a);
    assert(s.to_nat() == b.to_nat());
}

/// Your non-vacuity witness for `max_big`: one call whose `requires` hold.
fn max_witness() {
    let a = from_u64(7);
    let b = from_u64(9);
    let r = max_big(&a, &b);
}

} // verus!
