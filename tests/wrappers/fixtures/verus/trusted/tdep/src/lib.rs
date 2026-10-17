//! Test fixture (tests/wrappers): an invented layer with three holes. Under
//! --no-cheating a crate that calls copy_small or lemma_trusted is shown
//! their external_body holes; lemma_assumed's assume is never shown there.
use vstd::prelude::*;

verus! {

#[verifier::external_body]
pub fn copy_small(x: u64) -> (r: u64)
    ensures
        r == x,
{
    x
}

#[verifier::external_body]
pub proof fn lemma_trusted(x: nat)
    ensures
        x + x >= x,
{
}

pub proof fn lemma_assumed(x: nat)
    ensures
        x * 2 == x + x,
{
    assume(false);
}

} // verus!
