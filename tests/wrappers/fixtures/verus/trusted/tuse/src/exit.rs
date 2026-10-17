//! Test fixture (tests/wrappers): a file no `mod` reaches (its own crate
//! root on tuse's dependencies) with its own hole beside a dependency's.
use vstd::prelude::*;
use tdep::*;

verus! {

pub fn copy_twice(x: u64) -> (r: u64)
    ensures
        r == x,
{
    copy_small(copy_small(x))
}

pub proof fn own_hole(x: nat)
    ensures
        x >= 7,
{
    assume(false);
}

} // verus!
