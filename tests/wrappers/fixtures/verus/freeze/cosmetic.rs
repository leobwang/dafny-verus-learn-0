//! Test fixture (tests/wrappers): the same statements, written differently.
use vstd::prelude::*;

verus! {

// a comment between items
pub struct Pair { pub a: u64, pub b: u64 }

pub open spec fn total(p: Pair) -> int { p.a + p.b }

/// A different doc comment.
pub proof fn lemma_total(p: Pair)
    requires p.a > 0
    ensures total(p) > p.b
{
    assert(total(p) == p.a + p.b);  // the body is not part of the statement
}

#[verifier::external_body]
pub fn sum(p: &Pair) -> (r: u64)
    requires
        p.a + p.b < 1000,  // a trailing comment
    ensures
        r == total(*p),
{
    unimplemented!()
}

pub proof fn lemma_gone(x: nat)
    ensures x >= 0,
{
}

pub proof fn lemma_new(x: nat)
    ensures
        x + 0 == x,
{
}

} // verus!
