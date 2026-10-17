//! Gate v2 fixture K2: two small word operations.
use vstd::prelude::*;

verus! {

pub fn add_one(x: u32) -> (r: u32)
    requires
        x < 100,
    ensures
        r == x + 1,
{
    x + 1
}

pub fn half_up(x: u32) -> (r: u32)
    ensures
        2 * r >= x,
{
    x / 2
}

} // verus!
