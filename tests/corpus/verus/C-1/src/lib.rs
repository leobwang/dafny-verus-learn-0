//! Cheat corpus control C-1: a verified exec fn with a loop invariant.
use vstd::prelude::*;

verus! {

pub fn count_up(n: u32) -> (r: u32)
    ensures
        r == n,
{
    let mut i: u32 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

} // verus!
