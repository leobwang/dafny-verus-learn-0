//! Test fixture (tests/wrappers): an invented exec item for the empty-body gate.
use vstd::prelude::*;

verus! {

pub fn count_up(n: u64) -> (r: u64)
    ensures
        r == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    assert(i == n);
    i
}

} // verus!
