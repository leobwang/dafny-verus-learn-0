//! Test fixture (tests/wrappers): invented holes beside one real failure.
use vstd::prelude::*;

verus! {

pub open spec fn double(x: nat) -> nat {
    x + x
}

#[verifier::external_body]
pub fn exec_hole(x: u64) -> (r: u64)
    ensures
        r == x,
{
    unimplemented!()
}

pub proof fn really_fails(x: nat)
    ensures
        x + 1 > x,
{
    assert(x > 5);
}

// item: Q04.H1v S3
pub proof fn labelled(x: nat)
    ensures
        double(x) == 2 * x,
{
    #[verifier::proof_note("Q04.H1v")] assume(false);
}

// item: Q04.H2v S3
pub proof fn unlabelled(x: nat)
    ensures
        double(x) >= x,
{
    admit();
}

} // verus!
