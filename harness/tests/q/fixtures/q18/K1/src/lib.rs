//! Gate v2 fixture K1: a staircase closed form.
use vstd::prelude::*;

verus! {

pub open spec fn stair(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        n + stair((n - 1) as nat)
    }
}

pub proof fn lemma_stair_closed(n: nat)
    ensures
        2 * stair(n) == n * (n + 1),
    decreases n,
{
    if n > 0 {
        lemma_stair_closed((n - 1) as nat);
    }
}

} // verus!
