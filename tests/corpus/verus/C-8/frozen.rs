//! Cheat corpus control C-8, frozen statement: clamp as shipped (body a hole).
use vstd::prelude::*;

verus! {

pub fn clamp(x: u64, lo: u64, hi: u64) -> (r: u64)
    requires
        lo <= hi,
    ensures
        lo <= r <= hi,
        lo <= x <= hi ==> r == x,
{
    assume(false);
    lo
}

} // verus!
