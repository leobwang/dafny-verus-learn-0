// Topic (e) course-local task cl-v9-twos-pos (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_twos_ge` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// 2 to the power n.
pub open spec fn twos_pow(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        2 * twos_pow((n - 1) as nat)
    }
}

/// Every power of two is at least n + 1.
pub proof fn lemma_twos_ge(n: nat)
    ensures
        twos_pow(n) >= n + 1,
    decreases n,
{
    if n > 0 {
        lemma_twos_ge((n - 1) as nat);
    }
}

} // verus!
