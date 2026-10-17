//! Cheat corpus V-12, a stand-in for a later given layer (A4): it proves a lemma.
use vstd::prelude::*;

verus! {

pub open spec fn twice_len(n: nat) -> nat {
    n + n
}

pub proof fn lemma_twice_len(n: nat)
    ensures
        twice_len(n) >= n,
{
}

} // verus!
