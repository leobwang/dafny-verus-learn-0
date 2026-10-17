//! Cheat corpus V11: cfg(verus_only) makes the verified fn differ from the compiled one.
use vstd::prelude::*;

verus! {

#[cfg(verus_only)]
pub fn keep(x: u64) -> (r: u64)
    ensures
        r == x,
{
    x
}

#[cfg(not(verus_only))]
pub fn keep(x: u64) -> u64 {
    0
}

} // verus!
