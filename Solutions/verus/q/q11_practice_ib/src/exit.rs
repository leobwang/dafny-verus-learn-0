//! # Q11 — exit, Verus half (Reference Solution)
//!
//! Hole-free reference for `verus/q/q11_practice_ib/src/exit.rs` (author-only; never
//! learner-visible). Same imports, names, statements, item markers and order as the exit
//! file; the hole is filled. The exec item declares its `// triv:` body for the empty-body
//! gate's TRIV mode. Silent under `scripts/vcheck --ref`.
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
    ///
    /// Reference: when the low word is not full, add one to it; otherwise the low word
    /// wraps to 0 and the high word takes the carry, which the precondition keeps in range.
    /// The verifier does the arithmetic of `value` in both branches.
    pub fn incr(&mut self)
        requires
            old(self).hi < u64::MAX,
        ensures
            final(self).value() == old(self).value() + 1,
    {
        if self.lo < u64::MAX {
            self.lo = self.lo + 1;
        } else {
            self.lo = 0;
            self.hi = self.hi + 1;
        }
    }
    // triv: { }
}

} // verus!
