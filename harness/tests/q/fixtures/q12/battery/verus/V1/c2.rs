// Battery goal V1, candidate 2 (a whole file; it stands alone).
use vstd::prelude::*;

verus! {

/// The limb base, 2^64.
pub spec const BASE: nat = 0x1_0000_0000_0000_0000;

/// The value of a limb sequence, least significant limb first.
pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + BASE * seq_to_nat(s.drop_first())
    }
}

/// A zero limb put below s shifts its value up by one limb.
pub proof fn lemma_zero_cons(s: Seq<u64>)
    ensures
        seq_to_nat(seq![0u64] + s) == BASE * seq_to_nat(s),
{
}

} // verus!
