//! Cheat corpus V13c: a self-written spec of max2 too weak to pin the result (no frozen statement).
use vstd::prelude::*;

verus! {

pub fn max2(a: u64, b: u64) -> (r: u64)
    ensures
        r >= a,
        r >= b,
{
    u64::MAX
}

} // verus!
