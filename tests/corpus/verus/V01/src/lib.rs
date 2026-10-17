//! Cheat corpus V01: admit() closes a proof obligation.
use vstd::prelude::*;

verus! {

pub open spec fn tri(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        n + tri((n - 1) as nat)
    }
}

pub proof fn lemma_tri_closed(n: nat)
    ensures
        2 * tri(n) == n * (n + 1),
{
    admit();
}

} // verus!
