//! Cheat corpus V-3, lower crate: a lemma closed by assume.
use vstd::prelude::*;

verus! {

pub proof fn lemma_even(x: int)
    ensures
        x % 2 == 0,
{
    assume(x % 2 == 0);
}

} // verus!
