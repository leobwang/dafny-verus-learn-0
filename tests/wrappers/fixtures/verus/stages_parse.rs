//! Test fixture (tests/wrappers): a syntax error.
use vstd::prelude::*;

verus! {

pub proof fn broken(x: nat)
    ensures
        x == x,
{
    let y = ;
}

} // verus!
