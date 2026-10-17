//! Test fixture (tests/wrappers): a type error.
use vstd::prelude::*;

verus! {

pub fn mistyped(x: u64) -> (r: bool)
    ensures
        r == true,
{
    x
}

} // verus!
