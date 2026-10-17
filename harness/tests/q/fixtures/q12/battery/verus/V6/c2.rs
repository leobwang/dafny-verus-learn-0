// Battery goal V6, candidate 2 (a whole file; it stands alone).
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

/// A zero limb pushed at the top is one more zero limb.
pub proof fn lemma_count_zeros_push_zero(s: Seq<u64>)
    ensures
        count_zeros(s.push(0)) == count_zeros(s) + 1,
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_count_zeros_push_zero(s.drop_first());
    }
}

} // verus!
