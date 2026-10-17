//! # Q11 — exit, Verus half (closed book)
//!
//! Closed book: keep the chapter, the exercise files, later modules' files, search tools
//! and /tutor closed. At most the given spine (verus/given/) may be open.
//!
//! This file ships with exactly 1 hole (X1); the Dafny half
//! (dafny/Q/Q11_PracticeIB/exit/Q11_Exit.dfy) ships with 1 hole. Each is timed: 10 minutes.
//! Score both halves in one sitting with
//!
//!     scripts/firsttry.sh Q11 --exit
//!
//! Threshold: 1 of the 2 exit items. The first full run (every block attempted) is the
//! score; repair every block afterwards, after which the strict gate covers this file too.
//! This file is never `mod`-declared and is in no build: work it with
//! `scripts/vcheck verus/q/q11_practice_ib/src/exit.rs`.
#![allow(unused_imports)]
use vstd::prelude::*;
use qg_bignat_l5::*;

verus! {

// Given (not an item): a two-word counter, its value read as two limbs.
pub struct Counter2 {
    pub lo: u64,
    pub hi: u64,
}

impl Counter2 {
    pub open spec fn value(&self) -> nat {
        self.lo as nat + BASE * self.hi as nat
    }

    // item: Q11.X1v S6
    // uses: mut-ref, old
    // need: pub fn incr(&mut self)
    /// **X1.** Add one to the counter.
    #[verifier::external_body]  // HOLE: remove this line and implement
    pub fn incr(&mut self)
        requires
            old(self).hi < u64::MAX,
        ensures
            final(self).value() == old(self).value() + 1,
    {
        unimplemented!()
    }
}

} // verus!
