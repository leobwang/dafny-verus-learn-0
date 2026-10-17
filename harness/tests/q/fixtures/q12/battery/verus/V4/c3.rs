// Battery goal V4, candidate 3 (a whole file; it stands alone).
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

/// A non-zero limb below s adds no zero limb.
pub proof fn lemma_count_zeros_cons_nonzero(d: u64, s: Seq<u64>)
    requires
        d != 0,
    ensures
        count_zeros(seq![d] + s) == count_zeros(s),
{
    assert((seq![d] + s).drop_first() =~= s);
    lemma_count_zeros_cons(d, s);
}

} // verus!
