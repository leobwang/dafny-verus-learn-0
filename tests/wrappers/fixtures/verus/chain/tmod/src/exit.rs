//! Test fixture (tests/wrappers): a file no `mod` declaration reaches.
use vstd::prelude::*;
use tla::*;

verus! {

pub proof fn nine(x: nat)
    ensures
        twice(x) + x == 3 * x,
{
    lemma_twice(x);
}

} // verus!
