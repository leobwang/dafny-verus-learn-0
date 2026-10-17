// Battery goal G11, Verus form (a whole file; it stands alone; given, Q15).
// A limb put below twice, its value unfolded (the step on the cons).
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

pub proof fn lemma_cons_twice(a: u64, b: u64, s: Seq<u64>)
    ensures
        seq_to_nat(seq![a] + (seq![b] + s)) == a + BASE * (b + BASE * seq_to_nat(s)),
{
    assert forall|d: u64, u: Seq<u64>| seq_to_nat(#[trigger] (seq![d] + u)) == d + BASE * seq_to_nat(u) by {
        assert((seq![d] + u).drop_first() =~= u);
    }
}

} // verus!
