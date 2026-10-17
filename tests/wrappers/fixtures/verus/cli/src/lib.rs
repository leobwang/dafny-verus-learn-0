//! Test fixture (tests/wrappers): the invented verified core of `tally`.
use vstd::prelude::*;
use tla::*;

verus! {

/// The sum of two words, widened.
pub fn sum_words(a: u32, b: u32) -> (r: u64)
    ensures
        r == a + b,
{
    a as u64 + b as u64
}

/// Twice a word, by the bottom crate's spec fn.
pub fn twice_word(a: u32) -> (r: u64)
    ensures
        r == twice(a as nat),
{
    a as u64 + a as u64
}

} // verus!
