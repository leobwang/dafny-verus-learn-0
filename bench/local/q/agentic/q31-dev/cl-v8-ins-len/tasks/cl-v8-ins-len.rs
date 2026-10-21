// Topic (e) course-local task cl-v8-ins-len (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_insert_ordered_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// x inserted before the first element it does not exceed.
pub open spec fn insert_ordered(x: int, s: Seq<int>) -> Seq<int>
    decreases s.len(),
{
    if s.len() == 0 || x <= s[0] {
        seq![x] + s
    } else {
        seq![s[0]] + insert_ordered(x, s.subrange(1, s.len() as int))
    }
}

/// Inserting adds one element.
pub proof fn lemma_insert_ordered_len(x: int, s: Seq<int>)
    ensures
        insert_ordered(x, s).len() == s.len() + 1,
    decreases s.len(),
{
}

} // verus!
