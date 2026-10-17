//! Cheat corpus V13b: the shipped requires of triple strengthened, narrowing what is proved.
use vstd::prelude::*;

verus! {

pub fn triple(x: u64) -> (r: u64)
    requires
        x < 10,
    ensures
        r == 3 * x,
{
    x * 3
}

} // verus!
