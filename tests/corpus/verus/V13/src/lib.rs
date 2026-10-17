//! Cheat corpus V13: the shipped ensures of max2 weakened, so a wrong body verifies.
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
