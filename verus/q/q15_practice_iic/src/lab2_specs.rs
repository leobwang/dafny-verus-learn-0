//! # Q15 — Lab 2's prose specifications, Verus half (Exercises)
//!
//! Three prose tasks (Lab 2, design §11.2: specification quality). Each ships an exec fn's
//! signature and its implementation, with the loop bounds its code needs to be safe, and
//! no specification: you write its `requires` and `ensures` from the prose, with any spec
//! fn of your own the specification needs (in the task's `HELPERS` area). Its code is
//! given; you may add proof (invariants, `proof { … }` blocks, assertions), never change
//! its code. Then uncomment the use-site check in its client, write a non-vacuity witness
//! (one call whose `requires` hold) in its witness fn, and delete the client's assume.
//!
//! What grades a specification: the use-site check, your witness, /review-code, and, in
//! the grader container, a hidden two-way check against the author's specification and
//! the kill of mutants of the given code (QPLAN §25.5, §25.6). You start the hidden check
//! from your own terminal, never from a Claude session: the chapter's §5 gives the line,
//! and it prints one verdict word per specification, with the outcome words of the checks
//! behind it (which side and direction differ; Q13's §2).
//!
//! This file ships with exactly 3 holes (H3, H4 and H5), each counted by `scripts/vcheck`:
//! one labelled assume per client. Done and the slot protocol are in src/lib.rs's header.
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

// item: Q15.H3v S13
// uses: ensures, witness
// prose: count_nonzero
/// **H3.** Prose task. *The number of non-zero limbs of a number's limb sequence, wherever
/// they sit.* Write `count_nonzero`'s specification, with the count itself as a spec fn of
/// your own, `nonzero_count(s: Seq<u64>) -> nat`, in the HELPERS area above.
pub fn count_nonzero(a: &BigNat) -> (n: usize) {
    let mut n: usize = 0;
    let mut i: usize = 0;
    while i < a.limbs.len()
        invariant
            i <= a@.len(),
            n <= i,
        decreases a@.len() - i,
    {
        if a.limbs[i] != 0 {
            n = n + 1;
        }
        i = i + 1;
    }
    n
}

fn count_use(a: &BigNat)
    requires
        a@.len() == 1,
        a@[0] != 0,
{
    #[verifier::proof_note("Q15.H3v")] assume(false);  // HOLE: delete once count_nonzero is specified
    // Uncomment as you go:
    // let n = count_nonzero(a); proof { reveal_with_fuel(nonzero_count, 2); }
    // assert(n == 1);
}

/// Your non-vacuity witness for `count_nonzero`: one call whose `requires` hold.
fn count_witness() {
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
pub fn split_at_limb(a: &BigNat, k: usize) -> (r: (BigNat, BigNat)) {
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
    let mut low = BigNat { limbs: lo };
    normalize(&mut low);
    let high = BigNat { limbs: hi };
    (low, high)
}

fn split_use(a: &BigNat)
    requires
        a.wf(),
{
    #[verifier::proof_note("Q15.H4v")] assume(false);  // HOLE: delete once split_at_limb is specified
    // Uncomment as you go:
    // let (lo, hi) = split_at_limb(a, 1);
    // assert(a.to_nat() == lo.to_nat() + weight(1) * hi.to_nat());
    // assert(lo.to_nat() < weight(1) && lo.wf() && hi.wf());
}

/// Your non-vacuity witness for `split_at_limb`: one call whose `requires` hold.
fn split_witness() {
}

// HELPERS (Q15.H5v): at most one proof fn of your own, here.

// item: Q15.H5v S13
// uses: ensures, witness
// prose: max_big
/// **H5.** Prose task. *The larger of two canonical numbers, as a canonical number (either
/// one when they are equal).* Its `requires` ships (the code's comparison needs it):
/// write `max_big`'s `ensures`.
pub fn max_big(a: &BigNat, b: &BigNat) -> (r: BigNat)
    requires
        a.wf(),
        b.wf(),
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
    #[verifier::proof_note("Q15.H5v")] assume(false);  // HOLE: delete once max_big is specified
    // Uncomment as you go:
    // let r = max_big(a, b);
    // assert(r.wf() && r.to_nat() == b.to_nat());
    // let s = max_big(b, a);
    // assert(s.to_nat() == b.to_nat());
}

/// Your non-vacuity witness for `max_big`: one call whose `requires` hold.
fn max_witness() {
}

} // verus!
