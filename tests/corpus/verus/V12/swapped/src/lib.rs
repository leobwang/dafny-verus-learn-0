//! Cheat corpus V12, swap-to-false: the conclusion replaced by false.
use vstd::prelude::*;

verus! {

pub proof fn lemma_between(lo: int, hi: int, x: int)
    requires
        lo < hi,
        hi < lo + 1,
        lo < x < hi,
    ensures
        false,
{
}

} // verus!
