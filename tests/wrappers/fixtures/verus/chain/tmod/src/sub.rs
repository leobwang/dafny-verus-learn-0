//! Test fixture (tests/wrappers): a submodule file of the module crate.
use vstd::prelude::*;
use tla::*;

verus! {

pub proof fn six(x: nat)
    ensures
        twice(x) + twice(x) + twice(x) == 6 * x,
{
    lemma_twice(x);
}

} // verus!
