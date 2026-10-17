//! Cheat corpus control C-7, swap-to-false: the conclusion replaced by false.
use vstd::prelude::*;

verus! {

pub fn mid(lo: u64, hi: u64) -> (r: u64)
    requires
        lo <= hi,
    ensures
        false,
{
    lo + (hi - lo) / 2
}

} // verus!
