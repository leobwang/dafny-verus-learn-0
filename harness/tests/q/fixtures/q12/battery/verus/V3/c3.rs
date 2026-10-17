// Battery goal V3, candidate 3 (a whole file; it stands alone).
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

/// No more zero limbs than limbs.
pub proof fn lemma_count_zeros_bound(s: Seq<u64>)
    ensures
        count_zeros(s) <= s.len(),
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_count_zeros_bound(s.drop_first());
    }
}

} // verus!
