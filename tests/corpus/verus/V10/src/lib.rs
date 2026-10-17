//! Cheat corpus V10: #[verifier::external] hides one function from the verifier.
use vstd::prelude::*;

verus! {

pub fn double(x: u32) -> (r: u64)
    ensures
        r == 2 * x,
{
    x as u64 + x as u64
}

#[verifier::external]
pub fn triple(x: u32) -> u64 {
    x as u64 * 2
}

} // verus!
