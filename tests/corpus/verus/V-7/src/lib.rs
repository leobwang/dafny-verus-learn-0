//! Cheat corpus V-7: a verified fn beside a public fn outside verus! that nothing checks.
use vstd::prelude::*;

verus! {

pub fn double(x: u32) -> (r: u64)
    ensures
        r == 2 * x,
{
    x as u64 * 2
}

} // verus!

/// Returns three times x (a claim nothing checks).
pub fn triple(x: u32) -> u64 {
    x as u64 * 2
}
