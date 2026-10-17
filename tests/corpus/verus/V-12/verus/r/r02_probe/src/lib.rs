//! Cheat corpus V-12: an A1 module crate calls a later layer's (A4) lemma by path.
use vstd::prelude::*;

verus! {

pub proof fn lemma_grows(n: nat)
    ensures
        rg_re_a4::twice_len(n) >= n,
{
    rg_re_a4::lemma_twice_len(n);
}

} // verus!
