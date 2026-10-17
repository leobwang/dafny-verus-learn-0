//! Test fixture (tests/wrappers): a whole goal asserted by (bit_vector) over a
//! recursive spec fn of a Seq, which keeps the Verus front end busy past any
//! short wall-clock limit (the Δ58 hazard; invented program).
use vstd::prelude::*;

verus! {

pub open spec fn total(s: Seq<u8>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        total(s.drop_last()) + s.last() as nat
    }
}

pub proof fn spin(s: Seq<u8>)
    requires
        s.len() > 0,
        s.last() == 0,
    ensures
        total(s) == total(s.drop_last()),
{
    assert(total(s) == total(s.drop_last())) by (bit_vector)
        requires
            s.len() > 0,
            s.last() == 0,
    ;
}

} // verus!
