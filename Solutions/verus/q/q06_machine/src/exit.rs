//! # Q06 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q06_machine/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the exit
//! file; both blocks are filled and silent under `scripts/vcheck --ref`. No fn carries a
//! resource attribute (X2 is a budget item).
#![allow(unused_imports)]
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;
use qg_bignat_l3::*;

verus! {

/// Given (not an item): the low part of `x` modulo `m`, for X2. Opaque: its body is hidden
/// from every proof that does not reveal it.
#[verifier::opaque]
pub open spec fn low(x: nat, m: nat) -> nat
    recommends
        m > 0,
{
    x % m
}

// item: Q06.X1v S12
// uses: property-test
// need: pub fn first_disagreement(xs: &Vec<bool>, ys: &Vec<bool>) -> (r: Option<usize>)
// need: r is None <==> (forall|k: int| 0 <= k < xs.len() ==> #[trigger] xs@[k] == ys@[k])
// need: r is Some ==> r->Some_0 < xs.len() && xs@[r->Some_0 as int] != ys@[r->Some_0 as int]
// pair: Q06.X1d
/// **X1.** A differential check of two result vectors.
///
/// Reference: one pass that returns the index of the first disagreement. The invariant
/// (every index before `k` agrees) gives the `None` exit its `forall`; the early return
/// carries its witness. The trivial body `None` fails the `<==>`.
pub fn first_disagreement(xs: &Vec<bool>, ys: &Vec<bool>) -> (r: Option<usize>)
    requires
        xs.len() == ys.len(),
    ensures
        r is None <==> (forall|k: int| 0 <= k < xs.len() ==> #[trigger] xs@[k] == ys@[k]),
        r is Some ==> r->Some_0 < xs.len() && xs@[r->Some_0 as int] != ys@[r->Some_0 as int],
{
    let mut k: usize = 0;
    while k < xs.len()
        invariant
            k <= xs.len(),
            xs.len() == ys.len(),
            forall|j: int| 0 <= j < k ==> #[trigger] xs@[j] == ys@[j],
        decreases xs.len() - k,
    {
        if xs[k] != ys[k] {
            return Some(k);
        }
        k = k + 1;
    }
    None
}
// triv: { None }

// item: Q06.X2v S11
// uses: opaque-reveal, rlimit
// need: pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)
// need: low(x + m * y, m) == low(x, m)
// pair: Q06.X2d
/// **X2.** Adding a multiple of `m` does not change the low part. This attempt does not
/// verify at the pinned rlimit:
///
///     reveal(low);
///     assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by {
///         reveal(low);
///         lemma_mod_add_multiples_vanish(t as int, m as int);
///     }
///
/// Reference: drop the quantified step (each instance makes a new `low` term, which fires
/// it again); reveal `low` and call `lemma_mod_multiples_vanish(y, x, m)`, which states
/// `(m * y + x) % m == x % m`. No resource attribute.
pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)
    requires
        0 < m,
    ensures
        low(x + m * y, m) == low(x, m),
{
    reveal(low);  // did: unfolds low's body for this proof
    lemma_mod_multiples_vanish(y as int, x as int, m as int);
}

} // verus!

// X1's suite (live in the reference): the results of a reference, of an agreeing
// candidate and of a planted one.
#[cfg(test)]
mod x1_suite {
    use super::*;

    fn results(f: fn(u64) -> bool) -> Vec<bool> {
        [0u64, 1, 2, 7, 8].iter().map(|&x| f(x)).collect()
    }

    #[test]
    fn agreeing_candidate() {
        let reference = results(|x| x % 2 == 0);
        let candidate = results(|x| x & 1 == 0);
        assert_eq!(first_disagreement(&candidate, &reference), None);
    }

    #[test]
    fn planted_candidate() {
        let reference = results(|x| x % 2 == 0);
        let planted = results(|x| x % 4 == 0);
        assert_eq!(first_disagreement(&planted, &reference), Some(2));
    }
}
