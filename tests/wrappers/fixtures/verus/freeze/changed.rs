//! Test fixture (tests/wrappers): statements weakened or changed.
use vstd::prelude::*;

verus! {

pub struct Pair {
    pub a: u64,
    pub b: u64,
}

pub open spec fn total(p: Pair) -> int {
    p.a + p.b + 0
}

pub proof fn lemma_total(p: Pair)
    requires
        p.a > 0,
    ensures
        total(p) >= p.b,
{
}

pub fn sum(p: &Pair) -> (r: u64)
    requires
        p.a + p.b < 1000,
        p.a < 10,
    ensures
        r == total(*p),
{
    p.a + p.b
}

} // verus!
