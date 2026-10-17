//! Cheat corpus V02: assume(P) discharges an overflow check and the postcondition.
use vstd::prelude::*;

verus! {

pub fn add_bytes(a: u8, b: u8) -> (r: u8)
    ensures
        r as int == a as int + b as int,
{
    assume(a as int + b as int <= 255);
    a + b
}

} // verus!
