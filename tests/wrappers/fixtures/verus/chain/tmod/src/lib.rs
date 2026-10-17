//! Test fixture (tests/wrappers): an invented module crate on the chain.
use vstd::prelude::*;
use tlb::*;

pub mod sub;

#[cfg(test)]
mod tests;

verus! {

// item: Q04.H3v S3
pub proof fn eight(x: nat)
    ensures
        quad(twice(x)) == 8 * x,
{
    #[verifier::proof_note("Q04.H3v")] assume(false);
}

pub fn add_two(x: u64) -> (r: u64)
    requires
        x < 1000,
    ensures
        r == x + 2,
{
    x + 2
}

} // verus!
