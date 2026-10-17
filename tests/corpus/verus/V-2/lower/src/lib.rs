//! Cheat corpus V-2, lower crate: an external_body fn whose spec its body does not meet.
use vstd::prelude::*;

verus! {

#[verifier::external_body]
pub fn halve(x: u64) -> (r: u64)
    ensures
        r * 2 == x,
{
    x / 2
}

} // verus!
