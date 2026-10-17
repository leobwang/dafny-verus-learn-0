//! Cheat corpus control C-3: a recursive spec fn with a decreases clause, and an exec fn that meets it.
use vstd::prelude::*;

verus! {

pub open spec fn pow2(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        2 * pow2((n - 1) as nat)
    }
}

pub fn pow2_small(n: u32) -> (r: u64)
    requires
        n <= 3,
    ensures
        r == pow2(n as nat),
{
    proof {
        reveal_with_fuel(pow2, 4);
    }
    if n == 0 {
        1
    } else if n == 1 {
        2
    } else if n == 2 {
        4
    } else {
        8
    }
}

} // verus!
