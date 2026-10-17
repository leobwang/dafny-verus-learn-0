//! Test fixture (tests/wrappers): one of each --no-cheating hole kind.
use vstd::prelude::*;

verus! {

pub uninterp spec fn u_marked(x: nat) -> nat;

pub spec fn u_bodyless(x: nat) -> nat;

pub axiom fn ax(x: nat)
    ensures
        x == x + 0;

} // verus!

pub fn plain(x: u64) -> u64 {
    x
}

verus! {

pub assume_specification[ plain ](x: u64) -> (r: u64)
    ensures
        r == x;

#[verifier::assume_termination]
pub proof fn loops(x: nat)
    ensures
        true,
    decreases x,
{
    loops(x);
}

#[verifier::external_body]
pub proof fn trusted(x: nat)
    ensures
        x > 100,
{
}

pub proof fn assumes(x: nat)
    ensures
        x == 3,
{
    assume(x == 3);
}

} // verus!
