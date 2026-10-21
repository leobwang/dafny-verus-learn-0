// Topic (e) course-local task cl-v13-count-up (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `tick_up_to`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

pub fn tick_up_to(n: u64) -> (r: u64)
    ensures
        r == n,
{
    let mut i: u64 = 0;
    while i < n
        invariant
            i <= n,
        decreases n - i,
    {
        i = i + 1;
    }
    i
}

} // verus!
