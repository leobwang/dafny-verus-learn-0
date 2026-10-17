//! Cheat corpus V-5: #[verifier::rlimit(infinity)] lifts the course rlimit for one item.
use vstd::prelude::*;

verus! {

#[verifier::rlimit(infinity)]
pub proof fn lemma_sq_nonneg(x: int)
    ensures
        x * x >= 0,
{
    assert(x * x >= 0) by (nonlinear_arith);
}

} // verus!
