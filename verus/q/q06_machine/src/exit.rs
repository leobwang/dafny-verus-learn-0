//! # Q06 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q06_Machine/exit/Q06_Exit.dfy) ships with 2 holes. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q06 --exit
//!
//! Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language. The first
//! full run (every block attempted) is the score; repair every block afterwards, after
//! which the strict gate covers this file too (and runs X1's suite: `scripts/vcheck --test
//! verus/q/q06_machine/src/exit.rs`). X2 counts only with no resource attribute in this
//! file. This file is never `mod`-declared and is in no build: work it with
//! `scripts/vcheck verus/q/q06_machine/src/exit.rs`.
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
/// **X1.** A differential check of two result vectors of equal length: return the index
/// of the first position at which they disagree, or `None` when they agree everywhere.
/// Then uncomment X1's suite at the end of this file: the agreeing candidate must give
/// `None`, the planted one the index of its first disagreement.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn first_disagreement(xs: &Vec<bool>, ys: &Vec<bool>) -> (r: Option<usize>)
    requires
        xs.len() == ys.len(),
    ensures
        r is None <==> (forall|k: int| 0 <= k < xs.len() ==> #[trigger] xs@[k] == ys@[k]),
        r is Some ==> r->Some_0 < xs.len() && xs@[r->Some_0 as int] != ys@[r->Some_0 as int],
{
    unimplemented!()
}

// item: Q06.X2v S11
// uses: opaque-reveal, rlimit
// need: pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)
// need: low(x + m * y, m) == low(x, m)
// pair: Q06.X2d
/// **X2.** Adding a multiple of `m` does not change the low part. Prove it at the pinned
/// rlimit, with no resource attribute. This attempt does not verify at that limit:
///
///     reveal(low);
///     assert forall|t: nat| #[trigger] low(t, m) == low(t + m, m) by {
///         reveal(low);
///         lemma_mod_add_multiples_vanish(t as int, m as int);
///     }
pub proof fn lemma_low_of_shift(x: nat, y: nat, m: nat)
    requires
        0 < m,
    ensures
        low(x + m * y, m) == low(x, m),
{
    #[verifier::proof_note("Q06.X2v")] assume(false);  // HOLE: replace this line
}

} // verus!

// X1's suite: the results of a reference, of an agreeing candidate and of a planted one.
// Uncomment as you go:
// #[cfg(test)]
// mod x1_suite {
//     use super::*;
//
//     fn results(f: fn(u64) -> bool) -> Vec<bool> {
//         [0u64, 1, 2, 7, 8].iter().map(|&x| f(x)).collect()
//     }
//
//     #[test]
//     fn agreeing_candidate() {
//         let reference = results(|x| x % 2 == 0);
//         let candidate = results(|x| x & 1 == 0);
//         assert_eq!(first_disagreement(&candidate, &reference), None);
//     }
//
//     #[test]
//     fn planted_candidate() {
//         let reference = results(|x| x % 2 == 0);
//         let planted = results(|x| x % 4 == 0);
//         assert_eq!(first_disagreement(&planted, &reference), Some(2));
//     }
// }
