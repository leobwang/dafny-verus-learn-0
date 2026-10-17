//! Test fixture (tests/wrappers): an invented lab task form that ships a
//! trusted proof fn (`#[verifier::external_body]`, a lever the lever check
//! allows because the task form ships it) which the task's lemma calls. A
//! delivery equal to it must not pass the lab gate (D24).
use vstd::prelude::*;

verus! {

pub open spec fn count(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { count((n - 1) as nat) + 1 }
}

#[verifier::external_body]
pub proof fn count_step(n: nat)
    ensures
        count(n) == n,
{
}

pub proof fn count_is_n(n: nat)
    ensures
        count(n) == n,
{
    count_step(n);
}

} // verus!
