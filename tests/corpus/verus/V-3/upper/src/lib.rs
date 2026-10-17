//! Cheat corpus V-3, upper crate: relies on the lower crate's assumed lemma.
use vstd::prelude::*;

verus! {

pub fn parity(x: u64) -> (r: u64)
    ensures
        r == 0,
{
    proof {
        corpus_vd3_lower::lemma_even(x as int);
    }
    x % 2
}

} // verus!
