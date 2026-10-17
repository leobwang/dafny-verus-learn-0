//! Test fixture (tests/wrappers): invented trait-impl methods for the empty-body
//! gate's qualified symbols (QPLAN §30 Q65(a)). Two impls of one trait and an
//! inherent method share the name `three`; each body needs its proof block.
use vstd::prelude::*;

verus! {

pub open spec fn count3(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { 1 + count3((n - 1) as nat) }
}

pub trait Probe: Sized {
    fn three(&self) -> (r: u64)
        ensures
            r as nat == count3(3),
    ;
}

pub struct A {
    pub x: u64,
}

pub struct B {
    pub y: u64,
}

impl A {
    pub fn three_plain(&self) -> (r: u64)
        ensures
            r == 3,
    {
        3
    }
}

impl Probe for A {
    fn three(&self) -> (r: u64) {
        proof {
            reveal_with_fuel(count3, 4);
        }
        3
    }
}

impl Probe for B {
    fn three(&self) -> (r: u64) {
        proof {
            reveal_with_fuel(count3, 4);
        }
        3
    }
}

} // verus!
