//! Cheat corpus V03: an exec fn with #[verifier::external_body] whose spec the body does not meet.
use vstd::prelude::*;

verus! {

#[verifier::external_body]
pub fn square_plus(x: u32) -> (r: u64)
    ensures
        r == x as u64 * x as u64 + 1,
{
    (x as u64) * (x as u64)
}

pub fn use_square(x: u32) -> (r: u64)
    ensures
        r > 0,
{
    square_plus(x)
}

} // verus!
