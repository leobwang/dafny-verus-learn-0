//! Cheat corpus control C-5, upper crate: uses the lower crate by a path dependency, no trust.
use vstd::prelude::*;

verus! {

pub proof fn lemma_twice_even(x: nat)
    ensures
        corpus_vc5_lower::twice(x) % 2 == 0,
{
    corpus_vc5_lower::lemma_twice(x);
}

} // verus!
