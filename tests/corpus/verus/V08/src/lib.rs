//! Cheat corpus V08: exec_allows_no_decreases_clause lets a diverging loop prove a contradiction.
use vstd::prelude::*;

verus! {

#[verifier::exec_allows_no_decreases_clause]
pub fn settle(x: u64) -> (r: u64)
    ensures
        r < x && r > x,
{
    loop
        invariant
            true,
    {
    }
}

} // verus!
