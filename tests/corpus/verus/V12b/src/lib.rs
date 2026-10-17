//! Cheat corpus V12b: a precondition predicate that no input satisfies admits a wrong body.
use vstd::prelude::*;

verus! {

pub open spec fn valid_window(lo: int, hi: int) -> bool {
    0 <= lo && lo < hi && hi <= lo
}

pub fn window_len(lo: u64, hi: u64) -> (r: u64)
    requires
        valid_window(lo as int, hi as int),
    ensures
        r == hi - lo,
{
    7
}

} // verus!
