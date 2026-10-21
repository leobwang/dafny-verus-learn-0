// Topic (e) course-local task cl-v3-rev-len (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_rev_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// The reverse of a sequence, built from its first element.
pub open spec fn rev(s: Seq<int>) -> Seq<int>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else {
        rev(s.subrange(1, s.len() as int)).push(s[0])
    }
}

/// Reversing keeps the length.
pub proof fn lemma_rev_len(s: Seq<int>)
    ensures
        rev(s).len() == s.len(),
    decreases s.len(),
{
}

} // verus!
