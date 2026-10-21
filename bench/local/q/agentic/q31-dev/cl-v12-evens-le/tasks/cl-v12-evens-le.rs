// Topic (e) course-local task cl-v12-evens-le (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_evens_below_le` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// How many even numbers lie below n.
pub open spec fn evens_below(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        evens_below((n - 1) as nat) + (if (n - 1) % 2 == 0 { 1nat } else { 0nat })
    }
}

/// There are at most n of them.
pub proof fn lemma_evens_below_le(n: nat)
    ensures
        evens_below(n) <= n,
    decreases n,
{
}

} // verus!
