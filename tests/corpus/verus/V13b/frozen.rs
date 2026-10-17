//! Cheat corpus V13b, frozen statement: triple as shipped.
use vstd::prelude::*;

verus! {

pub fn triple(x: u64) -> (r: u64)
    requires
        x <= u64::MAX / 3,
    ensures
        r == 3 * x,
{
    x * 3
}

} // verus!
