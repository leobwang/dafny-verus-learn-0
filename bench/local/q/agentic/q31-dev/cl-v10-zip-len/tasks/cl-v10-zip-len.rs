// Topic (e) course-local task cl-v10-zip-len (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_zip_pairs_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// The pairs of elements at equal positions.
pub open spec fn zip_pairs(a: Seq<int>, b: Seq<int>) -> Seq<(int, int)>
    decreases a.len(),
{
    if a.len() == 0 || b.len() == 0 {
        Seq::empty()
    } else {
        seq![(a[0], b[0])] + zip_pairs(a.subrange(1, a.len() as int), b.subrange(1, b.len() as int))
    }
}

/// Zipping equally long sequences keeps their length.
pub proof fn lemma_zip_pairs_len(a: Seq<int>, b: Seq<int>)
    requires
        a.len() == b.len(),
    ensures
        zip_pairs(a, b).len() == a.len(),
    decreases a.len(),
{
}

} // verus!
