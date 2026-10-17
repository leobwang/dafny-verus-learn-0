// Battery goal G09, Verus form (a whole file; it stands alone; given, Q15).
// Three place values in a row (a trigger with two terms).
// The goal is the last proof fn; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
use vstd::prelude::*;

verus! {

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

/// The place value of limb n, BASE to the power n. Opaque: its facts are the lemmas
/// below.
#[verifier::opaque]
pub open spec fn weight(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        BASE * weight((n - 1) as nat)
    }
}

pub proof fn lemma_weight_succ(k: nat)
    ensures
        weight(k + 1) == BASE * weight(k),
{
    reveal(weight);
}

pub proof fn lemma_weight_pos(k: nat)
    ensures
        weight(k) > 0,
    decreases k,
{
    reveal(weight);
    if k > 0 {
        lemma_weight_pos((k - 1) as nat);
    }
}

pub proof fn lemma_three_places(n: nat)
    ensures
        weight(n) < weight(n + 1),
        weight(n + 1) < weight(n + 1 + 1),
{
    assert forall|k: nat| #![trigger weight(k), weight(k + 1)] weight(k) < weight(k + 1) by {
        lemma_weight_succ(k);
        lemma_weight_pos(k);
    }
}

} // verus!
