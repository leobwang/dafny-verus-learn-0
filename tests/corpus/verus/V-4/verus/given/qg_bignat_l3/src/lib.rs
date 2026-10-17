//! Cheat corpus V-4, a stand-in for a later given layer (L3): it proves a lemma.
use vstd::prelude::*;

verus! {

pub open spec fn dbl(x: nat) -> nat {
    x + x
}

pub proof fn lemma_dbl(x: nat)
    ensures
        dbl(x) == 2 * x,
{
}

} // verus!
