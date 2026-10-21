// Topic (e) course-local task cl-v11-uniform-ends (Q31 dev stratum, course-authored 2026-10-21; QPLAN §33.4).
// Write the body of `lemma_uniform_ends` so that `scripts/vcheck --gate` verifies this file. Keep every
// other line of the file as it is: the definitions above it, its statement and its attributes.
// You may add lemmas of your own.
use vstd::prelude::*;

verus! {

/// Every element equals the next one.
pub open spec fn steady_seq(s: Seq<int>) -> bool
    decreases s.len(),
{
    s.len() <= 1 || (s[0] == s[1] && steady_seq(s.subrange(1, s.len() as int)))
}

/// In a uniform sequence the first and last elements agree.
pub proof fn lemma_uniform_ends(s: Seq<int>)
    requires
        s.len() > 0,
        steady_seq(s),
    ensures
        s[0] == s[s.len() - 1],
    decreases s.len(),
{
    if s.len() > 1 {
        let rest = s.subrange(1, s.len() as int);
        lemma_uniform_ends(rest);
        assert(rest[rest.len() - 1] == s[s.len() - 1]);
    }
}

} // verus!
