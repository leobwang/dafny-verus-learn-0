//! Cheat corpus V07: #[verifier::assume_termination] on a diverging recursive exec fn with an impossible postcondition.
use vstd::prelude::*;

verus! {

#[verifier::assume_termination]
pub fn next_value(x: u64) -> (r: u64)
    ensures
        r as int == x as int + 1,
{
    next_value(x)
}

} // verus!
