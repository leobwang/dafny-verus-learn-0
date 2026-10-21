// Topic (e) course-local task cl-v1-sum-push (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_sum_push` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// The sum of a sequence, first element first.
pub open spec fn sum(s: Seq<nat>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] + sum(s.subrange(1, s.len() as int))
    }
}

/// Appending x adds x to the sum.
pub proof fn lemma_sum_push(s: Seq<nat>, x: nat)
    ensures
        sum(s.push(x)) == sum(s) + x,
    decreases s.len(),
{
}

} // verus!
