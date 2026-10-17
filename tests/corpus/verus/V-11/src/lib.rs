//! Cheat corpus V-11: #[verifier::rlimit(50)] raises one item's rlimit above the course pin.
use vstd::prelude::*;

verus! {

#[verifier::rlimit(50)]
pub proof fn lemma_cube_nonneg(x: int)
    requires
        x >= 0,
    ensures
        x * x * x >= 0,
{
    assert(x * x * x >= 0) by (nonlinear_arith)
        requires
            x >= 0,
    {
    }
}

} // verus!
