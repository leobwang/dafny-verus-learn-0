//! Cheat corpus control C-7: a satisfiable precondition, with a witness and a swap-to-false probe.
use vstd::prelude::*;

verus! {

pub fn mid(lo: u64, hi: u64) -> (r: u64)
    requires
        lo <= hi,
    ensures
        lo <= r <= hi,
{
    lo + (hi - lo) / 2
}

} // verus!
