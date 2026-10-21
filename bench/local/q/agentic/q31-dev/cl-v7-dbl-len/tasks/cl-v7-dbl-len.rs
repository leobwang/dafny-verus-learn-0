// Topic (e) course-local task cl-v7-dbl-len (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_doubled_seq_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// Every element doubled.
pub open spec fn doubled_seq(s: Seq<int>) -> Seq<int>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else {
        seq![2 * s[0]] + doubled_seq(s.subrange(1, s.len() as int))
    }
}

/// Doubling keeps the length.
pub proof fn lemma_doubled_seq_len(s: Seq<int>)
    ensures
        doubled_seq(s).len() == s.len(),
    decreases s.len(),
{
}

} // verus!
