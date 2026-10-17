//! # Q08 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 2 holes (X1, X2); the Dafny half
//! (dafny/Q/Q08_InternalsII/exit/Q08_Exit.dfy) ships with 2 holes. Score both halves in one
//! sitting with
//!
//!     scripts/firsttry.sh Q08 --exit
//!
//! Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language. The first
//! full run (every block attempted) is the score; repair every block afterwards, after
//! which the strict gate covers this file too. Then fill the EXPLAIN-BACK block at the end
//! of the Dafny exit file. This file is never `mod`-declared and is in no build: work it
//! with `scripts/vcheck verus/q/q08_internals_ii/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l4::*;

verus! {

// Given (not items): the sum of a sequence of words, for X1 and X2.
pub open spec fn words_sum(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        words_sum(s.drop_last()) + s.last() as nat
    }
}

// Given (not items): a ledger whose total is the sum of its ghost log, for X2.
pub struct Ledger {
    pub total: u64,
    pub log: Ghost<Seq<u64>>,
}

impl Ledger {
    pub open spec fn inv(&self) -> bool {
        self.total == words_sum(self.log@)
    }
}

// item: Q08.X1v S6
// uses: trait-spec
// need: pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)
// need: r.value() == words_sum(xs@),
/// **X1.** Sum the words of `xs` into a natural number of any type `T` that implements L4's
/// `NatLike`, through the trait only.
#[verifier::external_body]  // HOLE: remove this line and implement
pub fn sum_words<T: NatLike>(xs: &Vec<u64>) -> (r: T)
    ensures
        r.valid(),
        r.value() == words_sum(xs@),
{
    unimplemented!()
}

// item: Q08.X2v S7
// need: pub fn record(&mut self, x: u64)
// need: final(self).log@ == old(self).log@.push(x),
/// **X2.** Record the amount `x` in the ledger: add it to the total and append it to the
/// log, keeping the invariant.
impl Ledger {
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn record(&mut self, x: u64)
        requires
            old(self).inv(),
            old(self).total + x <= u64::MAX,
        ensures
            final(self).inv(),
            final(self).log@ == old(self).log@.push(x),
    {
        unimplemented!()
    }
}

} // verus!
