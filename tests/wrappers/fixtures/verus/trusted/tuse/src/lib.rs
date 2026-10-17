//! Test fixture (tests/wrappers): a hole-free crate that calls every fn of
//! tdep (copy_small twice: one diagnostic per called fn, not per call).
use vstd::prelude::*;
use tdep::*;

verus! {

pub fn use_copy(x: u64) -> (r: u64)
    ensures
        r == x,
{
    copy_small(x)
}

pub fn use_copy_again(x: u64) -> (r: u64)
    ensures
        r == x,
{
    copy_small(x)
}

pub proof fn use_trusted(x: nat)
    ensures
        x + x >= x,
{
    lemma_trusted(x);
}

pub proof fn use_assumed(x: nat)
    ensures
        x * 2 == x + x,
{
    lemma_assumed(x);
}

} // verus!
