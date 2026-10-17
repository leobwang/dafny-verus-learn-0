//! Test fixture (tests/wrappers): reference-mode findings (lint only).
use vstd::prelude::*;

verus! {

pub uninterp spec fn u(x: nat) -> nat;  // expect: uninterp

pub axiom fn ax(x: nat)  // expect: axiom
    ensures
        x == x;

pub proof fn holes(x: nat)
    ensures
        x == 3,
{
    #[verifier::proof_note("Q04.H1v")] assume(false);  // expect: proof-note assume
    admit();  // expect: admit
}

#[verifier::external_body]  // expect: external-body
pub fn eb(x: u64) -> u64 {
    x
}

#[verifier::assume_termination]  // expect: assume-termination
pub proof fn t(x: nat)
    decreases x,
{
}

// item: Q04.P1v S3 obligation
// SLOT: FAILS ???  // expect: slot-in-reference

// item: Q04.X1v S4
// need: proof fn nine(x: nat)
pub proof fn nine(x: nat)
    ensures
        x + 0 == x,
{
}

// item: Q04.X2v S4
// need: proof fn ten(x: nat)
pub proof fn eleven(x: nat)
    ensures
        x == x,
{
}

} // verus!
