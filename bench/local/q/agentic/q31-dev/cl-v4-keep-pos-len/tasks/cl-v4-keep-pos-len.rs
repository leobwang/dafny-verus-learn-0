// Topic (e) course-local task cl-v4-keep-pos-len (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_keep_pos_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// How many elements of s are positive.
pub open spec fn count_pos(s: Seq<int>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] > 0 { 1nat } else { 0nat }) + count_pos(s.subrange(1, s.len() as int))
    }
}

/// The positive elements of s, in order.
pub open spec fn keep_pos(s: Seq<int>) -> Seq<int>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else if s[0] > 0 {
        seq![s[0]] + keep_pos(s.subrange(1, s.len() as int))
    } else {
        keep_pos(s.subrange(1, s.len() as int))
    }
}

/// keep_pos keeps exactly count_pos elements.
pub proof fn lemma_keep_pos_len(s: Seq<int>)
    ensures
        keep_pos(s).len() == count_pos(s),
    decreases s.len(),
{
}

} // verus!
