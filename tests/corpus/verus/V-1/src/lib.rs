//! Cheat corpus V-1: #[verifier::external_body] on a struct (opaque fields).
use vstd::prelude::*;

verus! {

#[verifier::external_body]
pub struct Token {
    secret: u64,
}

pub fn pass_on(t: Token) -> (r: Token)
    ensures
        r == t,
{
    t
}

} // verus!
