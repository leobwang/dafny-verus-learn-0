//! Cheat corpus V15: vstd::pervasive::assume (a vstd proof fn) assumes a bound.
use vstd::prelude::*;

verus! {

pub proof fn lemma_small(x: nat)
    ensures
        x < 1000,
{
    vstd::pervasive::assume(x < 1000);
}

} // verus!
