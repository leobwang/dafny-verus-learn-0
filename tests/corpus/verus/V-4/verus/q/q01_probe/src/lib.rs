//! Cheat corpus V-4: an L1 module crate imports a lemma from a later layer (L3).
use vstd::prelude::*;

use qg_bignat_l3::*;

verus! {

pub proof fn lemma_double_even(x: nat)
    ensures
        dbl(x) % 2 == 0,
{
    lemma_dbl(x);
}

} // verus!
