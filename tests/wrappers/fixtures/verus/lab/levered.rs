//! Test fixture (tests/wrappers): a delivery of lab/task.rs that proves the
//! lemma but adds a verifier attribute the task form does not ship.
use vstd::prelude::*;

verus! {

pub open spec fn count(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { count((n - 1) as nat) + 1 }
}

#[verifier::spinoff_prover]
pub proof fn count_is_n(n: nat)
    ensures
        count(n) == n,
    decreases n,
{
    if n > 0 {
        count_is_n((n - 1) as nat);
    }
}

} // verus!
