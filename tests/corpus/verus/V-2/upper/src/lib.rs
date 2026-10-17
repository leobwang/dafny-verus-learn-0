//! Cheat corpus V-2, upper crate: calls the lower crate's trusted fn.
use vstd::prelude::*;

verus! {

pub fn quarter(x: u64) -> (r: u64)
    ensures
        r * 4 == x,
{
    let h = corpus_vd2_lower::halve(x);
    corpus_vd2_lower::halve(h)
}

} // verus!
