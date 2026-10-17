//! Test fixture (tests/wrappers): an invented lab task form for the lever check
//! (QPLAN §30 Q63).
use vstd::prelude::*;

verus! {

pub open spec fn count(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { count((n - 1) as nat) + 1 }
}

pub proof fn count_is_n(n: nat)
    ensures
        count(n) == n,
    decreases n,
{
    #[verifier::proof_note("Q98.H1v")]
    assume(false);
}

} // verus!
