//! Cheat corpus V05: assume_specification gives a std fn a spec it does not meet.
use vstd::prelude::*;

verus! {

pub assume_specification[ u64::rotate_left ](x: u64, n: u32) -> (r: u64)
    ensures
        r == x;

pub fn rotate_three(x: u64) -> (r: u64)
    ensures
        r == x,
{
    x.rotate_left(3)
}

} // verus!
