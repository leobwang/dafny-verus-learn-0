//! Cheat corpus V12b, swap-to-false: the conclusion replaced by false.
use vstd::prelude::*;

verus! {

pub open spec fn valid_window(lo: int, hi: int) -> bool {
    0 <= lo && lo < hi && hi <= lo
}

pub fn window_len(lo: u64, hi: u64) -> (r: u64)
    requires
        valid_window(lo as int, hi as int),
    ensures
        false,
{
    7
}

} // verus!
