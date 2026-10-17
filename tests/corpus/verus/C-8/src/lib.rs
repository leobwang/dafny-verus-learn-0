//! Cheat corpus control C-8: the shipped statement of clamp kept, the body filled.
use vstd::prelude::*;

verus! {

pub fn clamp(x: u64, lo: u64, hi: u64) -> (r: u64)
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
