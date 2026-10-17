//! Cheat corpus V07b: #[verifier::assume_termination] lets an exec fn loop forever without a decreases clause.
use vstd::prelude::*;

verus! {

#[verifier::assume_termination]
pub fn drain(x: u64) -> (r: u64)
    ensures
        r < x && r > x,
{
    let mut i: u64 = x;
    while i != 0
        invariant
            true,
    {
        i = i;
    }
    loop
        invariant
            true,
    {
    }
}

} // verus!
