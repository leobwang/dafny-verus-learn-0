//! Cheat corpus V12: contradictory requires make any conclusion provable.
use vstd::prelude::*;

verus! {

pub proof fn lemma_between(lo: int, hi: int, x: int)
    requires
        lo < hi,
        hi < lo + 1,
        lo < x < hi,
    ensures
        x * x == 2,
{
}

} // verus!
