//! Cheat corpus V09: every function lies outside verus!, so nothing is verified.
use vstd::prelude::*;

/// Returns the larger of two values (a claim nothing checks).
pub fn larger(a: u64, b: u64) -> u64 {
    if a > b {
        a
    } else {
        b
    }
}

verus! {

} // verus!
