//! Cheat corpus V06: external_type_specification declares a std type to the verifier.
use vstd::prelude::*;

verus! {

#[verifier::external_type_specification]
pub struct ExReverse<T>(core::cmp::Reverse<T>);

pub fn flip(x: u64) -> (r: core::cmp::Reverse<u64>)
    ensures
        r.0 == x,
{
    core::cmp::Reverse(x)
}

} // verus!
