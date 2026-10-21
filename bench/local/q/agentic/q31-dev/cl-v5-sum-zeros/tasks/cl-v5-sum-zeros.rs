// Topic (e) course-local task cl-v5-sum-zeros (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_sum_zeros` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// The sum of a sequence, first element first.
pub open spec fn total(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] + total(s.subrange(1, s.len() as int))
    }
}

/// A sequence of zeros sums to zero.
pub proof fn lemma_sum_zeros(s: Seq<int>)
    requires
        forall|i: int| 0 <= i < s.len() ==> s[i] == 0,
    ensures
        total(s) == 0,
    decreases s.len(),
{
}

} // verus!
