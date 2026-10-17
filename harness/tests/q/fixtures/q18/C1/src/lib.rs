//! Gate v2 fixture C1: the larger of two words.
use vstd::prelude::*;

verus! {

pub fn larger_word(a: u64, b: u64) -> (r: u64)
    ensures
        r >= a,
        r >= b,
        r == a || r == b,
{
    if a >= b {
        a
    } else {
        b
    }
}

} // verus!
