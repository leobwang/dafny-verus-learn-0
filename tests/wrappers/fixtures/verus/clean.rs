//! Test fixture (tests/wrappers): invented, hole-free.
use vstd::prelude::*;

verus! {

pub open spec fn double(x: int) -> int {
    2 * x
}

pub proof fn lemma_double(x: int)
    ensures
        double(x) == x + x,
{
}

pub fn add_one(x: u64) -> (r: u64)
    requires
        x < 100,
    ensures
        r == x + 1,
{
    x + 1
}

} // verus!
