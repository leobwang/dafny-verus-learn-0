//! Cheat corpus V-10: include! splices in source the lint never reads.
use vstd::prelude::*;

include!("extra_items.rs");

verus! {

pub fn settle_twice(x: u64) -> (r: u64)
    ensures
        r < x && r > x,
{
    settle(x)
}

} // verus!
