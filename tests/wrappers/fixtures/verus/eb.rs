//! Test fixture (tests/wrappers): invented proof items for the empty-body gate.
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

// item: Q04.H5v S4
pub proof fn lemma_tri_closed(n: nat)
    ensures
        2 * tri(n) == n * (n + 1),
    decreases n,
{
    if n > 0 {
        lemma_tri_closed((n - 1) as nat);
        assert(2 * tri(n) == n * (n + 1)) by (nonlinear_arith)
            requires
                2 * tri((n - 1) as nat) == (n - 1) * n,
                tri(n) == n + tri((n - 1) as nat),
                n > 0,
        ;
    }
}

pub proof fn lemma_easy(x: nat)
    ensures
        x + x == 2 * x,
{
}

} // verus!
