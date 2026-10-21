// Topic (e) course-local task cl-v6-max-ge (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_seq_max_ge` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// The largest element of a non-empty sequence.
pub open spec fn seq_max(s: Seq<int>) -> int
    recommends
        s.len() > 0,
    decreases s.len(),
{
    if s.len() <= 1 {
        s[0]
    } else {
        let m = seq_max(s.subrange(1, s.len() as int));
        if s[0] >= m { s[0] } else { m }
    }
}

/// Every element is at most the maximum.
pub proof fn lemma_seq_max_ge(s: Seq<int>, i: int)
    requires
        0 <= i < s.len(),
    ensures
        s[i] <= seq_max(s),
    decreases s.len(),
{
    if s.len() > 1 && i > 0 {
        lemma_seq_max_ge(s.subrange(1, s.len() as int), i - 1);
    }
}

} // verus!
