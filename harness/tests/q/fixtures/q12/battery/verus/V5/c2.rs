// Battery goal V5, candidate 2 (a whole file; it stands alone).
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

/// A zero limb below a non-zero one: one zero limb.
pub proof fn lemma_one_zero(d: u64)
    requires
        d != 0,
    ensures
        count_zeros(seq![0u64, d]) == 1,
{
    assert(seq![0u64, d].drop_first() =~= seq![d]);
    assert(seq![d].drop_first() =~= Seq::<u64>::empty());
}

} // verus!
