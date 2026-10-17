//! Cheat corpus V14: a spec fn reads one past the end of a sequence (partial spec).
use vstd::prelude::*;

verus! {

pub open spec fn ascending(s: Seq<u64>) -> bool {
    forall|i: int| 0 <= i < s.len() ==> #[trigger] s[i] <= s[i + 1]
}

pub proof fn lemma_first_pair(s: Seq<u64>)
    requires
        s.len() >= 1,
        ascending(s),
    ensures
        s[0] <= s[1],
{
    assert(s[0] <= s[1]);
}

} // verus!
