//! Test fixture (tests/wrappers): the invented middle layer.
use vstd::prelude::*;
pub use tla::*;

verus! {

pub open spec fn quad(x: nat) -> nat {
    twice(twice(x))
}

pub proof fn lemma_quad(x: nat)
    ensures
        quad(x) == 4 * x,
{
    lemma_twice(x);
    lemma_twice(twice(x));
}

} // verus!
