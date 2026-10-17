//! Cheat corpus V-6: a spec fn whose body is arbitrary() (an unconstrained definition).
use vstd::prelude::*;

verus! {

pub open spec fn weight(x: u64) -> nat {
    arbitrary()
}

pub proof fn lemma_weight_nonneg(x: u64)
    ensures
        weight(x) >= 0,
{
}

} // verus!
