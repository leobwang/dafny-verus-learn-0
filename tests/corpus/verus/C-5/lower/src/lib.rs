//! Cheat corpus control C-5, lower crate: a proved lemma and its spec fn.
use vstd::prelude::*;

verus! {

pub open spec fn twice(x: nat) -> nat {
    x + x
}

pub proof fn lemma_twice(x: nat)
    ensures
        twice(x) == 2 * x,
{
}

} // verus!
