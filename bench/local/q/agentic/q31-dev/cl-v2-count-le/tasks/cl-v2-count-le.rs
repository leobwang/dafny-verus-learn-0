// Topic (e) course-local task cl-v2-count-le (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_count_le_len` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// How many times x occurs in s.
pub open spec fn count(s: Seq<int>, x: int) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] == x { 1nat } else { 0nat }) + count(s.subrange(1, s.len() as int), x)
    }
}

/// No value occurs more often than the sequence is long.
pub proof fn lemma_count_le_len(s: Seq<int>, x: int)
    ensures
        count(s, x) <= s.len(),
    decreases s.len(),
{
}

} // verus!
