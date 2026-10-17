//! Cheat corpus control C-2: a proof fn by induction.
use vstd::prelude::*;

verus! {

pub open spec fn sum_to(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        n + sum_to((n - 1) as nat)
    }
}

pub proof fn lemma_sum_to_ge(n: nat)
    ensures
        sum_to(n) >= n,
    decreases n,
{
    if n > 0 {
        lemma_sum_to_ge((n - 1) as nat);
    }
}

} // verus!
