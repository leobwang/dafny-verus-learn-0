// Battery goal V2, candidate 3 (a whole file; it stands alone).
use vstd::prelude::*;

verus! {

/// The number of zero limbs.
pub open spec fn count_zeros(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] == 0 { 1nat } else { 0nat }) + count_zeros(s.drop_first())
    }
}

/// Zero limbs add up over a concatenation.
pub proof fn lemma_count_zeros_append(s: Seq<u64>, t: Seq<u64>)
    ensures
        count_zeros(s + t) == count_zeros(s) + count_zeros(t),
    decreases s.len(),
{
    if s.len() == 0 {
        assert(s + t =~= t);
    } else {
        lemma_count_zeros_append(s.drop_first(), t);
    }
}

} // verus!
