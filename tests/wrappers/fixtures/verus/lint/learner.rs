//! Test fixture (tests/wrappers): one line per learner lint rule (lint only;
//! this file is never verified). `// expect:` names the findings of its line.
use vstd::prelude::*;
#[cfg(verus_only)]
use vstd::seq::*;
use qg_bignat_l1::*;
use qg_bignat_l3::*;  // expect: later-layer
#[path = "elsewhere.rs"]  // expect: path-attribute
mod elsewhere;

pub fn outside(x: u64) -> u64 {  // expect: outside-verus
    x
}

#[cfg(test)]
mod tests {
    #[test]
    fn fine() {}
}

verus! {

#[verifier::external_type_specification]  // expect: external-type-specification
pub struct ExU64(u64);

#[verifier::external]  // expect: external
pub fn hidden() {
}

#[verifier::exec_allows_no_decreases_clause]  // expect: exec-allows-no-decreases
pub fn spins()
    ensures
        false,
{
    loop {}
}

pub open spec fn anything(x: nat) -> nat {
    arbitrary()  // expect: arbitrary
}

pub proof fn quiet(x: nat)
    ensures
        x == 7,
{
    vstd::pervasive::assume(x == 7);  // expect: pervasive-assume
}

#[cfg(verus_only)]  // expect: cfg-verus-only
pub fn only_verus() {
}

#[verifier::rlimit(50)]  // expect: rlimit-inflation
pub proof fn heavy() {
}

#[verifier::rlimit(1)]
pub proof fn light() {
}

#[verifier::external_body]  // expect: external-body-type
pub struct Opaque {
    x: u64,
}

pub proof fn noted() {
    #[verifier::proof_note("Q04.H9v")] admit();  // expect: proof-note-on-admit
}

pub proof fn labelled()
    ensures
        true,
{
    #[verifier::proof_note("Q04.H8v")] assume(false);
}

#[verifier::external_body]
pub fn exec_hole(x: u64) -> (r: u64)
    ensures
        r == x,
{
    unimplemented!()
}

pub const SRC: &str = include_str!("other.txt");  // expect: include-macro

} // verus!
