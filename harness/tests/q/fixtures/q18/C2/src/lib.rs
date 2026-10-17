//! Gate v2 fixture C2: a word bounded into a range.
use vstd::prelude::*;

verus! {

pub fn bound_into(x: u64, lo: u64, hi: u64) -> (r: u64)
    requires
        lo <= hi,
    ensures
        lo <= r <= hi,
        lo <= x <= hi ==> r == x,
{
    if x < lo {
        lo
    } else if x > hi {
        hi
    } else {
        x
    }
}

} // verus!
